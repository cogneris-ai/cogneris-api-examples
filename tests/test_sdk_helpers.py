import os
import hashlib
import json
import shutil
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
    def test_cli_suite_preserves_existing_checkout_build_and_dependency_state(self):
        # Run the real npm entrypoint in a private copy: a failing regression
        # must never delete output or alter dependencies in the active checkout.
        with tempfile.TemporaryDirectory(prefix="cogneris-cli-isolation-") as directory:
            checkout = Path(directory)
            for name in ("cli", "sdks/typescript", "node_modules"):
                shutil.copytree(ROOT / name, checkout / name, symlinks=True,
                                ignore=shutil.ignore_patterns("@cogneris-ai"))
            for name in ("package.json", "package-lock.json", "scripts/build-cli.mjs", "tests/cli_smoke.mjs"):
                destination = checkout / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, destination)
            roots = ("cli/dist", "node_modules/@cogneris-ai/document-ai-sdk")
            for name in roots:
                sentinel = checkout / name / "pre-existing-sentinel"
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_bytes(b"pre-existing user artifact: do not change")

            def snapshot(name):
                base = checkout / name
                files = [base] if base.is_file() else sorted(base.rglob("*"))
                return {str(file.relative_to(checkout)): (
                    file.lstat().st_mode,
                    os.readlink(file) if file.is_symlink() else hashlib.sha256(file.read_bytes()).hexdigest(),
                ) for file in files if file.is_file() or file.is_symlink()}

            names = (*roots, "package-lock.json", "node_modules/.package-lock.json")
            before = {name: snapshot(name) for name in names}
            result = subprocess.run(["npm", "run", "test:cli"], cwd=checkout,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in names:
                with self.subTest(path=name):
                    self.assertEqual(snapshot(name), before[name], "CLI tests changed existing checkout state")

    def test_packed_typescript_sdk_against_loopback(self):
        result = subprocess.run(
            ["node", "--test", str(ROOT / "tests" / "sdk_typescript_smoke.mjs")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class CSharpSdkSmokeTests(unittest.TestCase):
    def test_packed_csharp_sdk_against_loopback(self):
        fixture = ROOT / "tests/fixtures/csharp-consumer"
        dotnet = os.environ.get("COGNERIS_DOTNET", "dotnet")
        for file in fixture.iterdir():
            self.assertNotIn("ProjectReference", file.read_text())
            self.assertNotIn(str(ROOT), file.read_text())
        with tempfile.TemporaryDirectory(prefix="cogneris-csharp-consumer-") as directory:
            root = Path(directory).resolve()
            packages = root / "packages"
            cache = root / "nuget-cache"
            environment = dict(os.environ, NUGET_PACKAGES=str(cache))
            # Build the current generated tree without leaving bin/obj in the
            # deterministic SDK output, then expose only its NuGet artifact.
            sdk = shutil.copytree(ROOT / "sdks/csharp", root / "sdk")
            packed = subprocess.run([
                dotnet, "pack", str(sdk / "src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj"),
                "-c", "Release", "-o", str(packages),
            ], cwd=root, env=environment, text=True, capture_output=True)
            self.assertEqual(packed.returncode, 0, packed.stdout + packed.stderr)
            project = shutil.copytree(fixture, root / "consumer")
            # Explicit restore avoids semicolon parsing by MSBuild command-line
            # properties, and no source project is available during consumption.
            shutil.rmtree(sdk)
            restored = subprocess.run([
                dotnet, "restore", str(project), "--source", str(packages),
                "--source", "https://api.nuget.org/v3/index.json",
            ], cwd=root, env=environment, text=True, capture_output=True)
            self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
            assets = json.loads((project / "obj/project.assets.json").read_text())
            library = assets["libraries"]["Cogneris.DocumentAI/0.1.0"]
            self.assertEqual(library["type"], "package")
            artifact = packages / "Cogneris.DocumentAI.0.1.0.nupkg"
            installed = cache / library["path"] / "cogneris.documentai.0.1.0.nupkg"
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(),
                             hashlib.sha256(installed.read_bytes()).hexdigest())
            result = subprocess.run([
                dotnet, "run", "--project", str(project), "--configuration", "Release", "--no-restore",
            ], cwd=root, env=environment, text=True, capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(str(cache / library["path"] / "lib/net8.0/Cogneris.DocumentAI.dll"), result.stdout)
            print(result.stdout, end="")
            print("NuGet artifact SHA256: " + hashlib.sha256(artifact.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
