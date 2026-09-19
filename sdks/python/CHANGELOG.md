# Changelog

## 0.1.0

- Initial generated client for the public Cogneris Document AI OpenAPI contract.
- Consume the `{data, meta, hasErrors}` response envelope on the async job endpoints: `submit_job`, `get_job`, `wait_for_job` and `cancel_job` unwrap `DocumentJobSubmissionEnvelope`, `DocumentJobEnvelope` and `DocumentJobCancellationEnvelope`; `cancel_job` returns `DocumentJobCancellation` (HTTP 202 with `jobId` and `cancellationRequested`) instead of `DocumentJob`; `SubmitDocumentJobResponse202` is removed (#14).
- Align the job contract with the producer: `submit_job` takes a `DocumentJobSubmitOperation` (adds `Facematch`) and an `artifact://` input reference, `ServiceResponseMeta` carries structured `ApiError` entries and `credits_consumed`, and cancelling a job that cannot be cancelled returns a typed `ServiceErrorEnvelope` on HTTP 409 (#15).
- Type the `meta` of the synchronous `/Document/*` `Envelope` as `ServiceResponseMeta`, the same producer metadata the job envelopes already carry, so `credits_consumed` and structured `errors` are typed fields on extraction, classification, zero-shot, crop, split and facematch responses instead of untyped `additional_properties`; `EnvelopeMeta` is removed (#20).
- License the package under Apache-2.0: `LICENSE` and `NOTICE` ship in the distribution and `pyproject.toml` declares the SPDX license metadata (#16).
