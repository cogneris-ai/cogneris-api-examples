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


if __name__ == "__main__":
    unittest.main()
