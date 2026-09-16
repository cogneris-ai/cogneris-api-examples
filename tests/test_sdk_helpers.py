import importlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK = ROOT / "sdks" / "python"
JOB_ID = "11111111-1111-4111-8111-111111111111"
FAILED_JOB_ID = "22222222-2222-4222-8222-222222222222"
ENDLESS_JOB_ID = "33333333-3333-4333-8333-333333333333"

sys.path.insert(0, str(PYTHON_SDK))
try:
    sdk = importlib.import_module("cogneris_document_ai_sdk")
except ImportError:
    sdk = None


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

    def _record(self, body):
        self.requests.append(
            {
                "authorization": self.headers.get("Authorization"),
                "body": body,
                "content_type": self.headers.get("Content-Type"),
                "method": self.command,
                "path": self.path,
            }
        )

    def do_POST(self):
        body = self._body()
        self._record(body)
        if self.path == "/Document/extraction":
            if b"reject-this-document" in body:
                self._json(
                    415,
                    {"code": "unsupported_media_type", "title": "Unsupported document"},
                )
            else:
                self._json(
                    200,
                    {
                        "data": {"accepted": True},
                        "meta": {"status": 200},
                        "hasErrors": False,
                    },
                )
            return
        if self.path == "/api/v1/document-jobs":
            self._json(
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
            self._json(
                200, {"jobId": JOB_ID, "operation": "Extraction", "status": "Cancelled"}
            )
            return
        self._json(404, {"code": "not_found", "title": "Not found"})

    def do_GET(self):
        self._record(b"")
        if self.path.startswith("/api/v1/document-jobs/"):
            job_id = self.path.rsplit("/", 1)[-1]
            count = self.polling_counts.get(job_id, 0) + 1
            self.polling_counts[job_id] = count
            if job_id == FAILED_JOB_ID:
                self._json(
                    200,
                    {
                        "jobId": job_id,
                        "operation": "Extraction",
                        "status": "Failed",
                        "failureCode": "processing_failed",
                        "retryable": False,
                    },
                )
            elif job_id == ENDLESS_JOB_ID:
                self._json(
                    200,
                    {
                        "jobId": job_id,
                        "operation": "Extraction",
                        "status": "Processing",
                    },
                    {"Retry-After": "0"},
                )
            elif count == 1:
                self._json(
                    200,
                    {
                        "jobId": job_id,
                        "operation": "Extraction",
                        "status": "Processing",
                    },
                    {"Retry-After": "1"},
                )
            else:
                self._json(
                    200,
                    {
                        "jobId": job_id,
                        "operation": "Extraction",
                        "status": "Succeeded",
                        "outputReference": "result/ref",
                    },
                )
            return
        self._json(404, {"code": "not_found", "title": "Not found"})


class PythonSdkHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)

    def setUp(self):
        _Handler.requests = []
        _Handler.polling_counts = {}

    def client(self, region="us"):
        return sdk.CognerisClient(
            api_key="test-api-key",
            region=region,
            _base_url_for_testing=self.base_url,
        )

    def test_installed_module_exports_region_and_typed_error_helpers(self):
        self.assertIsNotNone(sdk, "installed package must be importable")
        self.assertTrue(
            hasattr(sdk, "CognerisClient"),
            "installed package must export CognerisClient",
        )
        self.assertEqual(
            sdk.COGNERIS_REGION_URLS,
            {"us": "https://api-us.cogneris.ai", "eu": "https://api-eu.cogneris.ai"},
        )
        self.assertTrue(issubclass(sdk.CognerisError, Exception))
        self.assertTrue(issubclass(sdk.CognerisApiError, sdk.CognerisError))
        self.assertTrue(issubclass(sdk.CognerisJobTerminalError, sdk.CognerisError))
        self.assertTrue(issubclass(sdk.CognerisMaxAttemptsError, sdk.CognerisError))
        self.assertTrue(hasattr(sdk, "cogneris_base_url"))
        self.assertEqual(sdk.cogneris_base_url("us"), "https://api-us.cogneris.ai")
        self.assertEqual(sdk.cogneris_base_url("eu"), "https://api-eu.cogneris.ai")
        with self.assertRaisesRegex(ValueError, "us.*eu"):
            sdk.cogneris_base_url("apac")

    def test_extract_sends_bearer_multipart_without_leaking_bytes_in_errors(self):
        result = self.client().extract(b"ordinary-document", file_name="sample.pdf")
        self.assertTrue(result.data.to_dict()["accepted"])
        upload = _Handler.requests[-1]
        self.assertEqual(upload["authorization"], "Bearer test-api-key")
        self.assertRegex(upload["content_type"], r"^multipart/form-data; boundary=")
        self.assertIn(b"ordinary-document", upload["body"])
        self.assertIn(b"sample.pdf", upload["body"])

        with self.assertRaises(sdk.CognerisApiError) as caught:
            self.client().extract(b"reject-this-document", file_name="bad.exe")
        self.assertEqual(caught.exception.status, 415)
        self.assertEqual(caught.exception.code, "unsupported_media_type")
        self.assertNotIn("reject-this-document", str(caught.exception))
        self.assertNotIn("test-api-key", str(caught.exception))

    def test_job_helpers_submit_honor_retry_after_stop_and_cancel(self):
        client = self.client(region="eu")
        submission = client.submit_job("Extraction", "input/ref")
        self.assertEqual(submission.job_id, UUID(JOB_ID))
        submitted = json.loads(_Handler.requests[-1]["body"])
        self.assertEqual(
            submitted, {"operation": "Extraction", "inputReference": "input/ref"}
        )

        started = time.monotonic()
        job = client.wait_for_job(JOB_ID, max_attempts=3)
        self.assertEqual(job.status.value, "Succeeded")
        self.assertEqual(_Handler.polling_counts[JOB_ID], 2)
        self.assertGreaterEqual(time.monotonic() - started, 0.9)

        cancelled = client.cancel_job(JOB_ID)
        self.assertEqual(cancelled.status.value, "Cancelled")
        self.assertTrue(
            all(
                request["authorization"] == "Bearer test-api-key"
                for request in _Handler.requests
            )
        )

    def test_wait_surfaces_terminal_failure_and_bounded_attempt_exhaustion(self):
        client = self.client()
        with self.assertRaises(sdk.CognerisJobTerminalError) as failed:
            client.wait_for_job(FAILED_JOB_ID, max_attempts=3)
        self.assertEqual(failed.exception.job.status.value, "Failed")
        self.assertEqual(failed.exception.failure_code, "processing_failed")

        with self.assertRaises(sdk.CognerisMaxAttemptsError) as exhausted:
            client.wait_for_job(ENDLESS_JOB_ID, max_attempts=2)
        self.assertEqual(exhausted.exception.attempts, 2)
        self.assertEqual(_Handler.polling_counts[ENDLESS_JOB_ID], 2)

    def test_built_wheel_installs_and_exports_helpers_in_a_clean_environment(self):
        with tempfile.TemporaryDirectory(
            prefix="cogneris-python-sdk-smoke-"
        ) as temporary:
            output = Path(temporary) / "dist"
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(output)],
                cwd=PYTHON_SDK,
                check=True,
                capture_output=True,
                text=True,
            )
            wheel = next(output.glob("*.whl"))
            environment = Path(temporary) / "venv"
            subprocess.run(
                ["uv", "venv", "--python", sys.executable, str(environment)],
                check=True,
                capture_output=True,
                text=True,
            )
            python = environment / "bin" / "python"
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python), str(wheel)],
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [
                    str(python),
                    "-c",
                    "import cogneris_document_ai_sdk as s; "
                    "assert s.COGNERIS_REGION_URLS['eu'] == 'https://api-eu.cogneris.ai'; "
                    "assert s.CognerisClient",
                ],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
                env={
                    key: value
                    for key, value in os.environ.items()
                    if key != "PYTHONPATH"
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)


class TypeScriptSdkSmokeTests(unittest.TestCase):
    def test_packed_typescript_sdk_against_loopback(self):
        result = subprocess.run(
            ["node", "--test", str(ROOT / "tests" / "sdk_typescript_smoke.mjs")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
