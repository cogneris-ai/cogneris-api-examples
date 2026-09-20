# Cogneris Document AI quickstart

This repository is the canonical first-result path for the public Cogneris
Document AI API: TypeScript, Python, C#/.NET, Java, the `cogneris` CLI, and
Postman. All of them are built from
[`openapi/cogneris-openapi.yaml`](openapi/cogneris-openapi.yaml),
OpenAPI contract version `2026-08-07`.

For WhatsApp consent and delivery outcomes on the generated Portal API, see
[Portal magic links](docs/portal-magic-links.md).

## License

The SDKs, CLI, examples, documentation, and distributed artifacts in this
repository are licensed under the [Apache License 2.0](LICENSE). Copyright
2026 COGNERIS,INC. See [NOTICE](NOTICE) for scope and attribution. This license
does not grant rights to Cogneris trademarks or logos, access to Cogneris
services, or Cogneris backend code.

## Before you start

The TypeScript SDK and CLI require Node.js `>=20.0.0` for built-in `File`,
`fetch`, and multipart support; use npm 9+ to install the local tarballs. The
Python SDK requires Python `>=3.9,<4.0`. Installing an existing wheel with pip
and running the Python SDK does not require Node.js, npm, or uv. The C# package
`Cogneris.DocumentAI` targets `net8.0` and requires .NET 8. The Java package
`ai.cogneris:cogneris-document-ai-sdk` requires Java 17.

For building from this checkout and running its verification commands, use
Node.js 24 (the CI version), npm 10+, Python 3.12, .NET 8, a full JDK 17 with
`javac`, and `uv`/`uvx` on `PATH`.
The pinned TypeScript generator requires at least Node.js 22.18.0, which is
separate from the installed packages' runtime minimum. Use Python 3.12 for
generation/CI; the Python package is also tested on 3.9–3.14. `npm ci` installs
the pinned TypeScript compiler/generator; `uv build` obtains the declared wheel
build backend, and `uvx` obtains the pinned Python generator and formatter.
The setup commands below use uv for virtual environments and wheel installation;
it is a build/setup tool, not a Python SDK runtime dependency.
The pinned `jdk4py` Java 17 runtime can run the OpenAPI generator and provides
the local runtime fallback, but it is not a full compiler JDK on this host; use
a full JDK 17 to compile the Java SDK or an application.

Use a tenant-scoped API key and select exactly `us` and `eu` as the region. The
SDK examples and CLI read credentials only from `COGNERIS_API_KEY`; they never
accept the key as an argument. `COGNERIS_REGION` defaults to `us`.
The CLI requires the public `xtkt_live_` prefix and a non-empty suffix with
visible ASCII characters, without whitespace or control characters.

```bash
export COGNERIS_API_KEY='xtkt_live_...'
export COGNERIS_REGION='us' # or eu
```

The region maps to `https://api-us.cogneris.ai` or
`https://api-eu.cogneris.ai`. Do not log the key, file contents, extracted
fields, input/output references, or raw response bodies. The examples print
only controlled status summaries and identifiers.

## Install local release artifacts

`@cogneris-ai/document-ai-sdk`, `cogneris-document-ai-sdk`, and
`@cogneris-ai/document-ai-cli` are not published to npm or PyPI. The C# and
Java packages are not published to NuGet or Maven Central, and no repository
workflow publishes them there. Until each registry release is separately
verified, install only locally built or owner-provided local release artifacts.
Do not run a registry install by package name alone.

Choose explicit checkout, release-artifact, and consumer directories. Use
absolute paths so later commands cannot accidentally resolve against a
different working directory:

```bash
export COGNERIS_CHECKOUT=/absolute/path/to/cogneris-api-examples
export COGNERIS_RELEASE="$COGNERIS_CHECKOUT/release"
export COGNERIS_CONSUMER=/absolute/path/to/my-cogneris-consumer
```

Build TypeScript SDK and CLI tarballs plus the Python wheel in the checkout:

```bash
cd "$COGNERIS_CHECKOUT"
npm ci
npm run build --prefix sdks/typescript
npm run build:cli
mkdir -p "$COGNERIS_RELEASE"
npm pack ./sdks/typescript --pack-destination "$COGNERIS_RELEASE"
npm pack ./cli --pack-destination "$COGNERIS_RELEASE"
(cd sdks/python && uv build --wheel --out-dir "$COGNERIS_RELEASE")
```

Set up the separate consumer project. This block installs both npm tarballs in
one operation so the CLI's exact `0.1.0` SDK dependency is satisfied locally,
installs the wheel into a consumer-local virtual environment, and copies the
runnable examples to paths that exist in the consumer:

<!-- consumer-setup:start -->
```bash
export COGNERIS_CHECKOUT="${COGNERIS_CHECKOUT:-/absolute/path/to/cogneris-api-examples}"
export COGNERIS_RELEASE="${COGNERIS_RELEASE:-$COGNERIS_CHECKOUT/release}"
export COGNERIS_CONSUMER="${COGNERIS_CONSUMER:-/absolute/path/to/my-cogneris-consumer}"
mkdir -p "$COGNERIS_CONSUMER/examples/typescript" "$COGNERIS_CONSUMER/examples/python"
cp "$COGNERIS_CHECKOUT/examples/typescript/quickstart.mjs" "$COGNERIS_CONSUMER/examples/typescript/"
cp "$COGNERIS_CHECKOUT/examples/python/quickstart.py" "$COGNERIS_CONSUMER/examples/python/"
cd "$COGNERIS_CONSUMER"
test -f package.json || npm init --yes
npm install "$COGNERIS_RELEASE/cogneris-ai-document-ai-sdk-0.1.0.tgz" "$COGNERIS_RELEASE/cogneris-ai-document-ai-cli-0.1.0.tgz"
uv venv --python "${PYTHON_BIN:-python3}" .venv
uv pip install --python .venv/bin/python "$COGNERIS_RELEASE/cogneris_document_ai_sdk-0.1.0-py3-none-any.whl"
```
<!-- consumer-setup:end -->

## TypeScript: upload or submit and poll

The runnable example imports `CognerisClient` from the official installed
`@cogneris-ai/document-ai-sdk` package. Synchronous extraction sends the file as
`multipart/form-data` and prints only envelope status:

```bash
cd "$COGNERIS_CONSUMER"
node ./examples/typescript/quickstart.mjs extract /path/to/document.pdf
```

For an already-uploaded input reference, submit an asynchronous job and poll it
to a terminal state. The reference must be valid for your tenant; the public
contract does not upload it for you.

```bash
cd "$COGNERIS_CONSUMER"
node ./examples/typescript/quickstart.mjs async Extraction artifact://tenant/input/reference
```

The maintained interface used by the example is:

```js
const client = new CognerisClient({ apiKey: process.env.COGNERIS_API_KEY, region: "us" });
const envelope = await client.extract(file, { fileName: "document.pdf" });
const submission = await client.submitJob("Extraction", "artifact://tenant/input/reference");
const job = await client.waitForJob(submission.jobId);
```

## Python: upload or submit and poll

The Python example imports `CognerisClient` from the installed
`cogneris-document-ai-sdk` wheel:

```bash
cd "$COGNERIS_CONSUMER"
./.venv/bin/python ./examples/python/quickstart.py extract /path/to/document.pdf
./.venv/bin/python ./examples/python/quickstart.py async Extraction artifact://tenant/input/reference
```

The equivalent maintained interface is:

```python
client = CognerisClient(api_key=os.environ["COGNERIS_API_KEY"], region="us")
envelope = client.extract(contents, file_name="document.pdf")
submission = client.submit_job("Extraction", "artifact://tenant/input/reference")
job = client.wait_for_job(submission.job_id)
client.close()
```

## .NET 8: local NuGet package

`Cogneris.DocumentAI.0.1.0.nupkg` is an owner-provided local artifact targeting
`net8.0`; it is not evidence of NuGet availability. Create a separate .NET 8
consumer, copy the runnable example, add the package with the explicit local
source, and restore public transitive dependencies from NuGet.org:

```bash
mkdir -p "$COGNERIS_CONSUMER/dotnet"
cd "$COGNERIS_CONSUMER/dotnet"
dotnet new console --framework net8.0
cp "$COGNERIS_CHECKOUT/examples/dotnet/Quickstart.cs" Program.cs
dotnet add package Cogneris.DocumentAI --version 0.1.0 --source "$COGNERIS_RELEASE" --no-restore
dotnet restore --source "$COGNERIS_RELEASE" --source https://api.nuget.org/v3/index.json
dotnet run -- extract /path/to/document.pdf
```

The example maps `COGNERIS_REGION=us|eu` to `CognerisRegion.Us` or
`CognerisRegion.Eu`. It demonstrates `ExtractAsync`, `SubmitJobAsync`,
`GetJobAsync`, `WaitForJobAsync`, and `CancelJobAsync`; choose the command shown
by `dotnet run` usage. The facade sends bearer authentication and multipart
uploads, honors `Retry-After`, and supports `CancellationToken`. It reports
sanitized `CognerisApiException`, `CognerisTransportException`,
`CognerisResponseException`, `CognerisJobTerminalException`, and
`CognerisMaxAttemptsException` rather than retaining response bodies or keys.

## Java 17: local Maven artifact

Stage the exact `cogneris-document-ai-sdk-0.1.0.jar` and
`cogneris-document-ai-sdk-0.1.0.pom` as one local Maven artifact. A full JDK 17
with `javac` and Apache Maven 3.9 or newer are required; `jdk4py` is not a full
compiler JDK on this host.

```bash
export COGNERIS_MAVEN_REPOSITORY="$COGNERIS_CONSUMER/java/maven-repository"
export COGNERIS_MAVEN_COORDINATES="$COGNERIS_MAVEN_REPOSITORY/ai/cogneris/cogneris-document-ai-sdk/0.1.0"
mkdir -p "$COGNERIS_MAVEN_COORDINATES"
cp "$COGNERIS_RELEASE/cogneris-document-ai-sdk-0.1.0.jar" "$COGNERIS_MAVEN_COORDINATES/"
cp "$COGNERIS_RELEASE/cogneris-document-ai-sdk-0.1.0.pom" "$COGNERIS_MAVEN_COORDINATES/"
```

Create `$COGNERIS_CONSUMER/java/pom.xml` with the dependency bound to that
explicit repository. Maven Central remains available only for the artifact's
public transitive dependencies and build plugins; the Cogneris package itself
resolves from `COGNERIS_MAVEN_REPOSITORY`:

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId>
  <artifactId>cogneris-quickstart</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.release>17</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <repositories>
    <repository>
      <id>cogneris-local-release</id>
      <url>file://${env.COGNERIS_MAVEN_REPOSITORY}</url>
    </repository>
  </repositories>
  <dependencies>
    <dependency>
      <groupId>ai.cogneris</groupId>
      <artifactId>cogneris-document-ai-sdk</artifactId>
      <version>0.1.0</version>
    </dependency>
  </dependencies>
</project>
```

Copy the example into Maven's source layout, compile it, resolve the runtime
classpath from the POM, and invoke it with only the compiled example plus the
resolved package dependencies:

```bash
export COGNERIS_JAVA_CONSUMER="$COGNERIS_CONSUMER/java"
mkdir -p "$COGNERIS_JAVA_CONSUMER/src/main/java"
cp "$COGNERIS_CHECKOUT/examples/java/Quickstart.java" \
  "$COGNERIS_JAVA_CONSUMER/src/main/java/Quickstart.java"
cd "$COGNERIS_JAVA_CONSUMER"
mvn --batch-mode compile dependency:build-classpath \
  -Dmdep.outputFile=target/runtime-classpath.txt
export COGNERIS_JAVA_CLASSPATH="$(tr -d '\r\n' < target/runtime-classpath.txt)"
java -cp "target/classes:$COGNERIS_JAVA_CLASSPATH" Quickstart extract /path/to/document.pdf
```

The command is a package-only first-result path: the consumer has no reference
to `sdks/java` and Maven resolves the Cogneris coordinate from the explicit
local repository. The package remains unavailable from Maven Central. The
example maps `COGNERIS_REGION=us|eu` to `CognerisClient.Region.US` or
`CognerisClient.Region.EU` and demonstrates `extract`, `submitJob`, `getJob`,
`waitForJob`, and `cancelJob`. The facade sends bearer authentication and
multipart uploads, honors `Retry-After`, bounds waits by attempts and a total
timeout, preserves caller interruption for `waitForJob`, and exposes only safe
typed `CognerisException` subclasses for API, transport, response, terminal,
and maximum-attempt failures.

All four SDKs support asynchronous operations `Extraction`, `Classification`,
`ZeroShot`, `Crop`, `Split`, and `Facematch`. Polling honors integer `Retry-After` hints,
stops on success/failure/cancellation, and uses a bounded attempt count.

## CLI

The consumer-local binary is `./node_modules/.bin/cogneris`. Invoke that path
from `$COGNERIS_CONSUMER`; a local npm install does not add it to the user's
shell `PATH`. Its supported grammar is exactly:

```text
./node_modules/.bin/cogneris [--region us|eu] extract <file>
./node_modules/.bin/cogneris [--region us|eu] jobs submit --operation <operation> --input-reference <reference>
./node_modules/.bin/cogneris [--region us|eu] jobs get <job-id>
./node_modules/.bin/cogneris [--region us|eu] jobs wait <job-id>
./node_modules/.bin/cogneris [--region us|eu] jobs cancel <job-id>
```

`--region` overrides `COGNERIS_REGION`. The CLI has no `--api-key` or public
base-URL option. Success is JSON on stdout. Configuration/usage failures exit
2; controlled API/runtime failures exit 1 and go to stderr. CLI JSON can include
contract response fields, so treat it as sensitive unless you reduce it to a
safe status summary before sharing it.

## Responses and errors

Successful synchronous document calls return an `Envelope`: `data` is the
operation payload, `meta` is the `ServiceResponseMeta` shared with the job
endpoints (`httpStatusCode`, `messages`, structured `errors`, and the
`creditsConsumed` charge for the call), and `hasErrors` is the fast
failure indicator. Application code may inspect `data`, but the quickstart
examples deliberately do not print extracted field values or raw bodies.

Asynchronous job endpoints use the same wire envelope. The maintained SDK
helpers unwrap its `data` payload, so `submitJob`/`submit_job`, `getJob`/`get_job`,
and polling return the typed job payload directly. Cancellation is accepted with
HTTP 202 and returns `{jobId, cancellationRequested}` after unwrapping.

The maintained SDK helpers raise typed, locally controlled errors. TypeScript
uses `CognerisApiError`, `CognerisJobTerminalError`, and
`CognerisMaxAttemptsError`; Python additionally distinguishes
`CognerisTransportError` and `CognerisResponseError`. C# and Java expose the
corresponding safe `CognerisApiException`, `CognerisTransportException`,
`CognerisResponseException`, `CognerisJobTerminalException`, and
`CognerisMaxAttemptsException` types. Branch on the error type, HTTP `status`,
terminal job `status`, or `retryable` when present. Do not log the whole request,
response, exception context, document, or credential.

## Public contract limits

- Uploads use `multipart/form-data`. Accepted extensions are `.pdf`, `.png`,
  `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.doc`, and `.docx`.
- The maximum is 10 MB per file except `/Document/split`, which accepts 500 MB.
- There is no fetch-by-URL upload: synchronous documents travel in the request
  body. Asynchronous submission takes a reference to an already-uploaded input.
- One fixed-window limit covers the contract: 50 requests per API key per
  1-minute window. Excess requests return HTTP 429.
- Schema is selected by tenant configuration and the document itself. There is
  no public schema or template parameter on extraction requests.
- Public evidence, cost, destination, and webhook-signature APIs are absent
  from OpenAPI contract `2026-08-07`. Do not fabricate calls or infer private
  service behavior for those capabilities.
- `CognerisClient` is the maintained document/job helper. Portal,
  administrative, and internal APIs are not SDK helper features. Public Portal
  operations that exist in the generated contract have separate scopes and
  response rules; this quickstart does not present them as document helpers.

## Postman path

The existing Postman workflow remains supported:

1. Import [`postman/Cogneris-API.postman_collection.json`](postman/Cogneris-API.postman_collection.json).
2. Set the secret collection variable `bearerToken` to a valid key. The
   committed value is intentionally empty.
3. Use **Documents → extraction → Extract structured fields from a document**
   and select a local file in the `file` form-data field.
4. Keep optional form-data fields deselected unless needed.

`ComplementaryPrompt` is appended verbatim to the model prompt. Classifier and
facematch accept multiple files. The collection defaults to the US endpoint;
set `baseUrl` to `https://api-eu.cogneris.ai` for an EU-hosted tenant.

The existing opt-in live smoke uses its historical `COGNERIS_KEY` input and a
non-sensitive local file. It reports response shape, not extracted values:

```bash
COGNERIS_KEY=xtkt_live_... npm run smoke:live -- --file /path/to/document.pdf
```

For an EU-hosted tenant, add `--base-url https://api-eu.cogneris.ai` to this
legacy live-smoke command.

This live-smoke compatibility path is separate from the SDK examples and CLI,
which use only `COGNERIS_API_KEY` and `COGNERIS_REGION`.

## Regeneration, support, and versions

Regenerate Postman and verify deterministic SDK output with:

```bash
npm run generate
npm run generate:sdks
npm test
npm run check:sdks
```

The OpenAPI source is copied from `cogneris-site/src/openapi.yaml`. The Postman
generator removes unstable converter IDs, adds an empty secret-typed
`bearerToken`, and uses a fixed random seed so identical input produces the
same committed collection. Neither generator persists credentials.

See [`SUPPORT.md`](SUPPORT.md) for support and security reporting boundaries and
[`VERSIONING.md`](VERSIONING.md) for Semantic Versioning, dated OpenAPI
compatibility, and deprecation notice policy.

See [`RELEASING.md`](RELEASING.md) for local artifact verification, the manual
dry-run workflow, and the owner-controlled gates required before publication.
