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

For C#, state whether you installed the verified public
[Cogneris.DocumentAI 0.1.0](https://www.nuget.org/packages/Cogneris.DocumentAI/0.1.0)
release from NuGet.org or a local `Cogneris.DocumentAI.0.2.0.nupkg` built from source.
For Java, state whether you installed the verified public
[ai.cogneris:cogneris-document-ai-sdk:0.1.0](https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/)
release from Maven Central or a local `cogneris-document-ai-sdk-0.2.0.jar`
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
