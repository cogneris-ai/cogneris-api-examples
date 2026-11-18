# Raw HTTP examples — classification, extraction, status and webhooks

These examples call the published HTTP contract without a Cogneris SDK. They have only been exercised against a local synthetic HTTP server; DEV execution and the end-to-end ticket acceptance remain unverified.

Prerequisites: Python with `requests` 2.32.5, or .NET 8 or later; a PDF; and an authorized API key. Set `COGNERIS_API_KEY` as an environment variable. Optionally set `COGNERIS_API_BASE` to the API base for the key's tenant and region (for example the DEV host when using a DEV key). The default is `https://api-eu.cogneris.ai`. Do not commit keys. Responses can contain document data: use synthetic documents and protect terminal output.

Synchronous classification accepts a production key. It sends a PDF as multipart `files`:

```sh
python examples/http-classify/python/classify.py synthetic.pdf
dotnet run --project examples/http-classify/dotnet -- synthetic.pdf
```

Schema-backed asynchronous extraction requires a production key and the UUID of a finished template belonging to the tenant. It uploads an artifact, then submits an Extraction job with `templateId`; the program prints the job response:

```sh
python examples/http-extract/python/extract.py synthetic.pdf TEMPLATE_UUID
dotnet run --project examples/http-extract/dotnet -- synthetic.pdf TEMPLATE_UUID
```

Each new invocation creates a new idempotency key. If adding retries to a real integration, persist and reuse the same key and request body for that logical job; do not repeat an invocation blindly after an ambiguous network failure.

Read a job's current status and, when it has succeeded and provides an output reference, fetch its result:

```sh
python examples/http-status/python/status.py JOB_UUID
dotnet run --project examples/http-status/dotnet -- JOB_UUID
```

The local webhook receivers demonstrate job notification signature verification. Set `COGNERIS_WEBHOOK_SECRET` to the **text** of the secret returned at endpoint registration, and optionally `WEBHOOK_PORT` (default 8080):

```sh
python examples/http-webhook/python/receiver.py
dotnet run --project examples/http-webhook/dotnet
```

They bind only to `127.0.0.1`, verify `X-Xtrakt-Signature` over timestamp and raw bytes, enforce a five-minute window, and acknowledge duplicate `X-Xtrakt-Delivery` IDs. They do not register an endpoint, fetch results, or process payloads. The in-memory set is not durable and is only illustrative: production requires HTTPS ingress, a bounded request body, a durable atomic deduplication store and reliable processing. Job notification webhooks are a separate contract from platform event webhooks. A production key with `webhooks.manage` is required to register job endpoints; sandbox jobs do not deliver them.

Hermetic tests (no API credentials or external requests):

```sh
python -m unittest tests.test_http_classify_examples tests.test_http_extract_examples tests.test_http_status_examples tests.test_http_webhook_examples -v
```

The tests use a synthetic key and localhost only. They do not prove behavior in DEV, which needs an authorized test tenant, key, finished template and synthetic PDF.
