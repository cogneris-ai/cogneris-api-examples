import importlib.util
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cogneris_document_ai_sdk as sdk


ROOT = Path(os.environ["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"]).resolve()
EXAMPLE = ROOT / "examples" / "python" / "quickstart.py"
API_KEY = "xtkt_live_TEST_ONLY_NOT_A_SECRET-must-not-be-logged"
DOCUMENT_MARKER = "document-content-must-not-be-logged"
EXTRACTED_MARKER = "extracted-field-must-not-be-logged"
RESPONSE_MARKER = "raw-response-must-not-be-logged"
JOB_ID = "11111111-1111-4111-8111-111111111111"


class Handler(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_args):
        pass

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
                "meta": {"httpStatusCode": status, "messages": [], "errors": []},
                "hasErrors": False,
            },
            headers,
        )

    def _record(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.requests.append(
            {
                "authorization": self.headers.get("Authorization"),
                "body": body,
                "method": self.command,
                "path": self.path,
            }
        )
        return body

    def do_POST(self):
        body = self._record()
        if self.path == "/Document/extraction":
            if b"application-error-document" in body:
                self._json(
                    200,
                    {
                        "data": {"metadata": {"secretField": EXTRACTED_MARKER}},
                        "meta": {"httpStatusCode": 200, "messages": [RESPONSE_MARKER]},
                        "hasErrors": True,
                    },
                )
            elif b"error-document" in body:
                self._json(500, {"title": RESPONSE_MARKER, "detail": EXTRACTED_MARKER})
            else:
                self._json(
                    200,
                    {
                        "data": {"metadata": {"secretField": EXTRACTED_MARKER}},
                        "meta": {"httpStatusCode": 200},
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
                    "retryAfterSeconds": 0,
                },
                {"Retry-After": "0"},
            )
            return
        self._json(404, {"title": RESPONSE_MARKER})

    def do_GET(self):
        self._record()
        if self.path == f"/api/v1/document-jobs/{JOB_ID}":
            self._service_response(
                200,
                {
                    "jobId": JOB_ID,
                    "operation": "Extraction",
                    "status": "Succeeded",
                    "outputReference": RESPONSE_MARKER,
                },
            )
            return
        self._json(404, {"title": RESPONSE_MARKER})


class InstalledPythonExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(Path(sdk.__file__).resolve()).startswith(str(ROOT)):
            raise AssertionError(f"SDK resolved from source tree: {sdk.__file__}")
        spec = importlib.util.spec_from_file_location("cogneris_quickstart", EXAMPLE)
        cls.example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.example)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.temporary = tempfile.TemporaryDirectory(prefix="cogneris-python-example-input-")
        cls.file_path = Path(cls.temporary.name) / "sample.pdf"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temporary.cleanup()

    def invoke(self, arguments, contents=DOCUMENT_MARKER):
        self.file_path.write_text(contents)
        stdout = io.StringIO()
        stderr = io.StringIO()
        regions = []

        def create_client(**options):
            regions.append(options["region"])
            return sdk.CognerisClient(**options, _base_url_for_testing=self.base_url)

        resolved_arguments = [str(self.file_path) if value == "$FILE" else value for value in arguments]
        exit_code = self.example._run_example_for_testing(
            arguments=resolved_arguments,
            environment={"COGNERIS_API_KEY": API_KEY, "COGNERIS_REGION": "eu"},
            stdout=stdout,
            stderr=stderr,
            _create_client_for_testing=create_client,
        )
        return exit_code, regions, stdout.getvalue(), stderr.getvalue()

    def test_sync_upload_emits_only_a_safe_summary(self):
        Handler.requests = []
        exit_code, regions, stdout, stderr = self.invoke(["extract", "$FILE"])
        self.assertEqual(exit_code, 0, stderr)
        self.assertEqual(regions, ["eu"])
        self.assertEqual(
            json.loads(stdout),
            {"operation": "extraction", "hasErrors": False, "httpStatusCode": 200},
        )
        self.assertEqual(stderr, "")
        self.assertEqual(Handler.requests[-1]["authorization"], f"Bearer {API_KEY}")
        self.assertIn(DOCUMENT_MARKER.encode(), Handler.requests[-1]["body"])
        for sensitive in (API_KEY, DOCUMENT_MARKER, EXTRACTED_MARKER, RESPONSE_MARKER):
            self.assertNotIn(sensitive, stdout + stderr)

    def test_async_submission_and_polling_omit_output_reference(self):
        Handler.requests = []
        input_reference = "private/input/reference.pdf"
        exit_code, _, stdout, stderr = self.invoke(["async", "Extraction", input_reference])
        self.assertEqual(exit_code, 0, stderr)
        self.assertEqual(
            json.loads(stdout),
            {"operation": "Extraction", "jobId": JOB_ID, "status": "Succeeded"},
        )
        self.assertEqual(stderr, "")
        submission = next(
            request for request in Handler.requests
            if request["method"] == "POST" and request["path"] == "/api/v1/document-jobs"
        )
        self.assertEqual(
            json.loads(submission["body"]),
            {"operation": "Extraction", "inputReference": input_reference},
        )
        self.assertNotIn(RESPONSE_MARKER, stdout)
        self.assertNotIn(input_reference, stdout)

    def test_controlled_error_omits_raw_response_and_credentials(self):
        exit_code, _, stdout, stderr = self.invoke(["extract", "$FILE"], "error-document")
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Cogneris API request failed with HTTP 500.\n")
        for sensitive in (API_KEY, EXTRACTED_MARKER, RESPONSE_MARKER):
            self.assertNotIn(sensitive, stderr)

    def test_application_error_envelope_is_a_safe_failure(self):
        exit_code, _, stdout, stderr = self.invoke(
            ["extract", "$FILE"], "application-error-document"
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Cogneris extraction reported an application error.\n")
        for sensitive in (API_KEY, EXTRACTED_MARKER, RESPONSE_MARKER):
            self.assertNotIn(sensitive, stderr)

    def test_documented_invocation_has_no_public_base_url_input(self):
        source = EXAMPLE.read_text()
        self.assertNotIn("COGNERIS_BASE_URL", source)
        self.assertNotIn("--base-url", source)


if __name__ == "__main__":
    unittest.main()
