# Changelog

## 0.2.0

Generated from OpenAPI contract `2026-09-24` (was `2026-08-07`). Compatibility: additive, with one nullable widening. No operation, model, or field from 0.1.0 was removed or renamed. `ProblemDetailsErrorsItem.field` is now `Union[None, Unset, str]`, because the service sends `null` there.

- Add the `artifacts` API: `upload_artifact` (`POST /api/v1/artifacts`) stores a job's input document and returns an `ArtifactUploadEnvelope` whose `Artifact.reference` is the `artifact://` value `submit_job` takes; `download_artifact` (`GET /api/v1/artifacts/content`) reads back the bytes of an upload or of a finished job's `output_reference`. New models: `Artifact`, `ArtifactUploadEnvelope`, `UploadArtifactBody` (XTRAK-1742).
- Add the `ExtractedField` model, which documents what each entry of `EnvelopeData.metadata` holds: `value`, `confidence` (0–100), and, when the value was located on the page, `page`, `bbox`, and `bbox_confidence` (0–100). `EnvelopeData.metadata` keeps its open `EnvelopeDataMetadata` type, whose entries still arrive in `additional_properties` exactly as before; `ExtractedField` and the docstrings describe them rather than retyping them (XTRAK-1744).
- Type the fields the service already returned on `EnvelopeData`: `results` (`ClassificationResult`), `document_type`, `confidence`, `fraud_blocked`, `fraud_request_id`, `quality` (`QualityAssessment`, `QualityFinding`, `QualityVerdict`), `image_urls`, `documents` (`CropDocument`), `composite_image_url`, `request_id`, `extractions` (`FaceExtraction`) and `matches` (`FaceMatch`); add `credits_consumed` to `DocumentJob` (XTRAK-1798).
- Every operation declares `400`, `401`, `403`, `404`, `409`, `429` and `500`, and the generated functions parse them as `ProblemDetails`, which gains `field` and `errors[].details`. Operations that already returned `ServiceErrorEnvelope` for an error status keep it (XTRAK-1798).
- `SubmitDocumentJobBody` gains optional `template_id`, the finished template an `Extraction` job extracts with (XTRAK-1816).
- `CognerisClient` reports an error status whose body is not JSON as `CognerisApiError` with its `status`, as 0.1.0 did, instead of `CognerisResponseError` (XTRAK-1798).
- Docstrings now describe the per-field source-coordinate convention, the `artifact://` reference lifecycle, and `DocumentJob.output_reference` (XTRAK-1744, XTRAK-1742).

## 0.1.0

- Add optional typed WhatsApp consent (`PortalMagicLinkRequest.opt_in`) and preserve `PortalMagicLink.send_suppression_reason`, including unknown future reasons. Existing requests can still omit consent (XTRAK-1651).

- Initial generated client for the public Cogneris Document AI OpenAPI contract.
- Consume the `{data, meta, hasErrors}` response envelope on the async job endpoints: `submit_job`, `get_job`, `wait_for_job` and `cancel_job` unwrap `DocumentJobSubmissionEnvelope`, `DocumentJobEnvelope` and `DocumentJobCancellationEnvelope`; `cancel_job` returns `DocumentJobCancellation` (HTTP 202 with `jobId` and `cancellationRequested`) instead of `DocumentJob`; `SubmitDocumentJobResponse202` is removed (#14).
- Align the job contract with the producer: `submit_job` takes a `DocumentJobSubmitOperation` (adds `Facematch`) and an `artifact://` input reference, `ServiceResponseMeta` carries structured `ApiError` entries and `credits_consumed`, and cancelling a job that cannot be cancelled returns a typed `ServiceErrorEnvelope` on HTTP 409 (#15).
- Type the `meta` of the synchronous `/Document/*` `Envelope` as `ServiceResponseMeta`, the same producer metadata the job envelopes already carry, so `credits_consumed` and structured `errors` are typed fields on extraction, classification, zero-shot, crop, split and facematch responses instead of untyped `additional_properties`; `EnvelopeMeta` is removed (#20).
- License the package under Apache-2.0: `LICENSE` and `NOTICE` ship in the distribution and `pyproject.toml` declares the SPDX license metadata (#16).
