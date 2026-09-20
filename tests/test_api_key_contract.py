"""Keep the published authentication contract aligned with sandbox support."""

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ApiKeyContractTests(unittest.TestCase):
    def test_public_authentication_describes_both_key_environments(self):
        contract = yaml.safe_load((ROOT / "openapi/cogneris-openapi.yaml").read_text())
        descriptions = [
            contract["info"]["description"],
            contract["components"]["securitySchemes"]["ApiKey"]["description"],
            contract["components"]["responses"]["Unauthorized"]["description"],
        ]
        for description in descriptions:
            with self.subTest(description=description):
                for prefix, environment in [("xtkt_live_", "production"), ("xtkt_test_", "sandbox")]:
                    self.assertIn(f"`{prefix}`", description)
                    self.assertIn(environment, description)


if __name__ == "__main__":
    unittest.main()
