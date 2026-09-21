# Versioning and compatibility

The TypeScript SDK (`@cogneris-ai/document-ai-sdk`), Python SDK
(`cogneris-document-ai-sdk`), C# SDK (`Cogneris.DocumentAI`), Java SDK
(`ai.cogneris:cogneris-document-ai-sdk`), and TypeScript CLI
(`@cogneris-ai/document-ai-cli`) use Semantic Versioning. Their current `0.1.0`
npm and Maven Central artifacts remain unpublished.
[cogneris-document-ai-sdk 0.1.0](https://pypi.org/project/cogneris-document-ai-sdk/0.1.0/)
is published on PyPI, with its public wheel and installation verified on 2026-09-21.
[Cogneris.DocumentAI 0.1.0](https://www.nuget.org/packages/Cogneris.DocumentAI/0.1.0)
is published on NuGet.org, with public installation verified on 2026-09-21.
A package version or local artifact alone does not prove registry availability.

Every generated SDK release is tied to a dated public OpenAPI contract. The
current artifacts are generated from Cogneris Document AI OpenAPI version
`2026-08-07`; [`sdks/manifest.json`](sdks/manifest.json) records the exact
contract SHA-256 and generated file hashes. `npm run check:sdks` verifies that
committed output still matches that input and the pinned generators.

Semantic Versioning applies to the maintained SDK helper and CLI interfaces:

- Patch versions fix compatible implementation, documentation, packaging, or
  generation defects without intentionally changing the public interface.
- Minor versions add backward-compatible public capabilities or support a new
  compatible dated OpenAPI contract.
- Major versions may remove or incompatibly change a public helper, command,
  option, output, or generated contract surface.

While the packages remain below `1.0.0`, release notes must still call out any
compatibility impact explicitly. A newer OpenAPI date is not by itself proof of
backward compatibility; compare the contract and regenerate/check all four SDKs.

## Deprecation notice

Before a supported helper, command, or generated public operation is removed,
the deprecation must be announced in repository release notes and the relevant
documentation, including its replacement and the first version that may remove
it. No fixed deprecation window is promised until the service owner approves
and publishes one. Urgent security or legal changes may require a shorter
window and must be identified explicitly in the release notes.

Contract features absent from OpenAPI version `2026-08-07` are not deprecated;
they are unsupported and must not be inferred from an internal service.
