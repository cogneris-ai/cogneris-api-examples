import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SDK = ROOT / "sdks" / "python"
INSTALLED_SMOKE = ROOT / "tests" / "sdk_python_installed_smoke.py"


class PythonInstalledSdkSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="cogneris-python-sdk-smoke-")
        temporary = Path(cls.temporary.name)
        output = temporary / "dist"
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(output)],
            cwd=PYTHON_SDK,
            check=True,
            capture_output=True,
            text=True,
        )
        wheel = next(output.glob("*.whl"))
        cls.environment = temporary / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(cls.environment)],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.python = cls.environment / "bin" / "python"
        subprocess.run(
            ["uv", "pip", "install", "--python", str(cls.python), str(wheel)],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_installed(self, test_name):
        environment = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONPATH", "VIRTUAL_ENV"}
        }
        environment["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"] = str(ROOT)
        result = subprocess.run(
            [
                str(self.python),
                str(INSTALLED_SMOKE),
                f"InstalledPythonSdkTests.{test_name}",
                "-v",
            ],
            cwd=self.temporary.name,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_behavior_resolves_from_installed_wheel(self):
        self.run_installed("test_module_resolves_from_site_packages")

    def test_reflected_server_content_is_not_retained(self):
        self.run_installed("test_reflected_server_content_is_not_retained")

    def test_submit_hint_delays_first_poll(self):
        self.run_installed("test_submit_hint_delays_first_poll")

    def test_transport_and_parse_failures_are_safe_typed_errors(self):
        self.run_installed("test_transport_and_parse_failures_are_safe_typed_errors")

    def test_poll_intervals_handle_non_finite_values_safely(self):
        self.run_installed("test_poll_intervals_handle_non_finite_values_safely")

    def test_public_flows_and_bounded_polling(self):
        self.run_installed("test_public_flows_and_bounded_polling")


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
