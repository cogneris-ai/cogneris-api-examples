from __future__ import annotations

import json
import re
import unittest
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
