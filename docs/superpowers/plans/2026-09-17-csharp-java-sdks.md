# C# and Java SDKs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reproducible, Apache-2.0-licensed C#/.NET and Java SDK packages with full document/job workflow parity, isolated package consumers, and five-package release verification.

**Architecture:** Extend the existing atomic SDK generator with OpenAPI Generator 7.25.0 running on a pinned bundled Java 17 runtime. Keep generated models and low-level operations under `sdks/csharp` and `sdks/java`, add repository-owned `CognerisClient` facades as overlays, and prove the resulting NuGet and Maven artifacts only from clean external consumers.

**Tech Stack:** Node.js 24, Python 3.12, `uv`/`uvx`, OpenAPI Generator 7.25.0, jdk4py 17.0.9.2, .NET 8, C# 12, Java 17, Gradle 8.14.5, Python `unittest`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-csharp-java-sdks-and-site-docs-design.md`

## Global Constraints

- Package version remains exactly `0.1.0` in all SDK and CLI artifacts.
- C# package ID and root namespace are `Cogneris.DocumentAI`; target framework is `net8.0`.
- Java coordinates are `ai.cogneris:cogneris-document-ai-sdk`; root package is `ai.cogneris.documentai`; source and target level are Java 17.
- OpenAPI Generator is exactly `7.25.0`; its runtime is exactly jdk4py `17.0.9.2`.
- Java builds use the generated Gradle wrapper at exactly `8.14.5` with distribution SHA-256 `6f74b601422d6d6fc4e1f9a1ab6522f642c2fdcbc15ae33ebd30ba3d7198e854`.
- Public facade parity means `extract`, `submitJob`, `getJob`, `waitForJob`, `cancelJob`, `us`/`eu`, bearer auth, multipart upload, `Retry-After`, safe typed errors, cancellation, and bounded timeout behavior.
- Every generated SDK directory contains exact copies of repository `LICENSE` and `NOTICE`; built `.nupkg` and `.jar` artifacts contain both legal files.
- Generation is one atomic transaction: failure in any language preserves the entire previous `sdks/` tree.
- Package consumers must install only built artifacts; C# `ProjectReference` and Java source-directory classpaths are forbidden.
- No NuGet or Maven Central publication job is added. GitHub release/dry-run artifacts are the only new distribution output.
- Existing TypeScript, CLI, and Python generation, package, security, and consumer checks remain mandatory.

---

## File map

### Generator and contract

- `openapi/cogneris-openapi.yaml`: canonical contract; quote the flow-mapping 404 description so OpenAPI Generator validation succeeds without bypass flags.
- `scripts/sdk-config/generators.json`: exact generator/runtime pins and package identities for all four SDKs.
- `scripts/sdk-config/csharp.json`: OpenAPI Generator options for `generichost`, `net8.0`, nullable references, Apache-2.0, and deterministic output.
- `scripts/sdk-config/java.json`: OpenAPI Generator options for the native Java HTTP client, Jackson, Maven coordinates, and deterministic output.
- `scripts/generate-sdks.mjs`: orchestrate both new generators, normalize output, apply overlays/legal files, validate identities/routes, hash outputs, and swap atomically.
- `scripts/run-java.py`: run Gradle under an existing Java 17 or the pinned jdk4py Java 17 without leaking machine-global state.

### C# SDK

- `scripts/sdk-overlays/csharp/files/README.md`: source-build and package-consumer usage, with no NuGet availability claim.
- `scripts/sdk-overlays/csharp/files/src/Cogneris.DocumentAI/CognerisClient.cs`: regions, configuration, document/job methods, retry parsing, cancellation, and lifecycle.
- `scripts/sdk-overlays/csharp/files/src/Cogneris.DocumentAI/CognerisExceptions.cs`: safe typed public errors.
- `sdks/csharp/**`: generated output plus overlays, legal files, and package metadata.
- `tests/fixtures/csharp-consumer/CognerisSdkSmoke.csproj`: external package-only consumer project.
- `tests/fixtures/csharp-consumer/Program.cs`: loopback proof for auth, multipart, envelopes, polling, retry, cancellation, and safe errors.

### Java SDK

- `scripts/sdk-overlays/java/files/README.md`: source-build and package-consumer usage, with no Maven Central availability claim.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisClient.java`: regions, configuration, document/job methods, retry parsing, interruption, and bounded polling.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisException.java`: base safe error.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisApiException.java`: sanitized HTTP/API error.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisTransportException.java`: sanitized network error.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisResponseException.java`: sanitized contract-decoding error.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisJobTerminalException.java`: failed/cancelled job error.
- `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisMaxAttemptsException.java`: bounded polling error.
- `sdks/java/**`: generated output plus overlays, legal files, Java 17 build settings, and package metadata.
- `tests/fixtures/java-consumer/settings.gradle`: isolated external build identity.
- `tests/fixtures/java-consumer/build.gradle`: artifact-only dependency resolution from a staged Maven repository.
- `tests/fixtures/java-consumer/src/test/java/ai/cogneris/consumer/CognerisSdkSmokeTest.java`: loopback behavior proof.

### Release, CI, and documentation

- `scripts/sdk-release.py`: build, inspect, hash, install, and execute consumers for the five package families.
- `tests/test_sdk_generation.py`: generator, output, manifest, identity, build, atomicity, and forbidden-route contracts.
- `tests/test_sdk_helpers.py`: orchestration of C# and Java installed-package smoke suites.
- `tests/test_sdk_release.py`: NuGet/JAR/POM archive safety, legal metadata, tamper rejection, and clean install.
- `tests/test_sdk_workflows.py`: exact GitHub Actions execution contract including .NET 8 and Java 17.
- `tests/test_documentation.py`: truthful language/runtime/artifact documentation assertions.
- `.github/workflows/validate.yml`: PR/main build of all SDKs and artifact consumers.
- `.github/workflows/release-sdks.yml`: manual dry-run artifact construction without new registry publication.
- `package.json`: focused C# and Java verification commands and aggregate SDK verification.
- `README.md`, `RELEASING.md`, `VERSIONING.md`, `SUPPORT.md`: public boundaries and local artifact usage.
- `examples/dotnet/Quickstart.cs`, `examples/java/Quickstart.java`: facade examples used by documentation checks.

---

### Task 1: Make the contract valid for the pinned generator and lock the Java toolchain

**Files:**
- Modify: `openapi/cogneris-openapi.yaml:413`
- Modify: `scripts/sdk-config/generators.json`
- Create: `scripts/sdk-config/csharp.json`
- Create: `scripts/sdk-config/java.json`
- Create: `scripts/run-java.py`
- Modify: `tests/test_sdk_generation.py`

**Interfaces:**
- Produces: `generators.csharp` and `generators.java` pins consumed by `generate-sdks.mjs` and tests.
- Produces: `run-java.py -- <command> [args...]`, which exits with the child status and provides a verified Java 17 `JAVA_HOME`.

- [ ] **Step 1: Add failing configuration and contract-validation tests**

Extend `test_generator_versions_are_exactly_pinned` with these exact entries and add a validation test:

```python
"csharp": {
    "package": "openapi-generator-cli",
    "version": "7.25.0",
    "runtime": {"package": "jdk4py", "version": "17.0.9.2"},
},
"java": {
    "package": "openapi-generator-cli",
    "version": "7.25.0",
    "runtime": {"package": "jdk4py", "version": "17.0.9.2"},
    "gradle": {
        "version": "8.14.5",
        "distributionSha256": "6f74b601422d6d6fc4e1f9a1ab6522f642c2fdcbc15ae33ebd30ba3d7198e854",
    },
},
```

```python
def test_contract_passes_pinned_openapi_generator_validation(self):
    result = subprocess.run(
        [
            "uvx", "--from", "openapi-generator-cli==7.25.0",
            "--with", "jdk4py==17.0.9.2", "openapi-generator-cli",
            "validate", "-i", str(ROOT / "openapi/cogneris-openapi.yaml"),
        ],
        cwd=ROOT, text=True, capture_output=True,
    )
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
```

- [ ] **Step 2: Run the tests and observe the expected failure**

Run:

```bash
uv run --with PyYAML==6.0.3 python -m unittest \
  tests.test_sdk_generation.SdkGenerationTests.test_generator_versions_are_exactly_pinned \
  tests.test_sdk_generation.SdkGenerationTests.test_contract_passes_pinned_openapi_generator_validation -v
```

Expected: the pin assertion fails and validation reports the unexpected 404 response attribute created by the unquoted flow-mapping comma.

- [ ] **Step 3: Correct YAML serialization and add exact generator configs**

Change the 404 response to block style without changing its text:

```yaml
'404':
  description: No such form, or it belongs to another tenant. The two are indistinguishable by design.
```

Add `csharp.json`:

```json
{
  "packageName": "Cogneris.DocumentAI",
  "packageVersion": "0.1.0",
  "targetFramework": "net8.0",
  "library": "generichost",
  "nullableReferenceTypes": true,
  "licenseId": "Apache-2.0",
  "hideGenerationTimestamp": true
}
```

Add `java.json`:

```json
{
  "groupId": "ai.cogneris",
  "artifactId": "cogneris-document-ai-sdk",
  "artifactVersion": "0.1.0",
  "invokerPackage": "ai.cogneris.documentai",
  "apiPackage": "ai.cogneris.documentai.api",
  "modelPackage": "ai.cogneris.documentai.model",
  "library": "native",
  "dateLibrary": "java8",
  "serializationLibrary": "jackson",
  "hideGenerationTimestamp": true,
  "licenseName": "Apache-2.0",
  "licenseUrl": "https://www.apache.org/licenses/LICENSE-2.0"
}
```

- [ ] **Step 4: Add the Java 17 command runner**

Implement `scripts/run-java.py` with the exact boundary below:

```python
def java_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Return an environment whose java executable reports major version 17."""

def main(arguments: Sequence[str]) -> int:
    """Run arguments after `--` under Java 17 and return the child status."""
```

It must prefer an already configured Java 17, otherwise import
`jdk4py.JAVA_HOME`, verify `java -version` starts with `17.`, prepend its `bin`
directory to `PATH`, and call `subprocess.run` without `shell=True`.

- [ ] **Step 5: Run the focused tests and Java runner proof**

Run:

```bash
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 \
  python -m unittest tests.test_sdk_generation -v
uv run --with jdk4py==17.0.9.2 python scripts/run-java.py -- java -version
```

Expected: generator configuration/validation tests pass and Java reports `17.0.9`.

- [ ] **Step 6: Commit the validated toolchain contract**

```bash
git add openapi/cogneris-openapi.yaml scripts/sdk-config/generators.json \
  scripts/sdk-config/csharp.json scripts/sdk-config/java.json scripts/run-java.py \
  tests/test_sdk_generation.py
git commit -m "build: pin C# and Java SDK generators"
```

---

### Task 2: Extend atomic generation and commit both generated SDK trees

**Files:**
- Modify: `scripts/generate-sdks.mjs`
- Create: `scripts/sdk-overlays/csharp/files/README.md`
- Create: `scripts/sdk-overlays/java/files/README.md`
- Modify: `tests/test_sdk_generation.py`
- Create: `sdks/csharp/**`
- Create: `sdks/java/**`
- Modify: `sdks/manifest.json`

**Interfaces:**
- Consumes: exact pins/configs from Task 1.
- Produces: deterministic `sdks/csharp`, `sdks/java`, and `manifest.packages.csharp/java` entries.

- [ ] **Step 1: Add failing generation-output and manifest assertions**

Expand the SDK loops to `("typescript", "python", "csharp", "java")`, then assert:

```python
self.assertEqual(manifest["packages"]["csharp"]["name"], "Cogneris.DocumentAI")
self.assertEqual(manifest["packages"]["java"]["name"], "ai.cogneris:cogneris-document-ai-sdk")
self.assertIn("LICENSE", manifest["packages"]["csharp"]["files"])
self.assertIn("NOTICE", manifest["packages"]["java"]["files"])
self.assertEqual(
    (SDKS / "java/gradle/wrapper/gradle-wrapper.properties").read_text().count(
        "distributionSha256Sum=6f74b601422d6d6fc4e1f9a1ab6522f642c2fdcbc15ae33ebd30ba3d7198e854"
    ),
    1,
)
```

Add a subprocess shim assertion proving both generator calls contain the exact
`--from openapi-generator-cli==7.25.0` and `--with jdk4py==17.0.9.2` pairs.
Extend the existing output snapshot test with a `uvx` shim that exits `42` on
the second OpenAPI Generator call; assert the command fails and the complete
`sdks/` byte/mode/mtime snapshot is unchanged.

- [ ] **Step 2: Run the focused test and observe missing outputs**

```bash
uv run --with PyYAML==6.0.3 python -m unittest \
  tests.test_sdk_generation.SdkGenerationTests.test_generated_sdk_outputs_are_committed \
  tests.test_sdk_generation.SdkGenerationTests.test_manifest_binds_every_artifact_to_the_public_contract -v
```

Expected: failures name `sdks/csharp`, `sdks/java`, or their absent manifest entries.

- [ ] **Step 3: Add both OpenAPI Generator invocations to the existing staging transaction**

Add a helper and call it twice before overlays:

```javascript
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
```

Do not pass `--skip-validate-spec`. Generate into `stagedOutput/csharp` and
`stagedOutput/java`. From C#, remove `.gitignore`,
`.openapi-generator-ignore`, `.openapi-generator/`, `appveyor.yml`, `api/`,
`docs/`, `docs/scripts/`, and `src/Cogneris.DocumentAI.Test/`. From Java,
remove `.github/`, `.gitignore`, `.openapi-generator-ignore`,
`.openapi-generator/`, `.travis.yml`, `api/`, `docs/`, `git_push.sh`,
`build.sbt`, and `src/test/`. Then apply the repository overlays.

- [ ] **Step 4: Normalize package metadata and legal files**

Extend `applyApprovedLicense` to all four language directories. For C#,
transform the generated project to include:

```xml
<PackageLicenseExpression>Apache-2.0</PackageLicenseExpression>
<None Include="../../LICENSE" Pack="true" PackagePath="" />
<None Include="../../NOTICE" Pack="true" PackagePath="" />
```

For Java, replace both `JavaVersion.VERSION_11` occurrences with
`JavaVersion.VERSION_17`, add the pinned Gradle distribution checksum, and copy
legal files to both the package root and `src/main/resources/META-INF/`.

- [ ] **Step 5: Extend validation and manifest construction**

Validate exact project/POM identity, runtime targets, facade destination paths,
legal files, and forbidden routes for all languages. Add manifest entries:

```javascript
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
```

- [ ] **Step 6: Generate and verify exact committed output**

```bash
npm run generate:sdks
npm run check:sdks
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 \
  python -m unittest tests.test_sdk_generation -v
```

Expected: generation check reports `Generated SDK output is current.` and every generation test passes.

- [ ] **Step 7: Commit the atomic generator expansion**

```bash
git add scripts/generate-sdks.mjs scripts/sdk-overlays/csharp \
  scripts/sdk-overlays/java tests/test_sdk_generation.py sdks/csharp sdks/java \
  sdks/manifest.json
git commit -m "feat: generate C# and Java SDK packages"
```

---

### Task 3: Add the C# facade through a package-only loopback test

**Files:**
- Create: `tests/fixtures/csharp-consumer/CognerisSdkSmoke.csproj`
- Create: `tests/fixtures/csharp-consumer/Program.cs`
- Modify: `tests/test_sdk_helpers.py`
- Create: `scripts/sdk-overlays/csharp/files/src/Cogneris.DocumentAI/CognerisClient.cs`
- Create: `scripts/sdk-overlays/csharp/files/src/Cogneris.DocumentAI/CognerisExceptions.cs`
- Modify: `sdks/csharp/**`
- Modify: `sdks/manifest.json`

**Interfaces:**
- Produces: `CognerisClient(CognerisClientOptions)` implementing `IAsyncDisposable`.
- Produces: `ExtractAsync`, `SubmitJobAsync`, `GetJobAsync`, `WaitForJobAsync`, and `CancelJobAsync` with `CancellationToken` parameters.
- Produces: safe `CognerisException` subclasses with no response body, API key, or uploaded bytes in messages.

- [ ] **Step 1: Write the external C# consumer project**

Use a package reference populated by the test runner, never a project reference:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Cogneris.DocumentAI" Version="0.1.0" />
  </ItemGroup>
</Project>
```

`Program.cs` starts an `HttpListener` on loopback, records requests, and asserts:

```csharp
await using var client = new CognerisClient(new(
    ApiKey: "xtkt_live_package_only_secret",
    Region: CognerisRegion.Us,
    BaseUriForTesting: server.BaseUri));

var extracted = await client.ExtractAsync(
    new MemoryStream("document-bytes"u8.ToArray()),
    "identity.pdf",
    "application/pdf",
    "return id");
var submission = await client.SubmitJobAsync(
    DocumentJobSubmitOperation.Extraction,
    "artifact://tenant/input/reference");
var completed = await client.WaitForJobAsync(
    submission.JobId,
    maxAttempts: 3,
    pollInterval: TimeSpan.Zero);
var cancelled = await client.CancelJobAsync(submission.JobId);
```

The loopback sequence returns `Retry-After: 0`, queued/processing/succeeded
envelopes, an error containing reflected secret text, and a delayed response for
cancellation. Assertions cover bearer auth, multipart filename/content/prompt,
terminal data, retry calls, cancellation, and absence of the reflected/API-key
text from every thrown error.

- [ ] **Step 2: Add a Python test that packs and installs only the NuGet artifact**

Add this orchestration boundary to `tests/test_sdk_helpers.py`:

```python
def test_packed_csharp_sdk_against_loopback(self):
    with tempfile.TemporaryDirectory(prefix="cogneris-csharp-consumer-") as directory:
        root = Path(directory)
        packages = root / "packages"
        subprocess.run([
            "dotnet", "pack",
            str(ROOT / "sdks/csharp/src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj"),
            "-c", "Release", "-o", str(packages),
        ], check=True, cwd=root)
        project = shutil.copytree(ROOT / "tests/fixtures/csharp-consumer", root / "consumer")
        result = subprocess.run([
            "dotnet", "run", "--project", str(project), "--configuration", "Release",
            "--property:RestoreSources=" + str(packages) + ";https://api.nuget.org/v3/index.json",
        ], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
```

Before running, assert neither fixture file contains `ProjectReference` or the
absolute repository path.

- [ ] **Step 3: Run the smoke and observe the missing facade**

```bash
uv run --with PyYAML==6.0.3 python -m unittest \
  tests.test_sdk_helpers.CSharpSdkSmokeTests.test_packed_csharp_sdk_against_loopback -v
```

Expected: package consumer compilation fails because `CognerisClient` and its public exceptions do not exist.

- [ ] **Step 4: Implement the C# public types in overlay source**

Use these exact public signatures:

```csharp
public enum CognerisRegion { Us, Eu }

public sealed record CognerisClientOptions(
    string ApiKey,
    CognerisRegion Region = CognerisRegion.Us,
    Uri? BaseUriForTesting = null);

public Task<Envelope> ExtractAsync(
    Stream content, string fileName, string? contentType = null,
    string? complementaryPrompt = null, CancellationToken cancellationToken = default);
public Task<DocumentJobSubmission> SubmitJobAsync(
    DocumentJobSubmitOperation operation, string inputReference,
    CancellationToken cancellationToken = default);
public Task<DocumentJob> GetJobAsync(Guid jobId, CancellationToken cancellationToken = default);
public Task<DocumentJob> WaitForJobAsync(
    Guid jobId, int maxAttempts = 20, TimeSpan? pollInterval = null,
    CancellationToken cancellationToken = default);
public Task<DocumentJobCancellation> CancelJobAsync(
    Guid jobId, CancellationToken cancellationToken = default);
```

Construct generated `IDocumentsApi`/`IJobsApi` services with `ServiceCollection`,
`AddApiHttpClients`, and `BearerToken`. Restrict `BaseUriForTesting` to
`localhost`, `127.0.0.1`, or `::1`. Consume `Ok()`/`Accepted()` only after the
generated response reports the expected success status. Parse `Retry-After` as
a non-negative integer number of seconds, consume submit hints once, use
`Task.Delay(delay, cancellationToken)`, and translate transport/response errors
to sanitized local exception messages.

- [ ] **Step 5: Regenerate, run the package-only smoke, and prove cancellation**

```bash
npm run generate:sdks
npm run check:sdks
uv run --with PyYAML==6.0.3 python -m unittest \
  tests.test_sdk_helpers.CSharpSdkSmokeTests -v
```

Expected: the external executable resolves `Cogneris.DocumentAI.dll` from its
NuGet cache and exits zero after all loopback assertions.

- [ ] **Step 6: Commit the C# facade and consumer proof**

```bash
git add scripts/sdk-overlays/csharp tests/fixtures/csharp-consumer \
  tests/test_sdk_helpers.py sdks/csharp sdks/manifest.json
git commit -m "feat: add C# document workflow facade"
```

---

### Task 4: Add the Java facade through an isolated Maven-layout consumer

**Files:**
- Create: `tests/fixtures/java-consumer/settings.gradle`
- Create: `tests/fixtures/java-consumer/build.gradle`
- Create: `tests/fixtures/java-consumer/src/test/java/ai/cogneris/consumer/CognerisSdkSmokeTest.java`
- Modify: `tests/test_sdk_helpers.py`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisClient.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisException.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisApiException.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisTransportException.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisResponseException.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisJobTerminalException.java`
- Create: `scripts/sdk-overlays/java/files/src/main/java/ai/cogneris/documentai/CognerisMaxAttemptsException.java`
- Modify: `sdks/java/**`
- Modify: `sdks/manifest.json`

**Interfaces:**
- Produces: `CognerisClient(CognerisClient.Options)`.
- Produces: synchronous `extract`, `submitJob`, `getJob`, `waitForJob`, and `cancelJob` methods over generated Java 17 operations/models.
- Produces: `waitForJob(..., Duration timeout, Duration pollInterval) throws InterruptedException` so interruption is preserved.

- [ ] **Step 1: Write the artifact-only Gradle consumer**

`build.gradle` uses only staged Maven coordinates:

```groovy
plugins { id 'java' }
repositories {
    maven { url = uri(System.getenv('COGNERIS_MAVEN_REPOSITORY')) }
    mavenCentral()
}
dependencies {
    testImplementation 'ai.cogneris:cogneris-document-ai-sdk:0.1.0'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
}
java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
test { useJUnitPlatform() }
```

The fixture contains no source-set or file dependency pointing at `sdks/java`.

- [ ] **Step 2: Write the Java loopback test**

Use `HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0)` and this public call sequence:

```java
var client = new CognerisClient(new CognerisClient.Options(
    "xtkt_live_package_only_secret",
    CognerisClient.Region.US,
    serverUri));
var extracted = client.extract(file, "return id");
var submission = client.submitJob(
    DocumentJobSubmitOperation.EXTRACTION,
    "artifact://tenant/input/reference");
var completed = client.waitForJob(
    submission.getJobId(), 3, Duration.ofSeconds(2), Duration.ZERO);
var cancelled = client.cancelJob(submission.getJobId());
```

Mirror the C# server assertions and add one thread-interruption assertion:

```java
thread.start();
thread.interrupt();
thread.join(Duration.ofSeconds(2));
assertFalse(thread.isAlive());
assertInstanceOf(InterruptedException.class, observed.get());
```

- [ ] **Step 3: Add the isolated repository staging test runner**

In `tests/test_sdk_helpers.py`, build the SDK, generate its POM, copy only the
JAR and POM to this layout, then execute the fixture:

```text
repository/ai/cogneris/cogneris-document-ai-sdk/0.1.0/
  cogneris-document-ai-sdk-0.1.0.jar
  cogneris-document-ai-sdk-0.1.0.pom
```

Run Gradle through:

```python
command = [
    "uv", "run", "--with", "jdk4py==17.0.9.2", "python",
    str(ROOT / "scripts/run-java.py"), "--", "sh", str(ROOT / "sdks/java/gradlew"),
    "--no-daemon", "--project-dir", str(consumer), "test",
]
```

- [ ] **Step 4: Run the smoke and observe the missing Java facade**

```bash
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 python -m unittest \
  tests.test_sdk_helpers.JavaSdkSmokeTests.test_packed_java_sdk_against_loopback -v
```

Expected: consumer compilation fails because `ai.cogneris.documentai.CognerisClient` is absent.

- [ ] **Step 5: Implement the Java facade and exceptions**

Use these exact public types and signatures:

```java
public final class CognerisClient {
  public enum Region { US, EU }
  public record Options(String apiKey, Region region, URI baseUriForTesting) {}

  public Envelope extract(Path file, String complementaryPrompt);
  public DocumentJobSubmission submitJob(
      DocumentJobSubmitOperation operation, String inputReference);
  public DocumentJob getJob(UUID jobId);
  public DocumentJob waitForJob(
      UUID jobId, int maxAttempts, Duration timeout, Duration pollInterval)
      throws InterruptedException;
  public DocumentJobCancellation cancelJob(UUID jobId);
}
```

Configure generated `ApiClient`, `DocumentsApi`, and `JobsApi`; restrict the
test base URI to loopback; obtain `Retry-After` from `ApiResponse` headers;
validate positive attempts, finite non-negative durations, and total deadline;
use `Thread.sleep`; preserve the interrupted flag by propagating
`InterruptedException`; and never include generated `ApiException` body text in
public exception messages.

- [ ] **Step 6: Regenerate and run the isolated Java consumer**

```bash
npm run generate:sdks
npm run check:sdks
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 python -m unittest \
  tests.test_sdk_helpers.JavaSdkSmokeTests -v
```

Expected: Java 17 compiles and the external Gradle consumer passes all loopback tests using only staged Maven coordinates.

- [ ] **Step 7: Commit the Java facade and consumer proof**

```bash
git add scripts/sdk-overlays/java tests/fixtures/java-consumer \
  tests/test_sdk_helpers.py sdks/java sdks/manifest.json
git commit -m "feat: add Java document workflow facade"
```

---

### Task 5: Build and verify NuGet and Maven release artifacts

**Files:**
- Modify: `scripts/sdk-release.py`
- Modify: `tests/test_sdk_release.py`
- Modify: `tests/test_sdk_generation.py`

**Interfaces:**
- Replaces the filename-to-name map with artifact descriptors and adds `Cogneris.DocumentAI.<version>.nupkg`, `cogneris-document-ai-sdk-<version>.jar`, and `cogneris-document-ai-sdk-<version>.pom`.
- Extends `package_metadata(path)` to safely parse NuGet nuspec and Java POM/JAR metadata under existing archive resource limits.
- Extends `clean_install(arguments)` to run both new external consumer suites unless `--python-only` is selected.

- [ ] **Step 1: Add failing exact-artifact and legal-content assertions**

Change the expected manifest set to:

```python
{
    "cogneris-ai-document-ai-sdk-0.1.0.tgz",
    "cogneris-ai-document-ai-cli-0.1.0.tgz",
    "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl",
    "Cogneris.DocumentAI.0.1.0.nupkg",
    "cogneris-document-ai-sdk-0.1.0.jar",
    "cogneris-document-ai-sdk-0.1.0.pom",
}
```

Inspect `.nuspec` for ID/version/license and root `LICENSE`/`NOTICE`; inspect the
JAR for `META-INF/LICENSE`, `META-INF/NOTICE`, generated facade classes, and a
Java 17 class-file major version of 61; inspect the POM for exact coordinates.

- [ ] **Step 2: Run release tests and observe the missing package families**

```bash
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 python -m unittest \
  tests.test_sdk_release.ReleaseArtifactTests.test_built_artifacts_carry_the_approved_apache_license_and_notice \
  tests.test_sdk_release.ReleaseArtifactTests.test_real_artifacts_install_and_reject_tampering_before_publication -v
```

Expected: built filename and metadata assertions fail for NuGet and Java.

- [ ] **Step 3: Extend clean source/version binding**

Add both SDK directories to `BUILD_DIRECTORIES`, `scripts/run-java.py` to
`BUILD_FILES`, and exact version checks:

```python
require(csharp_project_version == version,
        "C# package version does not exactly match release input")
require(java_project_version == version,
        "Java package version does not exactly match release input")
```

Parse XML with `xml.etree.ElementTree`; do not use regular expressions for the
NuGet project or Maven POM identity.

- [ ] **Step 4: Build both package families from the clean snapshot**

Inside `build(arguments)`, after the wheel:

```python
run(["dotnet", "pack", checkout / csharp_project, "-c", "Release", "-o", staged], checkout)
run(java_command(checkout, "clean", "test", "jar", "generatePomFileForMavenPublication"), checkout)
shutil.copyfile(checkout / java_jar, staged / f"cogneris-document-ai-sdk-{version}.jar")
shutil.copyfile(checkout / java_pom, staged / f"cogneris-document-ai-sdk-{version}.pom")
```

`java_command` must invoke `scripts/run-java.py` without a shell interpolation
boundary. Update the success message to `Built 5 package families`.

- [ ] **Step 5: Extend bounded metadata inspection and exact integrity checks**

Treat `.nupkg` and `.jar` as ZIP containers under the existing entry/count/size
limits. Require one nuspec, parse XML without external entities, and require one
copy of each legal file. For JAR, require exact `META-INF/LICENSE` and
`META-INF/NOTICE`. Parse `.pom` only after its byte limit and real-file checks;
require its exact coordinates and Apache-2.0 license name/URL, while treating it
as the JAR's metadata sidecar rather than an archive that embeds legal files.
Bind all six files to the release manifest SHA-256 map. The NuGet package and
Java JAR remain the legal-text containers for their package families.

- [ ] **Step 6: Add both external consumers to clean installation**

Stage the NuGet package source and Maven directory inside the owned temporary
consumer root. Copy the tracked fixtures, set only scoped environment variables,
and run their existing package-only tests. Preserve `--python-only` behavior for
the Python compatibility matrix; it must skip Node, C#, and Java consumers.

- [ ] **Step 7: Run focused and complete release tests**

```bash
uv run --with PyYAML==6.0.3 --with jdk4py==17.0.9.2 \
  python -m unittest tests.test_sdk_release tests.test_sdk_helpers -v
```

Expected: archive adversarial tests, legal metadata, tamper rejection, and all
four SDK consumer families pass.

- [ ] **Step 8: Commit release construction and verification**

```bash
git add scripts/sdk-release.py tests/test_sdk_release.py tests/test_sdk_generation.py
git commit -m "build: verify NuGet and Java release artifacts"
```

---

### Task 6: Add public examples and truthful repository documentation

**Files:**
- Create: `examples/dotnet/Quickstart.cs`
- Create: `examples/java/Quickstart.java`
- Modify: `README.md`
- Modify: `RELEASING.md`
- Modify: `VERSIONING.md`
- Modify: `SUPPORT.md`
- Modify: `tests/test_documentation.py`

**Interfaces:**
- Produces: source/build artifact instructions for all four SDK languages.
- Preserves: explicit statement that npm, PyPI, NuGet, and Maven Central availability requires a separately verified registry release.

- [ ] **Step 1: Add failing documentation assertions**

Require the four SDK names, runtime floors, exact artifact filenames, and registry boundary:

```python
for text in (
    "Cogneris.DocumentAI", "net8.0", "Cogneris.DocumentAI.0.1.0.nupkg",
    "ai.cogneris:cogneris-document-ai-sdk", "Java 17",
    "cogneris-document-ai-sdk-0.1.0.jar", "not published to NuGet or Maven Central",
):
    self.assertIn(text, readme)
```

Also reject `dotnet add package Cogneris.DocumentAI` and a Maven dependency block
unless the surrounding section identifies an explicit local artifact source.

- [ ] **Step 2: Run the documentation test and observe missing languages**

```bash
npm run test:docs
```

Expected: assertions fail for the C# and Java package/runtime documentation.

- [ ] **Step 3: Add runnable facade examples**

C# example core:

```csharp
await using var client = new CognerisClient(new(
    Environment.GetEnvironmentVariable("COGNERIS_API_KEY")
        ?? throw new InvalidOperationException("COGNERIS_API_KEY is required"),
    CognerisRegion.Us));
await using var input = File.OpenRead(args[0]);
var result = await client.ExtractAsync(input, Path.GetFileName(args[0]));
Console.WriteLine(result);
```

Java example core:

```java
var client = new CognerisClient(new CognerisClient.Options(
    Objects.requireNonNull(System.getenv("COGNERIS_API_KEY"), "COGNERIS_API_KEY is required"),
    CognerisClient.Region.US,
    null));
var result = client.extract(Path.of(args[0]), null);
System.out.println(result);
```

- [ ] **Step 4: Update repository and release documentation**

Document:

- .NET 8 and Java 17 runtime/build prerequisites;
- exact local `.nupkg`, `.jar`, and `.pom` use from owner-provided release artifacts;
- all four facade workflows and region names;
- safe typed error/cancellation semantics;
- five package families in the dry run;
- Apache-2.0 packaging;
- the explicit absence of NuGet/Maven Central publishing jobs and availability.

- [ ] **Step 5: Run documentation and generation checks**

```bash
npm run test:docs
npm run check:sdks
git diff --check
```

Expected: documentation contracts and generated output checks pass with no whitespace errors.

- [ ] **Step 6: Commit examples and documentation**

```bash
git add examples/dotnet examples/java README.md RELEASING.md VERSIONING.md \
  SUPPORT.md tests/test_documentation.py
git commit -m "docs: document C# and Java SDK artifacts"
```

---

### Task 7: Put .NET 8 and Java 17 into CI and release dry runs

**Files:**
- Modify: `package.json`
- Modify: `.github/workflows/validate.yml`
- Modify: `.github/workflows/release-sdks.yml`
- Modify: `tests/test_sdk_workflows.py`

**Interfaces:**
- Produces: `npm run test:sdk:csharp` and `npm run test:sdk:java`.
- Produces: aggregate `verify:sdks` and release-build paths that compile/test all four SDKs and verify five package families.

- [ ] **Step 1: Expand the executable workflow contract first**

Add pinned allowed actions:

```python
ALLOWED_ACTIONS = {
    "actions/checkout", "actions/setup-node", "actions/setup-python",
    "actions/setup-dotnet", "actions/setup-java",
    "actions/upload-artifact", "actions/download-artifact",
    "pypa/gh-action-pypi-publish",
}
```

Require these exact actions in the build job:

```yaml
- uses: actions/setup-dotnet@26b0ec14cb23fa6904739307f278c14f94c95bf1 # v5
  with:
    dotnet-version: 8.0.x
- uses: actions/setup-java@b6effb05e454b25005698d916606bdc6ffcbf961 # v5
  with:
    distribution: temurin
    java-version: '17'
```

Require the focused C#/Java package consumer commands before artifact upload.

- [ ] **Step 2: Run workflow tests and observe contract mismatch**

```bash
npm run test:workflows
```

Expected: both workflow documents fail their exact step/action contract.

- [ ] **Step 3: Add package scripts**

Add:

```json
"test:sdk:csharp": "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sdk_helpers.CSharpSdkSmokeTests -v",
"test:sdk:java": "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sdk_helpers.JavaSdkSmokeTests -v",
"verify:sdks": "npm run check:sdks && npm run test:sdk:typescript && npm run test:sdk:python && npm run test:sdk:csharp && npm run test:sdk:java"
```

The CI jobs already provide .NET 8 and Java 17; local full-suite commands use
the pinned jdk4py wrapper established in Task 1.

- [ ] **Step 4: Update both workflows without adding registry publication**

Insert the pinned setup actions into `validate.yml` and the release build job.
Keep the existing `publish-npm` and `publish-pypi` jobs unchanged except for
their dependency on the stronger build proof. Do not add `publish-nuget` or
`publish-maven` jobs. The uploaded artifact directory contains the six exact
files plus `manifest.json`.

- [ ] **Step 5: Run workflow contracts and all focused SDK tests**

```bash
npm run test:workflows
npm run verify:sdks
```

Expected: exact workflow contracts pass, and all four SDK package consumers pass.

- [ ] **Step 6: Commit CI and script integration**

```bash
git add package.json .github/workflows/validate.yml \
  .github/workflows/release-sdks.yml tests/test_sdk_workflows.py
git commit -m "ci: validate C# and Java SDK artifacts"
```

---

### Task 8: Run the full clean proof and finish the SDK pull request

**Files:**
- Modify only if a failing check exposes a scoped defect in files from Tasks 1-7.

**Interfaces:**
- Produces: merged SDK commit, green remote checks, and exact artifact evidence consumed by the later site plan.

- [ ] **Step 1: Rebuild committed generated outputs and verify no drift**

```bash
npm run generate:sdks
git status --short
npm run check:sdks
```

Expected: generation changes no tracked file after the regenerated tree is committed.

- [ ] **Step 2: Run the complete local gate set**

```bash
npm run audit:deps
npm run verify:sdks
npm run test:cli
npm run build:cli
npm run test:docs
npm run test:workflows
npm test
```

Expected: every command exits zero.

- [ ] **Step 3: Build and verify the exact release artifact set from committed inputs**

```bash
release_root=$(mktemp -d -t cogneris-sdk-release.XXXXXX)
npm run pack:sdks -- --version 0.1.0 --output "$release_root/artifacts"
manifest_sha=$(shasum -a 256 "$release_root/artifacts/manifest.json" | cut -d ' ' -f 1)
npm run verify:artifacts -- --version 0.1.0 \
  --artifacts "$release_root/artifacts" \
  --manifest-sha256 "$manifest_sha" \
  --source "$(git rev-parse HEAD)"
```

Expected: five package families pass exact digest, metadata, legal-file, and isolated-consumer verification. The temporary directory is retained only long enough to record filenames/digests, then removed using an explicit validated path.

- [ ] **Step 4: Review and commit any final generated/documentation reconciliation**

```bash
git diff --check
git status --short
git add sdks README.md RELEASING.md VERSIONING.md SUPPORT.md
git diff --cached --check
git commit -m "chore: reconcile generated SDK release output"
```

Skip the commit when the index is empty.

- [ ] **Step 5: Push and update the existing draft pull request**

```bash
git push origin codex/xtrak-1615-csharp-java-sdks-20260917
gh pr ready 17
gh pr edit 17 --title "XTRAK-1615: add C# and Java SDKs"
```

Update the PR body with exact local results, package filenames, registry
non-publication boundary, and the current commit SHA.

- [ ] **Step 6: Wait for required checks and merge only on green**

```bash
gh pr checks 17 --watch
gh pr merge 17 --squash --delete-branch
git fetch origin main --prune
gh pr view 17 --json state,mergedAt,mergeCommit,url
```

Expected: PR state is `MERGED` with non-null `mergedAt`. If any required check
fails, keep the branch/worktree and repair the scoped failure before merging.

- [ ] **Step 7: Capture site-input evidence and clean this session worktree**

Record:

```text
merged SDK commit
PR URL
workflow run URLs and conclusions
artifact names and SHA-256 values
NuGet/Maven Central status: not published
```

After merge proof, remove only this task's clean worktree and local branch, then
run `git worktree prune`. The subsequent site change starts in a new branch and
worktree from the then-current `cogneris-site/origin/main`.

---

## Dependent site phase

The public-site work is a separate subsystem and repository, so it receives a
separate implementation plan in `cogneris-site` after Task 8 produces merged
evidence. That plan must use the current site `AGENTS.md`, create
`src/docs-dotnet-sdk.html` and `src/docs-java-sdk.html`, update quickstart/language
matrix/document-capture claims, regenerate `src/llms-full.txt`, sitemap dates,
and i18n catalogs, and retain the explicit statement that NuGet and Maven Central
publication has not occurred.
