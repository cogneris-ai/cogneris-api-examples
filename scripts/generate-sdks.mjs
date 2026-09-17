import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { replaceOutput } from "./sdk-output-swap.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const configDirectory = path.join(root, "scripts", "sdk-config");
const overlayDirectory = path.join(root, "scripts", "sdk-overlays");
const sourcePath = path.join(root, "openapi", "cogneris-openapi.yaml");
const committedOutput = path.join(root, "sdks");

const arguments_ = process.argv.slice(2);
if (arguments_.length > 1 || (arguments_.length === 1 && arguments_[0] !== "--check")) {
  console.error("Usage: node scripts/generate-sdks.mjs [--check]");
  process.exit(2);
}
const checkMode = arguments_[0] === "--check";

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

function run(command, argumentsList, options = {}) {
  const result = spawnSync(command, argumentsList, {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, ...options.env },
  });
  if (result.status !== 0) {
    if (result.stdout) process.stderr.write(result.stdout);
    if (result.stderr) process.stderr.write(result.stderr);
    throw new Error(`${command} exited with ${result.status ?? "no status"}`);
  }
}

function generateOpenApiSdk(generatorName, configPath, outputPath, generators) {
  const pin = generators[generatorName];
  run("uvx", [
    "--from", `${pin.package}==${pin.version}`,
    "--with", `${pin.runtime.package}==${pin.runtime.version}`,
    "openapi-generator-cli", "generate",
    "-g", generatorName,
    "-i", sourcePath,
    "-o", outputPath,
    "-c", configPath,
  ]);
}

async function sha256(filePath) {
  return crypto
    .createHash("sha256")
    .update(await fs.readFile(filePath))
    .digest("hex");
}

async function listFiles(directory, prefix = "") {
  let entries;
  try {
    entries = await fs.readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }

  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
    const absolutePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await listFiles(absolutePath, relativePath)));
    } else if (entry.isFile()) {
      files.push(relativePath);
    } else {
      throw new Error(`unsupported generated entry: ${relativePath}`);
    }
  }
  return files;
}

async function hashFiles(directory) {
  const files = {};
  for (const relativePath of await listFiles(directory)) {
    files[relativePath] = await sha256(path.join(directory, relativePath));
  }
  return files;
}

async function writeJson(filePath, value) {
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

async function applyOverlayFiles(sourceDirectory, destinationDirectory) {
  for (const relativePath of await listFiles(sourceDirectory)) {
    const destination = path.join(destinationDirectory, relativePath);
    await fs.mkdir(path.dirname(destination), { recursive: true });
    await fs.copyFile(path.join(sourceDirectory, relativePath), destination);
  }
}

async function appendOverlay(targetPath, overlayPath) {
  const current = await fs.readFile(targetPath, "utf8");
  const addition = await fs.readFile(overlayPath, "utf8");
  await fs.writeFile(targetPath, `${current.trimEnd()}\n${addition}`);
}

async function applyApprovedLicense(stagedOutput) {
  for (const packageDirectory of ["typescript", "python", "csharp", "java"]) {
    for (const legalFile of ["LICENSE", "NOTICE"]) {
      await fs.copyFile(
        path.join(root, legalFile),
        path.join(stagedOutput, packageDirectory, legalFile),
      );
    }
  }

  const pythonProjectPath = path.join(stagedOutput, "python", "pyproject.toml");
  const pythonProject = await fs.readFile(pythonProjectPath, "utf8");
  const readmeDeclaration = 'readme = "README.md"\n';
  if (!pythonProject.includes(readmeDeclaration)) {
    throw new Error("generated Python package metadata is missing its README declaration");
  }
  await fs.writeFile(
    pythonProjectPath,
    pythonProject.replace(
      readmeDeclaration,
      `${readmeDeclaration}license = "Apache-2.0"\nlicense-files = ["LICENSE", "NOTICE"]\n`,
    ),
  );

  const csharpProjectPath = path.join(stagedOutput, "csharp", "src", "Cogneris.DocumentAI", "Cogneris.DocumentAI.csproj");
  const csharpProject = await fs.readFile(csharpProjectPath, "utf8");
  if (!csharpProject.includes("<PackageLicenseExpression>Apache-2.0</PackageLicenseExpression>")) {
    throw new Error("generated C# project is missing the approved license expression");
  }
  await fs.writeFile(csharpProjectPath, csharpProject.replace("</Project>", `  <ItemGroup>
    <None Include="../../LICENSE" Pack="true" PackagePath="" />
    <None Include="../../NOTICE" Pack="true" PackagePath="" />
  </ItemGroup>

</Project>`));

  const javaLegalDirectory = path.join(stagedOutput, "java", "src", "main", "resources", "META-INF");
  await fs.mkdir(javaLegalDirectory, { recursive: true });
  for (const legalFile of ["LICENSE", "NOTICE"]) {
    await fs.copyFile(path.join(root, legalFile), path.join(javaLegalDirectory, legalFile));
  }
}

async function normalizeOpenApiSdk(sdkName, outputPath, generators) {
  const scaffolding = sdkName === "csharp"
    ? [".gitignore", ".openapi-generator-ignore", ".openapi-generator", "appveyor.yml", "api", "docs", "docs/scripts", "src/Cogneris.DocumentAI.Test", "Cogneris.DocumentAI.sln", "src/Cogneris.DocumentAI/README.md"]
    : [".github", ".gitignore", ".openapi-generator-ignore", ".openapi-generator", ".travis.yml", "api", "docs", "git_push.sh", "build.sbt", "src/test"];
  for (const relativePath of scaffolding) {
    await fs.rm(path.join(outputPath, relativePath), { recursive: true, force: true });
  }

  if (sdkName === "csharp") {
    const projectPath = path.join(outputPath, "src", "Cogneris.DocumentAI", "Cogneris.DocumentAI.csproj");
    let project = await fs.readFile(projectPath, "utf8");
    const replacements = new Map([
      ["<Authors>OpenAPI</Authors>", "<Authors>COGNERIS, INC.</Authors>"],
      ["<Company>OpenAPI</Company>", "<Company>COGNERIS, INC.</Company>"],
      ["<AssemblyTitle>OpenAPI Library</AssemblyTitle>", "<AssemblyTitle>Cogneris Document AI SDK</AssemblyTitle>"],
      ["<Description>A library generated from a OpenAPI doc</Description>", "<Description>Cogneris Document AI API client for .NET</Description>"],
      ["<Copyright>No Copyright</Copyright>", "<Copyright>Copyright 2026 COGNERIS, INC.</Copyright>"],
      ["<RepositoryUrl>https://github.com/GIT_USER_ID/GIT_REPO_ID.git</RepositoryUrl>", "<RepositoryUrl>https://github.com/cogneris-ai/cogneris-api-examples.git</RepositoryUrl>"],
    ]);
    for (const [generated, approved] of replacements) {
      if (project.split(generated).length !== 2) {
        throw new Error(`generated C# package metadata template changed: ${generated}`);
      }
      project = project.replace(generated, approved);
    }
    await fs.writeFile(projectPath, project);
  } else if (sdkName === "java") {
    const buildPath = path.join(outputPath, "build.gradle");
    let build = await fs.readFile(buildPath, "utf8");
    if (build.split("JavaVersion.VERSION_11").length !== 3) {
      throw new Error("generated Java runtime targets do not match the expected template");
    }
    build = build.replaceAll("JavaVersion.VERSION_11", "JavaVersion.VERSION_17");
    if (!build.includes("apply plugin: 'java'")) throw new Error("generated Java library plugin template is missing");
    build = build.replace("apply plugin: 'java'", "apply plugin: 'java-library'");
    // Generated public models and ApiClient expose these types. The published
    // Gradle POM must make them available when an external consumer compiles.
    for (const dependency of [
      "com.google.code.findbugs:jsr305",
      "com.fasterxml.jackson.core:jackson-core",
      "com.fasterxml.jackson.core:jackson-annotations",
      "com.fasterxml.jackson.core:jackson-databind",
      "org.openapitools:jackson-databind-nullable",
    ]) {
      const declaration = `implementation "${dependency}:`;
      if (!build.includes(declaration)) throw new Error(`generated Java public dependency is missing: ${dependency}`);
      build = build.replace(declaration, `api "${dependency}:`);
    }
    const publication = `            artifactId = 'cogneris-document-ai-sdk'
            from components.java`;
    if (build.split(publication).length !== 2) {
      throw new Error("generated Java publication template changed");
    }
    build = build.replace(publication, `${publication}
            pom {
                name = 'Cogneris Document AI SDK'
                description = 'Cogneris Document AI API client for Java'
                url = 'https://github.com/cogneris-ai/cogneris-api-examples'
                licenses {
                    license {
                        name = 'Apache-2.0'
                        url = 'https://www.apache.org/licenses/LICENSE-2.0'
                        distribution = 'repo'
                    }
                }
                developers {
                    developer {
                        name = 'COGNERIS, INC.'
                        organization = 'COGNERIS, INC.'
                        organizationUrl = 'https://github.com/cogneris-ai'
                    }
                }
                scm {
                    connection = 'scm:git:git://github.com/cogneris-ai/cogneris-api-examples.git'
                    developerConnection = 'scm:git:ssh://git@github.com/cogneris-ai/cogneris-api-examples.git'
                    url = 'https://github.com/cogneris-ai/cogneris-api-examples'
                }
            }`);
    await fs.writeFile(buildPath, build);
    const pomPath = path.join(outputPath, "pom.xml");
    let pom = await fs.readFile(pomPath, "utf8");
    for (const target of ["source", "target"]) {
      const declaration = `<maven.compiler.${target}>11</maven.compiler.${target}>`;
      if (!pom.includes(declaration)) throw new Error(`generated Java POM is missing ${declaration}`);
      pom = pom.replace(declaration, `<maven.compiler.${target}>17</maven.compiler.${target}>`);
    }
    const enforcer = /(<requireJavaVersion>\s*<version>)11(<\/version>\s*<\/requireJavaVersion>)/;
    if (!enforcer.test(pom)) throw new Error("generated Java POM is missing its Java 11 enforcer template");
    pom = pom.replace(enforcer, (_, opening, closing) => `${opening}17${closing}`);
    const generatedUrl = "<url>https://github.com/openapitools/openapi-generator</url>";
    if (pom.split(generatedUrl).length !== 3) {
      throw new Error(`generated Java POM provenance template changed: ${generatedUrl}`);
    }
    pom = pom.replaceAll(generatedUrl, "<url>https://github.com/cogneris-ai/cogneris-api-examples</url>");
    const pomReplacements = new Map([
      ["<description>OpenAPI Java</description>", "<description>Cogneris Document AI API client for Java</description>"],
      ["<connection>scm:git:git@github.com:openapitools/openapi-generator.git</connection>", "<connection>scm:git:git://github.com/cogneris-ai/cogneris-api-examples.git</connection>"],
      ["<developerConnection>scm:git:git@github.com:openapitools/openapi-generator.git</developerConnection>", "<developerConnection>scm:git:ssh://git@github.com/cogneris-ai/cogneris-api-examples.git</developerConnection>"],
      [`<developer>
            <name>OpenAPI-Generator Contributors</name>
            <email>team@openapitools.org</email>
            <organization>OpenAPITools.org</organization>
            <organizationUrl>http://openapitools.org</organizationUrl>
        </developer>`, `<developer>
            <name>COGNERIS, INC.</name>
            <organization>COGNERIS, INC.</organization>
            <organizationUrl>https://github.com/cogneris-ai</organizationUrl>
        </developer>`],
    ]);
    for (const [generated, approved] of pomReplacements) {
      if (!pom.includes(generated)) {
        throw new Error(`generated Java POM provenance template changed: ${generated}`);
      }
      pom = pom.replace(generated, approved);
    }
    await fs.writeFile(pomPath, pom);
    const wrapperPath = path.join(outputPath, "gradle", "wrapper", "gradle-wrapper.properties");
    const wrapper = await fs.readFile(wrapperPath, "utf8");
    const gradle = generators.java.gradle;
    if (!wrapper.includes(`gradle-${gradle.version}-bin.zip`) || wrapper.includes("distributionSha256Sum=")) {
      throw new Error("generated Gradle wrapper does not match the pinned distribution template");
    }
    await fs.writeFile(wrapperPath, `${wrapper.trimEnd()}\ndistributionSha256Sum=${gradle.distributionSha256}\n`);
  }
}

async function normalizeGeneratedText(directory) {
  for (const relativePath of await listFiles(directory)) {
    const filePath = path.join(directory, relativePath);
    const bytes = await fs.readFile(filePath);
    if (bytes.includes(0)) continue;
    const text = bytes.toString("utf8");
    // Never decode/rewrite binary artifacts such as the Gradle wrapper JAR.
    if (!Buffer.from(text, "utf8").equals(bytes)) continue;
    const normalized = text.replace(/[^\S\r\n]+(?=\r?$)/gm, "").replace(/(?:\r?\n){2,}$/, "\n");
    if (normalized !== text) await fs.writeFile(filePath, normalized);
  }
}

async function validatePackages(stagedOutput) {
  const typescriptPackage = await readJson(
    path.join(stagedOutput, "typescript", "package.json"),
  );
  if (
    typescriptPackage.name !== "@cogneris-ai/document-ai-sdk" ||
    typescriptPackage.version !== "0.1.0" ||
    typescriptPackage.private === true
  ) {
    throw new Error("generated TypeScript package identity is invalid");
  }

  const pythonProject = await fs.readFile(
    path.join(stagedOutput, "python", "pyproject.toml"),
    "utf8",
  );
  const requiredPythonMetadata = [
    'name = "cogneris-document-ai-sdk"',
    'version = "0.1.0"',
    'requires-python = ">=3.9,<4.0"',
    'license = "Apache-2.0"',
    'license-files = ["LICENSE", "NOTICE"]',
  ];
  for (const metadata of requiredPythonMetadata) {
    if (!pythonProject.split("\n").includes(metadata)) {
      throw new Error(`generated Python package metadata is invalid: missing ${metadata}`);
    }
  }
  await fs.access(
    path.join(
      stagedOutput,
      "python",
      "cogneris_document_ai_sdk",
      "__init__.py",
    ),
  );

  const csharpProject = await fs.readFile(path.join(stagedOutput, "csharp", "src", "Cogneris.DocumentAI", "Cogneris.DocumentAI.csproj"), "utf8");
  for (const metadata of [
    "<PackageId>Cogneris.DocumentAI</PackageId>",
    "<AssemblyName>Cogneris.DocumentAI</AssemblyName>",
    "<RootNamespace>Cogneris.DocumentAI</RootNamespace>",
    "<Version>0.1.0</Version>",
    "<TargetFramework>net8.0</TargetFramework>",
    "<Nullable>enable</Nullable>",
    "<PackageLicenseExpression>Apache-2.0</PackageLicenseExpression>",
    '<None Include="../../LICENSE" Pack="true" PackagePath="" />',
    '<None Include="../../NOTICE" Pack="true" PackagePath="" />',
  ]) {
    if (!csharpProject.includes(metadata)) throw new Error(`generated C# metadata is invalid: missing ${metadata}`);
  }

  const javaPom = await fs.readFile(path.join(stagedOutput, "java", "pom.xml"), "utf8");
  for (const metadata of [
    "<groupId>ai.cogneris</groupId>",
    "<artifactId>cogneris-document-ai-sdk</artifactId>",
    "<version>0.1.0</version>",
    "<packaging>jar</packaging>",
    "<maven.compiler.source>17</maven.compiler.source>",
    "<maven.compiler.target>17</maven.compiler.target>",
  ]) {
    if (!javaPom.includes(metadata)) throw new Error(`generated Java POM identity is invalid: missing ${metadata}`);
  }
  if (!/<requireJavaVersion>\s*<version>17<\/version>\s*<\/requireJavaVersion>/.test(javaPom)) {
    throw new Error("generated Java POM must enforce Java 17");
  }
  await fs.access(path.join(stagedOutput, "java", "src", "main", "java", "ai", "cogneris", "documentai", "ApiClient.java"));
  const javaBuild = await fs.readFile(path.join(stagedOutput, "java", "build.gradle"), "utf8");
  if (javaBuild.split("JavaVersion.VERSION_17").length !== 3 || javaBuild.includes("JavaVersion.VERSION_11")) {
    throw new Error("generated Java runtime targets must both be Java 17");
  }

  for (const sdkName of ["typescript", "python", "csharp", "java"]) {
    for (const legalFile of ["LICENSE", "NOTICE"]) {
      const expected = await fs.readFile(path.join(root, legalFile));
      const actual = await fs.readFile(path.join(stagedOutput, sdkName, legalFile));
      if (!expected.equals(actual)) throw new Error(`generated ${sdkName} ${legalFile} is invalid`);
      if (sdkName === "java") {
        const resource = await fs.readFile(path.join(stagedOutput, sdkName, "src", "main", "resources", "META-INF", legalFile));
        if (!expected.equals(resource)) throw new Error(`generated Java META-INF/${legalFile} is invalid`);
      }
    }
  }

  const forbiddenRoutes = ["/platform", "platform/v1", "/admin", "admincontroller"];
  for (const sdkName of ["typescript", "python", "csharp", "java"]) {
    for (const relativePath of await listFiles(path.join(stagedOutput, sdkName))) {
      const contents = await fs.readFile(
        path.join(stagedOutput, sdkName, relativePath),
        "utf8",
      );
      const lower = contents.toLowerCase();
      for (const forbiddenRoute of forbiddenRoutes) {
        if (lower.includes(forbiddenRoute)) {
          throw new Error(
            `generated ${sdkName} artifact contains forbidden route ${forbiddenRoute}: ${relativePath}`,
          );
        }
      }
    }
  }
}

async function compareOutputs(expectedDirectory, actualDirectory) {
  const expectedFiles = await listFiles(expectedDirectory);
  const actualFiles = await listFiles(actualDirectory);
  const expectedSet = new Set(expectedFiles);
  const actualSet = new Set(actualFiles);
  const differences = [];

  for (const relativePath of expectedFiles) {
    if (!actualSet.has(relativePath)) {
      differences.push(`missing: ${relativePath}`);
      continue;
    }
    const expected = await fs.readFile(path.join(expectedDirectory, relativePath));
    const actual = await fs.readFile(path.join(actualDirectory, relativePath));
    if (!expected.equals(actual)) differences.push(`changed: ${relativePath}`);
  }
  for (const relativePath of actualFiles) {
    if (!expectedSet.has(relativePath)) differences.push(`extra: ${relativePath}`);
  }
  return differences;
}

async function main() {
  const generators = await readJson(path.join(configDirectory, "generators.json"));
  const typescriptGeneratorPackage = await readJson(
    path.join(root, "node_modules", "@hey-api", "openapi-ts", "package.json"),
  );
  if (typescriptGeneratorPackage.version !== generators.typescript.version) {
    throw new Error(
      `installed ${generators.typescript.package} ${typescriptGeneratorPackage.version} does not match pin ${generators.typescript.version}`,
    );
  }

  const temporaryRoot = await fs.mkdtemp(path.join(root, ".sdk-generation-"));
  const stagedOutput = path.join(temporaryRoot, "sdks");
  const typescriptOutput = path.join(stagedOutput, "typescript");
  const pythonOutput = path.join(stagedOutput, "python");
  const csharpOutput = path.join(stagedOutput, "csharp");
  const javaOutput = path.join(stagedOutput, "java");

  try {
    await fs.mkdir(typescriptOutput, { recursive: true });
    run(
      path.join(root, "node_modules", ".bin", "openapi-ts"),
      ["--file", path.join(configDirectory, "typescript.config.mjs")],
      {
        env: {
          COGNERIS_SDK_OPENAPI_INPUT: sourcePath,
          COGNERIS_TYPESCRIPT_SDK_OUTPUT: path.join(typescriptOutput, "src"),
        },
      },
    );
    await fs.copyFile(
      path.join(configDirectory, "typescript-package.json"),
      path.join(typescriptOutput, "package.json"),
    );
    await fs.copyFile(
      path.join(configDirectory, "typescript-tsconfig.json"),
      path.join(typescriptOutput, "tsconfig.json"),
    );

    run(
      "uvx",
      [
        "--from",
        `${generators.python.package}==${generators.python.version}`,
        "--with",
        `ruff==${generators.python.dependencies.ruff}`,
        "openapi-python-client",
        "generate",
        "--path",
        sourcePath,
        "--config",
        path.join(configDirectory, "python.json"),
        "--meta",
        "uv",
        "--output-path",
        pythonOutput,
        "--fail-on-warning",
      ],
      // 0.26.2 builds a few annotation unions from sets. Pinning the standard
      // Python hash seed normalizes only that known source-order instability.
      { env: { PYTHONHASHSEED: "0" } },
    );

    // Some generator environments initialize a nested repository. Its object
    // database and refs are nondeterministic metadata, never SDK source.
    await fs.rm(path.join(pythonOutput, ".git"), {
      recursive: true,
      force: true,
    });
    await fs.rm(path.join(pythonOutput, ".ruff_cache"), {
      recursive: true,
      force: true,
    });
    await fs.copyFile(
      path.join(configDirectory, "python-CHANGELOG.md"),
      path.join(pythonOutput, "CHANGELOG.md"),
    );
    await fs.copyFile(
      path.join(configDirectory, "python-README.md"),
      path.join(pythonOutput, "README.md"),
    );

    for (const [sdkName, outputPath] of [["csharp", csharpOutput], ["java", javaOutput]]) {
      generateOpenApiSdk(sdkName, path.join(configDirectory, `${sdkName}.json`), outputPath, generators);
      await normalizeOpenApiSdk(sdkName, outputPath, generators);
    }

    await applyOverlayFiles(
      path.join(overlayDirectory, "typescript", "files"),
      typescriptOutput,
    );
    await appendOverlay(
      path.join(typescriptOutput, "src", "index.ts"),
      path.join(overlayDirectory, "typescript", "index.append.ts"),
    );
    await applyOverlayFiles(
      path.join(overlayDirectory, "python", "files"),
      pythonOutput,
    );
    await appendOverlay(
      path.join(pythonOutput, "cogneris_document_ai_sdk", "__init__.py"),
      path.join(overlayDirectory, "python", "__init__.append.py"),
    );
    for (const [sdkName, outputPath] of [["csharp", csharpOutput], ["java", javaOutput]]) {
      await applyOverlayFiles(path.join(overlayDirectory, sdkName, "files"), outputPath);
      await normalizeGeneratedText(outputPath);
    }

    await applyApprovedLicense(stagedOutput);

    await validatePackages(stagedOutput);
    const manifest = {
      schemaVersion: 1,
      source: {
        path: "openapi/cogneris-openapi.yaml",
        sha256: await sha256(sourcePath),
      },
      generators,
      packages: {
        csharp: {
          name: "Cogneris.DocumentAI",
          version: "0.1.0",
          files: await hashFiles(csharpOutput),
        },
        java: {
          name: "ai.cogneris:cogneris-document-ai-sdk",
          version: "0.1.0",
          files: await hashFiles(javaOutput),
        },
        python: {
          name: "cogneris-document-ai-sdk",
          version: "0.1.0",
          files: await hashFiles(pythonOutput),
        },
        typescript: {
          name: "@cogneris-ai/document-ai-sdk",
          version: "0.1.0",
          files: await hashFiles(typescriptOutput),
        },
      },
    };
    await writeJson(path.join(stagedOutput, "manifest.json"), manifest);

    if (checkMode) {
      const differences = await compareOutputs(stagedOutput, committedOutput);
      if (differences.length > 0) {
        console.error(`Generated SDK output is stale:\n${differences.join("\n")}`);
        process.exitCode = 1;
      } else {
        console.log("Generated SDK output is current.");
      }
    } else {
      await replaceOutput({ committedOutput, stagedOutput });
      console.log("Generated SDK output updated.");
    }
  } finally {
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
