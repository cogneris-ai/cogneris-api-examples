# Versioning and compatibility

The TypeScript SDK (`@cogneris-ai/document-ai-sdk`), Python SDK
(`cogneris-document-ai-sdk`), C# SDK (`Cogneris.DocumentAI`), Java SDK
(`ai.cogneris:cogneris-document-ai-sdk`), and TypeScript CLI
(`@cogneris-ai/document-ai-cli`) use Semantic Versioning. The committed source
is `0.2.0` for all five families, and `0.2.0` is unpublished on every registry.
The Java [ai.cogneris:cogneris-document-ai-sdk:0.1.0](https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/)
is published on Maven Central, with public artifact integrity, PGP signatures,
and Java 17 installation verified on 2026-09-21.
The committed source is `0.2.0` for all five families, and `0.2.0` is
unpublished on every registry.
The npm [SDK 0.1.0](https://www.npmjs.com/package/@cogneris-ai/document-ai-sdk/v/0.1.0)
and [CLI 0.1.0](https://www.npmjs.com/package/@cogneris-ai/document-ai-cli/v/0.1.0)
are published, with public tarball integrity and installation verified on 2026-09-21.
[cogneris-document-ai-sdk 0.1.0](https://pypi.org/project/cogneris-document-ai-sdk/0.1.0/)
is published on PyPI, with its public wheel and installation verified on 2026-09-21.
[Cogneris.DocumentAI 0.1.0](https://www.nuget.org/packages/Cogneris.DocumentAI/0.1.0)
is published on NuGet.org, with public installation verified on 2026-09-21.
A package version or local artifact alone does not prove registry availability.

Every generated SDK release is tied to a dated public OpenAPI contract. The
current artifacts are generated from Cogneris Document AI OpenAPI version
`2026-09-24` (the published `0.1.0` releases were generated from `2026-08-07`); [`sdks/manifest.json`](sdks/manifest.json) records the exact
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

## Release notes

### 0.2.0

Generated from OpenAPI contract `2026-09-24`, replacing `2026-08-07`. A minor
release under the policy above: it supports a new compatible contract.

Compatibility impact: **additive, with one nullable widening.** Compared symbol
by symbol against the `0.1.0` output of all four SDKs, no operation, model or
field was removed or renamed. One field was retyped:
`ProblemDetails.errors[].field` is now nullable (`string | null` in TypeScript,
`Optional[str]` in Python), because the service sends `null` there. Code that
reads it under TypeScript `strictNullChecks` must handle `null`; C# and Java
already exposed it as a nullable reference. Everything else written against
`0.1.0` needs no change.

- New Artifacts API in every SDK: `uploadArtifact` (`POST /api/v1/artifacts`)
  stores a job's input and returns the `artifact://` reference that job
  submission takes; `downloadArtifact` (`GET /api/v1/artifacts/content`) reads
  back an upload or a finished job's `outputReference`. New models `Artifact`
  and `ArtifactUploadEnvelope`.
- New `ExtractedField` model (and `BoundingBox` in TypeScript) documenting the
  entries of `data.metadata`: `value`, `confidence` from `0` to `100`, and, when
  the value was located on the page, `page`, `bbox`, and `bbox_confidence`.
  `data.metadata` keeps its open type, so these entries arrive exactly as they
  did in `0.1.0`.
- Generated documentation describes the per-field coordinate convention, the
  `artifact://` reference lifecycle, and `outputReference`.
- Fields the service already returned are now typed (XTRAK-1798):
  classifier `results` (`ClassificationResult`), zero-shot `documentType` and
  `confidence`, extraction `fraudBlocked`, `fraudRequestId` and `quality`
  (`QualityAssessment`, `QualityFinding`, `QualityVerdict`), crop `imageUrls`,
  `documents` (`CropDocument`) and `compositeImageUrl`, and facematch
  `requestId`, `extractions` (`FaceExtraction`) and `matches` (`FaceMatch`), all
  on the shared document envelope's `data`; `creditsConsumed` on `DocumentJob`.
- Every operation now declares its error responses — `400`, `401`, `403`,
  `404`, `409`, `429` and `500` — with a typed `ProblemDetails` body, which
  gains `field` and `errors[].details`. Where an operation already typed an
  error as `ServiceErrorEnvelope` (cancel `409`, download `400`/`410`), that
  type is kept.
- Job submission accepts an optional `templateId` for an `Extraction` job, which
  names the finished template to extract with (XTRAK-1816).
- The Python `CognerisClient` reports an error status whose body is not JSON —
  an HTML `429` from a proxy, an empty `401` — as `CognerisApiError` with its
  `status`, as it did in `0.1.0`, rather than as a contract mismatch.
- The CLI changes only its exact SDK dependency, to `0.2.0`; its commands,
  options, and output are unchanged.
- `CognerisClient` helpers are unchanged. Artifact upload is reachable through
  the generated Artifacts API, not a helper.

The Python SDK's `CHANGELOG.md` carries the same notes with Python names.

## Deprecation notice

Before a supported helper, command, or generated public operation is removed,
the deprecation must be announced in repository release notes and the relevant
documentation, including its replacement and the first version that may remove
it. No fixed deprecation window is promised until the service owner approves
and publishes one. Urgent security or legal changes may require a shorter
window and must be identified explicitly in the release notes.

Contract features absent from OpenAPI version `2026-09-22` are not deprecated;
they are unsupported and must not be inferred from an internal service.
