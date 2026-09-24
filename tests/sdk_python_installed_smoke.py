import json
import math
import os
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cogneris_document_ai_sdk as sdk


JOB_ID = "11111111-1111-4111-8111-111111111111"
FAILED_JOB_ID = "22222222-2222-4222-8222-222222222222"
ENDLESS_JOB_ID = "33333333-3333-4333-8333-333333333333"
RETRY_JOB_ID = "44444444-4444-4444-8444-444444444444"
PARSE_JOB_ID = "55555555-5555-4555-8555-555555555555"
TRANSPORT_JOB_ID = "66666666-6666-4666-8666-666666666666"
NAN_HINT_JOB_ID = "77777777-7777-4777-8777-777777777777"
INFINITY_HINT_JOB_ID = "88888888-8888-4888-8888-888888888888"
HTML_429_JOB_ID = "99999999-9999-4999-8999-999999999999"
EMPTY_401_JOB_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
REFLECTED_API_KEY = "xtkt_live_TEST_ONLY_NOT_A_SECRET-reflected-sentinel"
REFLECTED_DOCUMENT = "document-reflected-sentinel"


def error_exposure(error):
    return f"{error!s} {error.args!r} {vars(error)!r}"


class _Handler(BaseHTTPRequestHandler):
    requests = []
    polling_counts = {}

    def log_message(self, _format, *_args):
        pass

    def _body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", "0")))

    def _json(self, status, body, headers=None):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _service_response(self, status, data, headers=None):
        self._json(
            status,
            {
                "data": data,
                "meta": {"httpStatusCode": status, "messages": []},
                "hasErrors": False,
            },
            headers,
        )

    def _record(self, body):
        self.requests.append(
            {
                "authorization": self.headers.get("Authorization"),
                "body": body,
                "content_type": self.headers.get("Content-Type"),
                "method": self.command,
                "path": self.path,
                "received_at": time.monotonic(),
            }
        )

    def do_POST(self):
        body = self._body()
        self._record(body)
        if self.path == "/Document/extraction":
            if REFLECTED_DOCUMENT.encode() in body:
                self._json(
                    415,
                    {
                        "code": REFLECTED_API_KEY,
                        "title": REFLECTED_DOCUMENT,
                        "retryable": True,
                    },
                )
            else:
                self._json(
                    200,
                    {
                        "data": {"accepted": True},
                        "meta": {
                            "httpStatusCode": 200,
                            "messages": [],
                            "errors": [
                                {
                                    "code": "ocr.low_confidence",
                                    "message": "page 2 was read at 0.41 confidence",
                                    "field": None,
                                    "retryable": False,
                                }
                            ],
                            "creditsConsumed": 14.5,
                        },
                        "hasErrors": False,
                    },
                )
            return
        if self.path == "/api/v1/document-jobs":
            self._service_response(
                202,
                {
                    "jobId": JOB_ID,
                    "status": "Queued",
                    "statusUrl": f"/api/v1/document-jobs/{JOB_ID}",
                    "retryAfterSeconds": 1,
                },
                {"Location": f"/api/v1/document-jobs/{JOB_ID}", "Retry-After": "1"},
            )
            return
        if self.path == f"/api/v1/document-jobs/{JOB_ID}/cancel":
            self._service_response(
                202, {"jobId": JOB_ID, "cancellationRequested": True}
            )
            return
        self._json(404, {"code": "not_found", "title": "Not found"})

    def do_GET(self):
        self._record(b"")
        if not self.path.startswith("/api/v1/document-jobs/"):
            self._json(404, {"code": "not_found", "title": "Not found"})
            return
        job_id = self.path.rsplit("/", 1)[-1]
        count = self.polling_counts.get(job_id, 0) + 1
        self.polling_counts[job_id] = count
        if job_id == TRANSPORT_JOB_ID:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if job_id in (HTML_429_JOB_ID, EMPTY_401_JOB_ID):
            raw = f"<html>{REFLECTED_API_KEY}</html>".encode() if job_id == HTML_429_JOB_ID else b""
            self.send_response(429 if job_id == HTML_429_JOB_ID else 401)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if job_id == PARSE_JOB_ID:
            raw = f"not-json {REFLECTED_API_KEY} {REFLECTED_DOCUMENT}".encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if job_id == FAILED_JOB_ID:
            self._service_response(
                200,
                {
                    "jobId": job_id,
                    "operation": "Extraction",
                    "status": "Failed",
                    "failureCode": REFLECTED_DOCUMENT,
                    "outputReference": REFLECTED_API_KEY,
                    "retryable": False,
                },
            )
            return
        if job_id == ENDLESS_JOB_ID:
            self._service_response(
                200,
                {"jobId": job_id, "operation": "Extraction", "status": "Processing"},
                {"Retry-After": "0"},
            )
            return
        if job_id in {NAN_HINT_JOB_ID, INFINITY_HINT_JOB_ID}:
            if count == 1:
                hint = "NaN" if job_id == NAN_HINT_JOB_ID else "Infinity"
                self._service_response(
                    200,
                    {
                        "jobId": job_id,
                        "operation": "Extraction",
                        "status": "Processing",
                    },
                    {"Retry-After": hint},
                )
            else:
                self._service_response(
                    200,
                    {"jobId": job_id, "operation": "Extraction", "status": "Succeeded"},
                )
            return
        if job_id == RETRY_JOB_ID and count == 1:
            self._service_response(
                200,
                {"jobId": job_id, "operation": "Extraction", "status": "Processing"},
                {"Retry-After": "1"},
            )
            return
        if job_id == JOB_ID and count == 1:
            self._service_response(
                200,
                {"jobId": job_id, "operation": "Extraction", "status": "Processing"},
                {"Retry-After": "0"},
            )
            return
        self._service_response(
            200,
            {
                "jobId": job_id,
                "operation": "Extraction",
                "status": "Succeeded",
                "outputReference": "result/ref",
            },
        )


class InstalledPythonSdkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        _Handler.requests = []
        _Handler.polling_counts = {}

    def client(self, api_key="xtkt_live_TEST_ONLY_NOT_A_SECRET", region="us"):
        return sdk.CognerisClient(
            api_key=api_key,
            region=region,
            _base_url_for_testing=self.base_url,
        )

    def test_module_resolves_from_site_packages(self):
        module_path = Path(sdk.__file__).resolve()
        source_root = Path(os.environ["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"]).resolve()
        self.assertIn("site-packages", module_path.parts)
        self.assertFalse(module_path.is_relative_to(source_root), module_path)
        self.assertEqual(sdk.cogneris_base_url("us"), "https://api-us.cogneris.ai")
        self.assertEqual(sdk.cogneris_base_url("eu"), "https://api-eu.cogneris.ai")
        with self.assertRaisesRegex(ValueError, "us.*eu"):
            sdk.CognerisClient(
                api_key="xtkt_live_TEST_ONLY_NOT_A_SECRET",
                region="apac",
                _base_url_for_testing=self.base_url,
            )

    def test_reflected_server_content_is_not_retained(self):
        client = self.client(api_key=REFLECTED_API_KEY)
        with self.assertRaises(sdk.CognerisApiError) as api_failure:
            client.extract(REFLECTED_DOCUMENT.encode(), file_name="bad.exe")
        self.assertEqual(api_failure.exception.status, 415)
        self.assertTrue(api_failure.exception.retryable)
        self.assertFalse(hasattr(api_failure.exception, "code"))
        exposed = error_exposure(api_failure.exception)
        self.assertNotIn(REFLECTED_API_KEY, exposed)
        self.assertNotIn(REFLECTED_DOCUMENT, exposed)

        with self.assertRaises(sdk.CognerisJobTerminalError) as terminal:
            client.wait_for_job(FAILED_JOB_ID, max_attempts=1)
        self.assertEqual(terminal.exception.status, "Failed")
        self.assertFalse(terminal.exception.retryable)
        self.assertFalse(hasattr(terminal.exception, "job"))
        self.assertFalse(hasattr(terminal.exception, "failure_code"))
        exposed = error_exposure(terminal.exception)
        self.assertNotIn(REFLECTED_API_KEY, exposed)
        self.assertNotIn(REFLECTED_DOCUMENT, exposed)

    def test_submit_hint_delays_first_poll(self):
        client = self.client()
        submission = client.submit_job("Facematch", "artifact://input/ref")
        submitted = _Handler.requests[-1]
        job = client.wait_for_job(
            submission.job_id, max_attempts=3, poll_interval_seconds=0
        )
        self.assertEqual(job.status.value, "Succeeded")
        first_poll = next(
            request
            for request in _Handler.requests
            if request["method"] == "GET" and request["path"].endswith(JOB_ID)
        )
        self.assertGreaterEqual(
            first_poll["received_at"] - submitted["received_at"], 0.9
        )

    def test_transport_and_parse_failures_are_safe_typed_errors(self):
        client = self.client(api_key=REFLECTED_API_KEY)
        for job_id, error_type in [
            (TRANSPORT_JOB_ID, sdk.CognerisTransportError),
            (PARSE_JOB_ID, sdk.CognerisResponseError),
        ]:
            with self.subTest(job_id=job_id):
                with self.assertRaises(error_type) as caught:
                    client.get_job(job_id)
                exposed = error_exposure(caught.exception)
                self.assertNotIn(REFLECTED_API_KEY, exposed)
                self.assertNotIn(REFLECTED_DOCUMENT, exposed)
                self.assertIsNone(caught.exception.__cause__)
                self.assertIsNone(caught.exception.__context__)
                self.assertFalse(hasattr(caught.exception, "request"))
                self.assertFalse(hasattr(caught.exception, "response"))

    def test_error_status_without_a_json_body_keeps_its_status(self):
        # The contract declares a problem document on every error status, but an edge
        # proxy can answer with HTML or nothing; that is still an API error, not a
        # contract mismatch.
        client = self.client(api_key=REFLECTED_API_KEY)
        for job_id, status in [(HTML_429_JOB_ID, 429), (EMPTY_401_JOB_ID, 401)]:
            with self.subTest(status=status):
                with self.assertRaises(sdk.CognerisApiError) as caught:
                    client.get_job(job_id)
                self.assertEqual(caught.exception.status, status)
                self.assertIsNone(caught.exception.retryable)
                self.assertNotIn(REFLECTED_API_KEY, error_exposure(caught.exception))
                self.assertIsNone(caught.exception.__cause__)
                self.assertIsNone(caught.exception.__context__)

    def test_poll_intervals_handle_non_finite_values_safely(self):
        client = self.client()
        for interval in [math.nan, math.inf, -math.inf]:
            with self.subTest(interval=interval):
                with self.assertRaisesRegex(ValueError, "finite"):
                    client.wait_for_job(
                        ENDLESS_JOB_ID, max_attempts=2, poll_interval_seconds=interval
                    )
        for job_id in [NAN_HINT_JOB_ID, INFINITY_HINT_JOB_ID]:
            with self.subTest(job_id=job_id):
                job = client.wait_for_job(
                    job_id, max_attempts=2, poll_interval_seconds=0
                )
                self.assertEqual(job.status.value, "Succeeded")

    def test_portal_consent_and_suppression_round_trip(self):
        from cogneris_document_ai_sdk.models import PortalMagicLink, PortalMagicLinkRequest

        # Public DTO + controller mapping in api-be (cb6629d), no service envelope.
        payload = {"formId": 42, "name": "Test Recipient", "sendChannel": "whatsapp",
                   "phone": "+15555550100", "optIn": {
                       "source": "web_form", "evidenceText": "consent-form-42",
                       "evidenceUrl": "https://example.test/consents/42",
                       "collectedWhen": "2026-09-17T12:00:00Z"}}
        request = PortalMagicLinkRequest.from_dict(payload)
        self.assertTrue(hasattr(request, "opt_in"), "consent must be a typed SDK field")
        self.assertEqual(request.opt_in.evidence_text, "consent-form-42")
        serialized = request.to_dict()["optIn"]
        self.assertEqual(serialized["source"], "web_form")
        self.assertEqual(serialized["evidenceUrl"], "https://example.test/consents/42")
        self.assertEqual(serialized["collectedWhen"], "2026-09-17T12:00:00+00:00")
        self.assertNotIn("optIn", PortalMagicLinkRequest(form_id=42, name="Test").to_dict())
        self.assertIsNone(PortalMagicLinkRequest.from_dict({**payload, "optIn": None}).to_dict()["optIn"])
        for reason in ("whatsapp_no_optin", "whatsapp_optin_revoked", "whatsapp_blocked",
                       "provider_error", "future_reason", None):
            response = PortalMagicLink.from_dict({"id": 90210, "url": None, "sent": False,
                "sendChannel": "whatsapp", "sendSuppressionReason": reason})
            self.assertEqual(response.send_suppression_reason, reason)
            self.assertEqual(response.to_dict()["sendSuppressionReason"], reason)
        self.assertNotIn("sendSuppressionReason", PortalMagicLink.from_dict({"id": 90210}).to_dict())

    def test_public_flows_and_bounded_polling(self):
        client = self.client(region="eu")
        extracted = client.extract(b"ordinary-document", file_name="sample.pdf")
        self.assertTrue(extracted.data.to_dict()["accepted"])
        # XTRAK-1687: /Document/* meta carries the credit charge and structured
        # errors as typed fields, exactly like the job envelopes.
        self.assertEqual(extracted.meta.http_status_code, 200)
        self.assertEqual(extracted.meta.credits_consumed, 14.5)
        self.assertEqual(
            [error.code for error in extracted.meta.errors], ["ocr.low_confidence"]
        )
        upload = _Handler.requests[-1]
        self.assertEqual(upload["authorization"], "Bearer xtkt_live_TEST_ONLY_NOT_A_SECRET")
        self.assertRegex(upload["content_type"], r"^multipart/form-data; boundary=")
        self.assertIn(b"ordinary-document", upload["body"])
        self.assertIn(b"sample.pdf", upload["body"])

        started = time.monotonic()
        job = client.wait_for_job(RETRY_JOB_ID, max_attempts=2, poll_interval_seconds=0)
        self.assertEqual(job.status.value, "Succeeded")
        self.assertGreaterEqual(time.monotonic() - started, 0.9)

        cancelled = client.cancel_job(JOB_ID)
        self.assertEqual(str(cancelled.job_id), JOB_ID)
        self.assertTrue(cancelled.cancellation_requested)
        with self.assertRaises(sdk.CognerisMaxAttemptsError) as exhausted:
            client.wait_for_job(ENDLESS_JOB_ID, max_attempts=2, poll_interval_seconds=0)
        self.assertEqual(exhausted.exception.attempts, 2)
        self.assertEqual(_Handler.polling_counts[ENDLESS_JOB_ID], 2)


if __name__ == "__main__":
    unittest.main()
