from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "postman" / "Cogneris-API.postman_collection.json"
SECRET_RE = re.compile(r"xtkt_live_[A-Za-z0-9_-]{8,}")


def requests(items: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for item in items:
        if "request" in item:
            yield item["request"]
        yield from requests(item.get("item", []))


def is_required(field: dict[str, Any]) -> bool:
    """
    openapi-to-postmanv2 marks required body properties by prefixing their
    description with "(Required)". The converter version is pinned exactly, and
    test_required_form_fields_are_selected fails loudly if that ever changes.
    """
    description = field.get("description") or {}
    if isinstance(description, dict):
        description = description.get("content", "")
    return str(description).startswith("(Required)")


class PublishedArtifactTests(unittest.TestCase):
    def test_postman_collection_is_published(self):
        self.assertTrue(COLLECTION.is_file(), f"missing {COLLECTION.relative_to(ROOT)}")

    def test_generation_is_reproducible(self):
        original = COLLECTION.read_bytes()
        try:
            subprocess.run(["npm", "run", "generate"], cwd=ROOT, check=True)
            first = COLLECTION.read_bytes()
            subprocess.run(["npm", "run", "generate"], cwd=ROOT, check=True)
            second = COLLECTION.read_bytes()
        finally:
            COLLECTION.write_bytes(original)

        self.assertEqual(original, first, "published collection is stale")
        self.assertEqual(first, second, "same OpenAPI input generated different collections")

    def test_live_smoke_refuses_to_run_without_a_live_key(self):
        result = subprocess.run(
            ["npm", "run", "smoke:live", "--", "--file", str(COLLECTION)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("COGNERIS_KEY must start with xtkt_live_", result.stderr)

    def run_smoke_against(self, status: int, payload: bytes):
        """Run the live smoke against a stub returning the given response."""

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt") as document:
                document.write(b"xtrak-954 smoke document")
                document.flush()
                environment = os.environ.copy()
                environment["COGNERIS_KEY"] = "xtkt_" + "live_test_only_not_a_secret"
                return subprocess.run(
                    [
                        "npm",
                        "run",
                        "smoke:live",
                        "--",
                        "--file",
                        document.name,
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}",
                    ],
                    cwd=ROOT,
                    env=environment,
                    text=True,
                    capture_output=True,
                )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_live_smoke_fails_on_an_error_envelope_returned_with_http_200(self):
        """
        The API answers in a ServiceResponse envelope, so a refused extraction
        can still arrive as HTTP 200 with hasErrors set. Treating status alone
        as the verdict would report a passing acceptance run for a call that
        extracted nothing.
        """
        result = self.run_smoke_against(
            200, b'{"data":null,"hasErrors":true,"meta":{"messages":["template not found"]}}'
        )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("template not found", result.stderr)

    def test_live_smoke_reports_the_response_body_when_the_request_fails(self):
        result = self.run_smoke_against(402, b'{"detail":"no credits remaining"}')

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("402", result.stderr)
        self.assertIn("no credits remaining", result.stderr)

    def test_live_smoke_does_not_print_extracted_document_content(self):
        """Evidence for the ticket must not paste customer fields into a log."""
        result = self.run_smoke_against(
            200,
            b'{"data":{"id":"1","metadata":{"taxpayerId":"123.456.789-00"}},"hasErrors":false}',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("123.456.789-00", result.stdout)
        self.assertNotIn("123.456.789-00", result.stderr)

    def test_live_smoke_runs_the_collection_extraction_request(self):
        received: dict[str, Any] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                received.update(
                    path=self.path,
                    authorization=self.headers.get("Authorization"),
                    content_type=self.headers.get("Content-Type"),
                    body=self.rfile.read(length),
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"data":{},"hasErrors":false}')

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt") as document:
                document.write(b"xtrak-954 smoke document")
                document.flush()
                environment = os.environ.copy()
                environment["COGNERIS_KEY"] = "xtkt_" + "live_test_only_not_a_secret"
                result = subprocess.run(
                    [
                        "npm",
                        "run",
                        "smoke:live",
                        "--",
                        "--file",
                        document.name,
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}",
                    ],
                    cwd=ROOT,
                    env=environment,
                    text=True,
                    capture_output=True,
                )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(received["path"], "/Document/extraction")
        self.assertEqual(
            received["authorization"], "Bearer xtkt_" + "live_test_only_not_a_secret"
        )
        self.assertTrue(received["content_type"].startswith("multipart/form-data;"))
        self.assertIn(b"xtrak-954 smoke document", received["body"])
        # The deselected optional field must not reach the wire: its value is
        # appended verbatim to the model prompt.
        self.assertNotIn(b"ComplementaryPrompt", received["body"])
        self.assertNotIn(b"<string>", received["body"])


class PostmanCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = COLLECTION.read_text(encoding="utf-8")
        cls.collection = json.loads(cls.raw)

    def test_is_an_importable_postman_v2_1_collection(self):
        self.assertEqual(
            self.collection["info"]["schema"],
            "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        )

    def test_uses_public_base_url_and_an_empty_secret_variable(self):
        variables = {
            variable["key"]: variable
            for variable in self.collection.get("variable", [])
        }
        self.assertEqual(variables["baseUrl"]["value"], "https://api-us.cogneris.ai")
        self.assertEqual(variables["bearerToken"]["value"], "")
        self.assertEqual(variables["bearerToken"]["type"], "secret")
        self.assertEqual(self.collection["auth"]["type"], "bearer")
        bearer = self.collection["auth"]["bearer"]
        self.assertEqual(len(bearer), 1)
        self.assertEqual(bearer[0]["key"], "token")
        self.assertEqual(bearer[0]["value"], "{{bearerToken}}")
        self.assertIsNone(SECRET_RE.search(self.raw), "collection contains a live-looking key")

    def test_extraction_request_uploads_a_file_with_bearer_auth(self):
        extraction = [
            request
            for request in requests(self.collection["item"])
            if request["url"].get("path") == ["Document", "extraction"]
        ]
        self.assertEqual(len(extraction), 1)

        request = extraction[0]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["url"]["host"], ["{{baseUrl}}"])
        self.assertIsNone(request["auth"], "request should inherit collection Bearer auth")

        fields = {field["key"]: field for field in request["body"]["formdata"]}
        self.assertEqual(request["body"]["mode"], "formdata")
        self.assertEqual(fields["file"]["type"], "file")

    def test_required_form_fields_are_selected(self):
        """The document itself must be sent, so it may never ship disabled."""
        for request in requests(self.collection["item"]):
            body = request.get("body") or {}
            if body.get("mode") != "formdata":
                continue
            for field in body["formdata"]:
                if is_required(field):
                    self.assertNotEqual(
                        field.get("disabled"),
                        True,
                        f"required field {field['key']!r} ships disabled",
                    )

    def test_optional_form_fields_are_not_sent_by_default(self):
        """
        An enabled optional field is sent verbatim by Postman and by the live
        smoke runner. ComplementaryPrompt is appended to the model prompt, so a
        selected placeholder silently corrupts the first extraction a reader
        runs. Optional fields must be opt-in.
        """
        optional = []
        for request in requests(self.collection["item"]):
            body = request.get("body") or {}
            if body.get("mode") != "formdata":
                continue
            for field in body["formdata"]:
                if not is_required(field):
                    optional.append(field)
                    self.assertEqual(
                        field.get("disabled"),
                        True,
                        f"optional field {field['key']!r} is selected by default",
                    )

        self.assertTrue(optional, "no optional form field found to check")

    def test_extraction_complementary_prompt_is_opt_in(self):
        extraction = [
            request
            for request in requests(self.collection["item"])
            if request["url"].get("path") == ["Document", "extraction"]
        ][0]
        fields = {field["key"]: field for field in extraction["body"]["formdata"]}
        self.assertEqual(fields["ComplementaryPrompt"].get("disabled"), True)
        self.assertNotEqual(fields["file"].get("disabled"), True)


if __name__ == "__main__":
    unittest.main()
