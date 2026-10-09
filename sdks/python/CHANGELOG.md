# Changelog

## 1.0.0

Generated from OpenAPI contract `2026-09-28`. Compatibility impact: **major**.
The public `DocumentJobSubmitStatus` type, which only represented `Queued`, was
removed and replaced in `DocumentJobSubmission.status` by the existing broader
`DocumentJobStatus` type. Source code that names `DocumentJobSubmitStatus` must
use `DocumentJobStatus` and account for all documented job states. This removal
is a breaking source change even though accepted submissions still report
`Queued` when newly created. On an idempotent replay, `status` reports the
original job's current state and `replayed` indicates that the request returned
that existing job. The TypeScript SDK, Python SDK, C# SDK, Java SDK, and CLI all
use the coordinated source version `1.0.0` across all five families. These
artifacts are source outputs only; publication is a separate release action.

- Document sandbox key scope: only artifact and asynchronous job routes are available; job submission accepts `Extraction` without `templateId`, `Classification`, `ZeroShot`, `Crop` and `Split`. Sandbox jobs debit no credits or production quota; unsupported routes or operations return `403` with `environment.sandbox_route_unavailable`. Documentation only; no API behavior or SDK version change. XTRAK-2373. Main PR: [#54](https://github.com/cogneris-ai/cogneris-api-examples/pull/54).

- Replace `DocumentJobSubmitStatus` with `DocumentJobStatus` on job submission
  responses in the generated TypeScript, Python, C# and Java SDKs. The shared
  status type includes `Queued`, `Processing`, `Succeeded`, `Failed` and
  `Cancelled`; idempotent submit replay returns the original job's current
  status and reports `replayed`.
- `submit_document_job` takes an optional `idempotency_key`, sent as the
  `Idempotency-Key` header. Within the job's 7-day retention, a repeat with the
  same key and body returns the original job (`202`, `data.replayed: true`,
  `Idempotent-Replayed: true` header); the same key with a different body is
  rejected with `422`, and a repeat that arrives while the first request is
  still being accepted gets a retryable `409` (XTRAK-1830, #50).
- `DocumentJobSubmission` gains the required field `replayed`. Code that builds
  a `DocumentJobSubmission` itself, such as a test double, must now supply it
  (XTRAK-1830, #50).
- `submit_document_job` parses `400` and `409` as `ServiceErrorEnvelope`
  instead of `ProblemDetails`. Callers that inspected the `ProblemDetails` body
  of those statuses must read `ServiceErrorEnvelope` instead (XTRAK-1830, #50).
- The `cursor` argument of `list_templates` accepts `None`
  (`Union[None, Unset, str]`), a widening that existing calls do not notice
  (XTRAK-1830, #50).
- Set the TypeScript SDK, Python SDK, C# SDK, Java SDK and TypeScript CLI source
  versions to `1.0.0`. The CLI depends on the exact SDK version `1.0.0`.

## 0.2.0 (compatibility summary corrected)

Generated from OpenAPI contract `2026-09-28`. Its original compatibility summary was incomplete: it removed a public type
while carrying minor version `0.2.0`. The current coordinated source version is
`1.0.0`. Other generated changes included two nullable widenings. The field
`ProblemDetailsErrorsItem.field` is nullable (`Union[None, Unset, str]`) because
the service sends `null`, and `SubmitDocumentJobBody.template_id` is now
`Union[None, UUID, Unset]`.

Compatibility impact: **major**. `DocumentJobSubmitStatus` was removed and
`DocumentJobSubmission.status` now uses the broader `DocumentJobStatus` type.
Consumers that named the removed type must migrate and handle all documented job
states. New submissions still begin as `Queued`; an idempotent replay returns
the original job's current status and reports `replayed`.

- Add the `artifacts` API: `upload_artifact` (`POST /api/v1/artifacts`) stores a job's input document and returns an `ArtifactUploadEnvelope` whose `Artifact.reference` is the `artifact://` value `submit_job` takes; `download_artifact` (`GET /api/v1/artifacts/content`) reads back the bytes of an upload or of a finished job's `output_reference`. New models: `Artifact`, `ArtifactUploadEnvelope`, `UploadArtifactBody` (XTRAK-1742, #33).
- Add the `ExtractedField` model, which documents what each entry of `EnvelopeData.metadata` holds: `value`, `confidence` (0–100), and, when the value was located on the page, `page`, `bbox`, and `bbox_confidence` (0–100). `EnvelopeData.metadata` keeps its open `EnvelopeDataMetadata` type, whose entries still arrive in `additional_properties` exactly as before; `ExtractedField` and the docstrings describe them rather than retyping them (XTRAK-1744, #33).
- Type the fields the service already returned on `EnvelopeData`: `results` (`ClassificationResult`), `document_type`, `confidence`, `fraud_blocked`, `fraud_request_id`, `quality` (`QualityAssessment`, `QualityFinding`, `QualityVerdict`), `image_urls`, `documents` (`CropDocument`), `composite_image_url`, `request_id`, `extractions` (`FaceExtraction`) and `matches` (`FaceMatch`); add `credits_consumed` to `DocumentJob` (XTRAK-1798, #37).
- Every operation declares `400`, `401`, `403`, `404`, `409`, `429` and `500`, and the generated functions parse them as `ProblemDetails`, which gains `field` and `errors[].details`. Operations that already returned `ServiceErrorEnvelope` for an error status keep it (XTRAK-1798, #37).
- `SubmitDocumentJobBody` gains optional `template_id`, the finished template an `Extraction` job extracts with (XTRAK-1816, #37).
- `CognerisClient` reports an error status whose body is not JSON as `CognerisApiError` with its `status`, as 0.1.0 did, instead of `CognerisResponseError` (XTRAK-1798, #37).
- Docstrings now describe the per-field source-coordinate convention, the `artifact://` reference lifecycle, and `DocumentJob.output_reference` (XTRAK-1744, XTRAK-1742, #33).
- Add the `templates` API: `list_templates` (`GET /api/v1/templates`) lists the tenant's finished templates, with the models `Template`, `TemplateList`, `TemplateListEnvelope` and `TemplateStatus`. `DocumentJob` gains `template_id`, the template the job was submitted with (XTRAK-1830, #42).
- Add the `webhooks` API: `list_webhook_endpoints`, `create_webhook_endpoint`, `update_webhook_endpoint` and `delete_webhook_endpoint` (`/api/v1/webhook-endpoints`), with the `WebhookEndpoint*` models and the `WebhookEvent` enum (XTRAK-1830, #42).
- The generated `submit_document_job` parses a `422` as `ServiceErrorEnvelope`, the response for a `template_id` the platform refuses (`template_not_applicable`, `template_unknown`) (XTRAK-1830, #42; XTRAK-1859, #43).
- `upload_artifact` and the synchronous `/Document/*` operations (classify, crop, extract, facematch, split, zero-shot) parse `502`, `503` and `504` as `ServiceErrorEnvelope` (XTRAK-1859, #43).

## 0.1.0

- Add optional typed WhatsApp consent (`PortalMagicLinkRequest.opt_in`) and preserve `PortalMagicLink.send_suppression_reason`, including unknown future reasons. Existing requests can still omit consent (XTRAK-1651, #23).

- Initial generated client for the public Cogneris Document AI OpenAPI contract.
- Consume the `{data, meta, hasErrors}` response envelope on the async job endpoints: `submit_job`, `get_job`, `wait_for_job` and `cancel_job` unwrap `DocumentJobSubmissionEnvelope`, `DocumentJobEnvelope` and `DocumentJobCancellationEnvelope`; `cancel_job` returns `DocumentJobCancellation` (HTTP 202 with `jobId` and `cancellationRequested`) instead of `DocumentJob`; `SubmitDocumentJobResponse202` is removed (#14).
- Align the job contract with the producer: `submit_job` takes a `DocumentJobSubmitOperation` (adds `Facematch`) and an `artifact://` input reference, `ServiceResponseMeta` carries structured `ApiError` entries and `credits_consumed`, and cancelling a job that cannot be cancelled returns a typed `ServiceErrorEnvelope` on HTTP 409 (#15).
- Type the `meta` of the synchronous `/Document/*` `Envelope` as `ServiceResponseMeta`, the same producer metadata the job envelopes already carry, so `credits_consumed` and structured `errors` are typed fields on extraction, classification, zero-shot, crop, split and facematch responses instead of untyped `additional_properties`; `EnvelopeMeta` is removed (#20).
- License the package under Apache-2.0: `LICENSE` and `NOTICE` ship in the distribution and `pyproject.toml` declares the SPDX license metadata (#16).
