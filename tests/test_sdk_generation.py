from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]
SDKS = ROOT / "sdks"
MANIFEST = SDKS / "manifest.json"


def run_sdk_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["npm", "run", "check:sdks"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def sdk_snapshot() -> Dict[str, Tuple[bytes, int, int]]:
    return {
        path.relative_to(SDKS).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_mtime_ns,
        )
        for path in sorted(SDKS.rglob("*"))
        if path.is_file()
    }


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SdkGenerationTests(unittest.TestCase):
    def test_generated_sdk_outputs_are_committed(self):
        for relative_path in ("sdks/typescript", "sdks/python", "sdks/manifest.json"):
            with self.subTest(path=relative_path):
                self.assertTrue(
                    (ROOT / relative_path).exists(),
                    f"missing generated SDK output: {relative_path}",
                )

    def test_generator_versions_are_exactly_pinned(self):
        generators = json.loads(
            (ROOT / "scripts" / "sdk-config" / "generators.json").read_text()
        )
        package = json.loads((ROOT / "package.json").read_text())
        lock = json.loads((ROOT / "package-lock.json").read_text())

        self.assertEqual(
            generators,
            {
                "python": {
                    "package": "openapi-python-client",
                    "version": "0.26.2",
                },
                "typescript": {
                    "package": "@hey-api/openapi-ts",
                    "version": "0.99.0",
                },
            },
        )
        self.assertEqual(package["devDependencies"]["@hey-api/openapi-ts"], "0.99.0")
        self.assertEqual(
            lock["packages"]["node_modules/@hey-api/openapi-ts"]["version"],
            "0.99.0",
        )

    def test_manifest_binds_every_artifact_to_the_public_contract(self):
        manifest = json.loads(MANIFEST.read_text())
        source = ROOT / "openapi" / "cogneris-openapi.yaml"
        self.assertEqual(manifest["source"]["path"], "openapi/cogneris-openapi.yaml")
        self.assertEqual(manifest["source"]["sha256"], file_hash(source))

        for sdk_name in ("typescript", "python"):
            expected_files = {
                path.relative_to(SDKS / sdk_name).as_posix()
                for path in (SDKS / sdk_name).rglob("*")
                if path.is_file()
            }
            recorded_files = manifest["packages"][sdk_name]["files"]
            self.assertEqual(set(recorded_files), expected_files)
            for relative_path, expected_hash in recorded_files.items():
                self.assertEqual(
                    file_hash(SDKS / sdk_name / relative_path),
                    expected_hash,
                    relative_path,
                )

    def test_package_identities_and_versions_are_publishable(self):
        typescript = json.loads((SDKS / "typescript" / "package.json").read_text())
        self.assertEqual(typescript["name"], "@cogneris/document-ai-sdk")
        self.assertEqual(typescript["version"], "0.1.0")
        self.assertFalse(typescript.get("private", False))
        self.assertEqual(typescript["scripts"]["build"], "tsc -p tsconfig.json")

        pyproject = (SDKS / "python" / "pyproject.toml").read_text()
        self.assertRegex(pyproject, r'(?m)^name = "cogneris-document-ai-sdk"$')
        self.assertRegex(pyproject, r'(?m)^version = "0\.1\.0"$')
        self.assertRegex(pyproject, r'(?m)^requires-python = ">=3\.9,<4\.0"$')
        self.assertTrue(
            (SDKS / "python" / "cogneris_document_ai_sdk" / "__init__.py").is_file()
        )

    def test_typescript_package_builds(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "typescript"
            shutil.copytree(SDKS / "typescript", package)
            result = subprocess.run(
                [
                    str(ROOT / "node_modules" / ".bin" / "tsc"),
                    "-p",
                    str(package / "tsconfig.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue((package / "dist" / "index.js").is_file())
            self.assertTrue((package / "dist" / "index.d.ts").is_file())

    def test_python_package_builds_a_wheel(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "python"
            wheels = Path(temporary_directory) / "wheels"
            shutil.copytree(SDKS / "python", package)
            result = subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(wheels), str(package)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                [path.name for path in wheels.glob("*.whl")],
                ["cogneris_document_ai_sdk-0.1.0-py3-none-any.whl"],
            )

    def test_check_is_exact_and_does_not_modify_committed_outputs(self):
        before = sdk_snapshot()
        result = run_sdk_check()
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(sdk_snapshot(), before)

    def test_check_detects_a_missing_output_without_repairing_it(self):
        generated_file = SDKS / "typescript" / "src" / "index.ts"
        with tempfile.TemporaryDirectory() as temporary_directory:
            backup = Path(temporary_directory) / generated_file.name
            shutil.copy2(generated_file, backup)
            generated_file.unlink()
            try:
                result = run_sdk_check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing: typescript/src/index.ts", result.stderr)
                self.assertFalse(generated_file.exists(), "check mode repaired missing output")
            finally:
                shutil.copy2(backup, generated_file)

    def test_check_detects_stale_output_without_repairing_it(self):
        generated_file = SDKS / "typescript" / "src" / "index.ts"
        original = generated_file.read_bytes()
        stale = original + b"// stale test sentinel\n"
        generated_file.write_bytes(stale)
        try:
            result = run_sdk_check()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("changed: typescript/src/index.ts", result.stderr)
            self.assertEqual(
                generated_file.read_bytes(),
                stale,
                "check mode overwrote stale output",
            )
        finally:
            generated_file.write_bytes(original)

    def test_generated_artifacts_exclude_internal_platform_and_admin_routes(self):
        generated_text = "\n".join(
            path.read_text(errors="ignore")
            for directory in (SDKS / "typescript", SDKS / "python")
            for path in directory.rglob("*")
            if path.is_file()
        )
        lower = generated_text.lower()
        for forbidden in ("/platform", "platform/v1", "/admin", "admincontroller"):
            with self.subTest(route=forbidden):
                self.assertNotIn(forbidden, lower)

        # Positive controls ensure this test is inspecting generated API routes.
        self.assertIn("/Document/extraction", generated_text)
        self.assertIn("/api/v1/portal/forms", generated_text)

    def test_generated_text_has_no_trailing_whitespace(self):
        offenders = []
        for directory in (SDKS / "typescript", SDKS / "python"):
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                for line_number, line in enumerate(
                    path.read_text(errors="ignore").splitlines(), start=1
                ):
                    if line != line.rstrip():
                        offenders.append(
                            f"{path.relative_to(ROOT).as_posix()}:{line_number}"
                        )
        self.assertEqual(offenders, [], "trailing whitespace in generated artifacts")


if __name__ == "__main__":
    unittest.main()
