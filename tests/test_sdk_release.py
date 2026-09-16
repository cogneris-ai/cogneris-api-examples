import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sdk-release.py"


class ReleaseArtifactTests(unittest.TestCase):
    def invoke(self, *arguments, environment=None):
        self.assertTrue(SCRIPT.is_file(), "missing release artifact builder/verifier")
        return subprocess.run([sys.executable, str(SCRIPT), *arguments], cwd=ROOT,
                              env=environment, text=True, capture_output=True)

    def test_version_gate_rejects_missing_malformed_and_mismatched_versions(self):
        for version in ("", "v0.1.0", "01.1.0", "0.1", "0.1.0;false", "0.2.0"):
            with self.subTest(version=version):
                result = self.invoke("check-version", "--version", version)
                self.assertNotEqual(result.returncode, 0)
        result = self.invoke("check-version", "--version", "0.1.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_artifacts_install_and_reject_tampering_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-release-test-") as directory:
            output = Path(directory) / "artifacts"
            result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest_bytes = (output / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            digest = hashlib.sha256(manifest_bytes).hexdigest()
            self.assertEqual(set(manifest["files"]), {
                "cogneris-document-ai-sdk-0.1.0.tgz", "cogneris-document-ai-cli-0.1.0.tgz",
                "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl"})
            arguments = ["--version", "0.1.0", "--artifacts", str(output),
                         "--manifest-sha256", digest, "--source", manifest["source"]]
            result = self.invoke("verify", *arguments)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.invoke("verify", *arguments, "--python-only")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            # Never overwrite an existing artifact directory, including user files.
            marker = output / "pre-existing.txt"
            marker.write_text("must survive")
            result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), "must survive")
            result = self.invoke("verify", *arguments)
            self.assertNotEqual(result.returncode, 0, "extra files must be rejected")
            marker.unlink()

            artifact = output / "cogneris-document-ai-sdk-0.1.0.tgz"
            original = artifact.read_bytes()
            artifact.write_bytes(original + b"tampered")
            result = self.invoke("verify", *arguments)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("digest", result.stderr.lower())
            artifact.write_bytes(original)
            # A self-consistent checksum is insufficient if package metadata lies.
            with tarfile.open(artifact, "w:gz") as archive:
                encoded = json.dumps({"name": "@cogneris/document-ai-sdk", "version": "9.9.9"}).encode()
                member = tarfile.TarInfo("package/package.json")
                member.size = len(encoded)
                archive.addfile(member, io.BytesIO(encoded))
            forged_manifest = dict(manifest, files=dict(manifest["files"]))
            forged_manifest["files"][artifact.name] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            forged_bytes = json.dumps(forged_manifest).encode()
            (output / "manifest.json").write_bytes(forged_bytes)
            forged_arguments = list(arguments)
            forged_arguments[5] = hashlib.sha256(forged_bytes).hexdigest()
            result = self.invoke("verify", *forged_arguments)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("identity/version", result.stderr)
            artifact.write_bytes(original)
            (output / "manifest.json").write_bytes(manifest_bytes)
            bad_source = arguments[:-1] + ["0" * 40]
            self.assertNotEqual(self.invoke("verify", *bad_source).returncode, 0)
            (output / "manifest.json").write_bytes(manifest_bytes + b" ")
            self.assertNotEqual(self.invoke("verify", *arguments).returncode, 0)
            (output / "manifest.json").write_bytes(manifest_bytes)

            env = dict(os.environ)
            env.update(SDK_RELEASE_READY="", SDK_NPM_TRUSTED_PUBLISHING_READY="",
                       SDK_PYPI_TRUSTED_PUBLISHING_READY="")
            for registry in ("npm", "pypi"):
                result = self.invoke("check-publish", *arguments, "--registry", registry, environment=env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("SDK_RELEASE_READY", result.stderr)
            env.update(SDK_RELEASE_READY="true", SDK_NPM_TRUSTED_PUBLISHING_READY="true",
                       SDK_PYPI_TRUSTED_PUBLISHING_READY="true", GITHUB_REPOSITORY="cogneris-ai/cogneris-api-examples")
            result = self.invoke("check-publish", *arguments, "--registry", "npm", environment=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("repository", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
