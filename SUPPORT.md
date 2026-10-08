# Support policy

This repository supports the public Cogneris Document AI contract and the
generated TypeScript, Python, C#/.NET 8, and Java 17 SDK artifacts, CLI artifact,
examples, and Postman collection built from it. Support covers reproducible generation,
installation from a release artifact, documented authentication and region
selection, and behavior represented by the dated public OpenAPI contract.

For reproducible defects or documentation problems, open a GitHub Issue in
[`cogneris-ai/cogneris-api-examples`](https://github.com/cogneris-ai/cogneris-api-examples/issues).
Include the artifact version, OpenAPI contract version, runtime version,
command or minimal reproduction, safe error class/status, and region. Remove
API keys, document contents, extracted values, raw responses, tenant data, and
input/output references before posting.

## Registry and source versions

The public registry versions below were checked on **2026-10-03**. “Source” is
the version recorded in checked-in SDK or CLI metadata, or the Flutter source
tag; it does not imply that the same version has been published to that registry.

| Artifact | Source version | Latest public registry version |
| --- | --- | --- |
| TypeScript SDK, `@cogneris-ai/document-ai-sdk` | `1.0.0` | [npm `0.2.0`](https://www.npmjs.com/package/@cogneris-ai/document-ai-sdk/v/0.2.0) |
| TypeScript CLI, `@cogneris-ai/document-ai-cli` | `1.0.0` | [npm `0.2.0`](https://www.npmjs.com/package/@cogneris-ai/document-ai-cli/v/0.2.0) |
| Python SDK, `cogneris-document-ai-sdk` | `1.0.0` | [PyPI `0.2.0`](https://pypi.org/project/cogneris-document-ai-sdk/0.2.0/) |
| C# SDK, `Cogneris.DocumentAI` | `1.0.0` | [NuGet.org `0.1.0`](https://www.nuget.org/packages/Cogneris.DocumentAI/0.1.0) |
| Java SDK, `ai.cogneris:cogneris-document-ai-sdk` | `1.0.0` | [Maven Central `0.1.0`](https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/) |
| Flutter SDK, `cogneris_sdk` | `0.2.1`, tag `sdk-v0.2.1` | No pub.dev package (`publish_to: none`) |

The C# and Java source versions are newer than their current public registry
versions. Do not use `1.0.0` as a NuGet or Maven Central install version; use
the versions linked above unless you are building the repository source locally.

## Artifact upload and download helpers

The OpenAPI contract in this repository is dated `2026-09-28`. It defines
`POST /api/v1/artifacts` as a multipart upload that returns an `artifact://`
reference, and `GET /api/v1/artifacts/content?reference=...` as a byte download.
An uploaded reference can be reused and expires after seven days. SDK convenience
methods differ from the generated API methods:

| Source | Upload | Download |
| --- | --- | --- |
| TypeScript `CognerisClient` | `uploadArtifact(file: Blob | File, options: ExtractOptions = {}): Promise<Artifact>` | `downloadArtifact(reference: string): Promise<unknown>` |
| Python `CognerisClient` | `upload_artifact(content: Union[bytes, BinaryIO], *, file_name: str) -> Artifact` | `download_artifact(reference: str) -> object` |
| C# generated `ArtifactsApi` | `UploadArtifactAsync(FileParameter file, CancellationToken cancellationToken = default): Task<IUploadArtifactApiResponse>`; `FileParameter(Stream content, string? fileName = null, string contentType = "application/octet-stream")` | `DownloadArtifactAsync(string reference, CancellationToken cancellationToken = default): Task<IDownloadArtifactApiResponse>`; the successful response exposes a `Stream` |
| Java generated `ArtifactsApi` | `uploadArtifact(File file) throws ApiException` returns an `ArtifactUploadEnvelope` | `downloadArtifact(String reference) throws ApiException` returns a `File` written to a temporary path |

TypeScript and Python expose upload/download on their maintained
`CognerisClient` wrappers. C# and Java expose them through the generated
`ArtifactsApi`, not the higher-level `CognerisClient` facade. The CLI accepts a
local file for synchronous `extract` and accepts an `inputReference` for job
submission; it has no artifact upload or download command. These signatures are
from the checked-in source and do not establish that every source version is
available from its public registry.

For C#, state whether you installed the verified public
[Cogneris.DocumentAI 0.1.0](https://www.nuget.org/packages/Cogneris.DocumentAI/0.1.0)
release from NuGet.org or a local `Cogneris.DocumentAI.1.0.0.nupkg` built from source.
For Java, state whether you installed the verified public
[ai.cogneris:cogneris-document-ai-sdk:0.1.0](https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/)
release from Maven Central or a local `cogneris-document-ai-sdk-1.0.0.jar`
and `.pom` built from source. Include the Java runtime version and dependency
resolution details.

The repository does not provide support for tenant configuration, schema or
template design, service entitlement, Portal administration, private/internal
APIs, destinations, or live-environment operations. A repository issue cannot
grant access, change a tenant, or authorize publication or deployment.

## Security reporting

Do not report suspected vulnerabilities, credentials, customer documents, or
other sensitive details in public GitHub Issues. The owner-approved private
security reporting channel is GitHub Security Advisories: use
[privately report a security vulnerability](https://github.com/cogneris-ai/cogneris-api-examples/security/advisories/new).
Do not report the same information in a public issue. This private channel must
remain enabled before public release of the artifacts.

Version compatibility and deprecation rules are documented in
[`VERSIONING.md`](VERSIONING.md).
