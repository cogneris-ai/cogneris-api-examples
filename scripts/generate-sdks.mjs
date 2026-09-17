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

  const forbiddenRoutes = ["/platform", "platform/v1", "/admin", "admincontroller"];
  for (const sdkName of ["typescript", "python"]) {
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

    await validatePackages(stagedOutput);
    const manifest = {
      schemaVersion: 1,
      source: {
        path: "openapi/cogneris-openapi.yaml",
        sha256: await sha256(sourcePath),
      },
      generators,
      packages: {
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
