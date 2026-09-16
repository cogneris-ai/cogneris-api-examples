import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK = ROOT / "sdks" / "python"
PYTHON_SMOKE = ROOT / "tests" / "examples_python_installed_smoke.py"


class DocumentationContractTests(unittest.TestCase):
    def test_readme_is_the_complete_truthful_quickstart(self):
        readme = (ROOT / "README.md").read_text().lower()
        required_terms = (
            "@cogneris/document-ai-sdk",
            "cogneris-document-ai-sdk",
            "@cogneris/document-ai-cli",
            "cognerisclient",
            "cogneris_api_key",
            "cogneris_region",
            "2026-08-07",
            "postman",
            "multipart/form-data",
            "50 requests",
            "10 mb",
            "500 mb",
            "tenant configuration",
            "evidence",
            "cost",
            "destination",
            "webhook-signature",
            "not published",
            "local release artifacts",
        )
        for term in required_terms:
            self.assertIn(term, readme, f"README is missing required term: {term}")
        self.assertIn("exactly `us` and `eu`", readme)
        self.assertIn("no fetch-by-url", readme)
        self.assertIn("not sdk helper features", readme)

    def test_support_and_versioning_policies_define_public_boundaries(self):
        support = (ROOT / "SUPPORT.md").read_text().lower()
        versioning = (ROOT / "VERSIONING.md").read_text().lower()
        for term in ("github issues", "security", "public release", "owner-approved"):
            self.assertIn(term, support)
        self.assertIn("do not report", support)
        for term in ("semantic versioning", "2026-08-07", "deprecation", "openapi"):
            self.assertIn(term, versioning)
        self.assertIn("unpublished", versioning)

    def test_examples_document_only_supported_environment_and_inputs(self):
        for relative in (
            Path("examples/typescript/quickstart.mjs"),
            Path("examples/python/quickstart.py"),
        ):
            source = (ROOT / relative).read_text()
            self.assertIn("COGNERIS_API_KEY", source)
            self.assertIn("COGNERIS_REGION", source)
            self.assertNotIn("COGNERIS_BASE_URL", source)
            self.assertNotIn("--base-url", source)

    def test_documented_consumer_setup_resolves_examples_and_local_cli(self):
        readme = (ROOT / "README.md").read_text()
        match = re.search(
            r"<!-- consumer-setup:start -->\s*```bash\n(?P<script>.*?)\n```\s*"
            r"<!-- consumer-setup:end -->",
            readme,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "README must provide an executable consumer setup block")

        with tempfile.TemporaryDirectory(prefix="cogneris-documented-workflow-") as temporary_name:
            temporary = Path(temporary_name)
            release = temporary / "release"
            consumer = temporary / "consumer"
            release.mkdir()
            try:
                subprocess.run(
                    ["npm", "run", "build", "--prefix", "sdks/typescript"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["npm", "run", "build:cli"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [
                        "npm", "pack", "./sdks/typescript", "--pack-destination",
                        str(release), "--silent",
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["npm", "pack", "./cli", "--pack-destination", str(release), "--silent"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["uv", "build", "--wheel", "--out-dir", str(release)],
                    cwd=PYTHON_SDK,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                environment = dict(os.environ)
                environment.update(
                    {
                        "COGNERIS_CHECKOUT": str(ROOT),
                        "COGNERIS_RELEASE": str(release),
                        "COGNERIS_CONSUMER": str(consumer),
                        "PYTHON_BIN": sys.executable,
                    }
                )
                result = subprocess.run(
                    ["bash", "-eu", "-o", "pipefail", "-c", match.group("script")],
                    cwd=temporary,
                    check=False,
                    capture_output=True,
                    text=True,
                    env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

                invocations = (
                    (["node", "./examples/typescript/quickstart.mjs", "extract", "missing.pdf"], 2),
                    ([str(consumer / ".venv/bin/python"), "./examples/python/quickstart.py", "extract", "missing.pdf"], 2),
                    (["./node_modules/.bin/cogneris", "jobs", "get", "job-id"], 2),
                )
                for command, expected_code in invocations:
                    invoked = subprocess.run(
                        command,
                        cwd=consumer,
                        check=False,
                        capture_output=True,
                        text=True,
                        env={key: value for key, value in environment.items() if key != "COGNERIS_API_KEY"},
                    )
                    self.assertEqual(invoked.returncode, expected_code, invoked.stdout + invoked.stderr)
                    self.assertEqual(invoked.stdout, "")
            finally:
                shutil.rmtree(ROOT / "sdks/typescript/dist", ignore_errors=True)
                shutil.rmtree(ROOT / "cli/dist", ignore_errors=True)


class InstalledExampleSmokeTests(unittest.TestCase):
    def test_typescript_example_uses_installed_sdk_against_loopback(self):
        result = subprocess.run(
            ["node", "--test", str(ROOT / "tests" / "examples_typescript_smoke.mjs")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_python_example_uses_installed_wheel_against_loopback(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-python-example-") as temporary_name:
            temporary = Path(temporary_name)
            output = temporary / "dist"
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(output)],
                cwd=PYTHON_SDK,
                check=True,
                capture_output=True,
                text=True,
            )
            wheel = next(output.glob("*.whl"))
            environment = temporary / "venv"
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
            child_environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"PYTHONPATH", "VIRTUAL_ENV"}
            }
            child_environment["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"] = str(ROOT)
            result = subprocess.run(
                [str(python), str(PYTHON_SMOKE), "-v"],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
                env=child_environment,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
