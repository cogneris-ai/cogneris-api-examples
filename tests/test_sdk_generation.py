from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
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


def sdk_snapshot(directory: Path = SDKS) -> Dict[str, Tuple[bytes, int, int]]:
    return {
        path.relative_to(directory).as_posix(): (
            path.read_bytes(),
            path.stat().st_mode,
            path.stat().st_mtime_ns,
        )
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SdkGenerationTests(unittest.TestCase):
    def run_generation_with_uvx_shim(self, fail_second_openapi=False):
        with tempfile.TemporaryDirectory(prefix="cogneris-generator-pin-") as directory:
            checkout = Path(directory)
            for name in ("scripts", "openapi", "sdks"):
                shutil.copytree(ROOT / name, checkout / name,
                                ignore=shutil.ignore_patterns("dist", "__pycache__", "node_modules"))
            for name in ("LICENSE", "NOTICE"):
                shutil.copy2(ROOT / name, checkout / name)
            (checkout / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
            binary = checkout / "bin"
            binary.mkdir()
            captured = checkout / "uvx-arguments.jsonl"
            shim = binary / "uvx"
            real_uvx = shutil.which("uvx")
            self.assertIsNotNone(real_uvx)
            shim.write_text(
                f"#!{sys.executable}\nimport json, os, sys\n"
                f"with open({str(captured)!r}, 'a') as output: output.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                f"calls = [json.loads(line) for line in open({str(captured)!r})]\n"
                f"if {fail_second_openapi!r} and sum('openapi-generator-cli' in call for call in calls) == 2: sys.exit(42)\n"
                f"os.execv({real_uvx!r}, [{real_uvx!r}, *sys.argv[1:]])\n"
            )
            shim.chmod(0o755)
            before = sdk_snapshot(checkout / "sdks")
            arguments = ["node", "scripts/generate-sdks.mjs"]
            if not fail_second_openapi:
                arguments.append("--check")
            result = subprocess.run(arguments, cwd=checkout,
                                    env={**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"]},
                                    text=True, capture_output=True)
            after = sdk_snapshot(checkout / "sdks")
            calls = [json.loads(line) for line in captured.read_text().splitlines()]
            return result, calls, before, after

    def test_generation_invokes_the_exact_formatter_and_openapi_runtime_pins(self):
        result, calls, before, after = self.run_generation_with_uvx_shim()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        python_call = next(call for call in calls if "openapi-python-client" in call)
        self.assertIn(["--with", "ruff==0.13.3"],
                      [python_call[index:index + 2] for index in range(len(python_call))])
        openapi_calls = [call for call in calls if "openapi-generator-cli" in call]
        self.assertEqual(len(openapi_calls), 2, calls)
        self.assertEqual([call[call.index("-g") + 1] for call in openapi_calls], ["csharp", "java"])
        for arguments in openapi_calls:
            pairs = [arguments[index:index + 2] for index in range(len(arguments))]
            self.assertIn(["--from", "openapi-generator-cli==7.25.0"], pairs)
            self.assertIn(["--with", "jdk4py==17.0.9.2"], pairs)
            self.assertNotIn("--skip-validate-spec", arguments)
        self.assertEqual(after, before)

    def test_second_openapi_generator_failure_preserves_all_committed_outputs(self):
        result, calls, before, after = self.run_generation_with_uvx_shim(fail_second_openapi=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("uvx exited with 42", result.stderr)
        self.assertEqual(len([call for call in calls if "openapi-generator-cli" in call]), 2)
        self.assertEqual(after, before)

    def test_generated_sdk_outputs_are_committed(self):
        for relative_path in ("sdks/typescript", "sdks/python", "sdks/csharp", "sdks/java", "sdks/manifest.json"):
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
                    "dependencies": {"ruff": "0.13.3"},
                },
                "typescript": {
                    "package": "@hey-api/openapi-ts",
                    "version": "0.99.0",
                },
                "csharp": {
                    "package": "openapi-generator-cli",
                    "version": "7.25.0",
                    "runtime": {"package": "jdk4py", "version": "17.0.9.2"},
                },
                "java": {
                    "package": "openapi-generator-cli",
                    "version": "7.25.0",
                    "runtime": {"package": "jdk4py", "version": "17.0.9.2"},
                    "gradle": {
                        "version": "8.14.5",
                        "distributionSha256": "6f74b601422d6d6fc4e1f9a1ab6522f642c2fdcbc15ae33ebd30ba3d7198e854",
                    },
                },
            },
        )
        self.assertEqual(package["devDependencies"]["@hey-api/openapi-ts"], "0.99.0")
        self.assertEqual(
            lock["packages"]["node_modules/@hey-api/openapi-ts"]["version"],
            "0.99.0",
        )

    def test_contract_passes_pinned_openapi_generator_validation(self):
        result = subprocess.run(
            [
                "uvx", "--from", "openapi-generator-cli==7.25.0",
                "--with", "jdk4py==17.0.9.2", "openapi-generator-cli",
                "validate", "-i", str(ROOT / "openapi/cogneris-openapi.yaml"),
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_java_runner_sets_java_home_for_a_java_17_child(self):
        result = subprocess.run(
            [
                "uv", "run", "--with", "jdk4py==17.0.9.2", "python",
                "scripts/run-java.py", "--", sys.executable, "-c",
                (
                    "import os, subprocess, sys; "
                    "version = subprocess.run(['java', '-version'], text=True, "
                    "capture_output=True); "
                    "print(os.environ['JAVA_HOME']); "
                    "print(version.stderr, end=''); "
                    "sys.exit(version.returncode)"
                ),
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.splitlines()[0])
        self.assertRegex(result.stdout, r'(?:openjdk|java) version "17\.')

    def test_java_runner_falls_back_when_configured_java_is_unusable(self):
        uv = shutil.which("uv")
        self.assertIsNotNone(uv)
        child = "import os; print(os.environ['JAVA_HOME']); print(os.environ['PATH'])"
        probe = (
            "import os, subprocess, sys; from jdk4py import JAVA_HOME; "
            "result = subprocess.run("
            "[sys.executable, 'scripts/run-java.py', '--', sys.executable, '-c', "
            f"{child!r}], "
            "env={**os.environ, 'JAVA_HOME': '/definitely/missing-java-home', "
            "'PATH': ''}, text=True, capture_output=True); "
            "print(result.returncode); print(JAVA_HOME); print(result.stdout, end=''); "
            "print(result.stderr, end='', file=sys.stderr)"
        )
        result = subprocess.run(
            [
                uv, "run", "--with", "jdk4py==17.0.9.2", "python",
                "-c", probe,
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        child_status, expected_java_home, java_home, path = result.stdout.splitlines()
        self.assertEqual(child_status, "0")
        self.assertEqual(java_home, expected_java_home)
        self.assertEqual(path, str(Path(java_home) / "bin"))

    def test_java_runner_returns_the_child_status(self):
        result = subprocess.run(
            [
                "uv", "run", "--with", "jdk4py==17.0.9.2", "python",
                "scripts/run-java.py", "--", sys.executable, "-c",
                "raise SystemExit(23)",
            ],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)

    def test_manifest_binds_every_artifact_to_the_public_contract(self):
        manifest = json.loads(MANIFEST.read_text())
        source = ROOT / "openapi" / "cogneris-openapi.yaml"
        self.assertEqual(manifest["source"]["path"], "openapi/cogneris-openapi.yaml")
        self.assertEqual(manifest["source"]["sha256"], file_hash(source))

        self.assertEqual(set(manifest["packages"]), {"typescript", "python", "csharp", "java"})
        self.assertEqual(manifest["packages"]["csharp"]["name"], "Cogneris.DocumentAI")
        self.assertEqual(manifest["packages"]["java"]["name"], "ai.cogneris:cogneris-document-ai-sdk")
        self.assertIn("LICENSE", manifest["packages"]["csharp"]["files"])
        self.assertIn("NOTICE", manifest["packages"]["java"]["files"])
        for sdk_name in ("typescript", "python", "csharp", "java"):
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
        self.assertEqual(typescript["name"], "@cogneris-ai/document-ai-sdk")
        self.assertEqual(typescript["version"], "0.2.0")
        self.assertFalse(typescript.get("private", False))
        self.assertEqual(typescript["scripts"]["build"], "tsc -p tsconfig.json")
        self.assertEqual(
            typescript["repository"],
            {
                "type": "git",
                "url": "git+https://github.com/cogneris-ai/cogneris-api-examples.git",
            },
        )

        pyproject = (SDKS / "python" / "pyproject.toml").read_text()
        self.assertRegex(pyproject, r'(?m)^name = "cogneris-document-ai-sdk"$')
        self.assertRegex(pyproject, r'(?m)^version = "0\.1\.0"$')
        self.assertRegex(pyproject, r'(?m)^requires-python = ">=3\.9,<4\.0"$')
        self.assertTrue(
            (SDKS / "python" / "cogneris_document_ai_sdk" / "__init__.py").is_file()
        )

    def test_csharp_and_java_metadata_and_legal_files_are_normalized(self):
        self.assertTrue((SDKS / "csharp/src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj").is_file(), "missing generated C# project")
        project = ET.parse(SDKS / "csharp/src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj")
        for tag, value in (("PackageId", "Cogneris.DocumentAI"), ("Version", "0.2.0"),
                           ("TargetFramework", "net8.0"), ("PackageLicenseExpression", "Apache-2.0"),
                           ("Authors", "COGNERIS, INC."), ("Company", "COGNERIS, INC."),
                           ("Copyright", "Copyright 2026 COGNERIS, INC."),
                           ("RepositoryUrl", "https://github.com/cogneris-ai/cogneris-api-examples.git")):
            self.assertEqual(project.findtext(f".//{tag}"), value)
        for legal in ("LICENSE", "NOTICE"):
            item = project.find(f".//None[@Include='../../{legal}']")
            self.assertIsNotNone(item)
            self.assertEqual(item.attrib, {"Include": f"../../{legal}", "Pack": "true", "PackagePath": ""})
        pom = ET.parse(SDKS / "java/pom.xml")
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        for tag, value in (("groupId", "ai.cogneris"), ("artifactId", "cogneris-document-ai-sdk"), ("version", "0.2.0")):
            self.assertEqual(pom.findtext(f"m:{tag}", namespaces=ns), value)
        self.assertEqual(pom.findtext("m:url", namespaces=ns), "https://github.com/cogneris-ai/cogneris-api-examples")
        self.assertEqual(pom.findtext("m:developers/m:developer/m:name", namespaces=ns), "COGNERIS, INC.")
        self.assertEqual(
            pom.findtext("m:developers/m:developer/m:organizationUrl", namespaces=ns),
            "https://github.com/cogneris-ai",
        )
        self.assertEqual(
            pom.findtext("m:scm/m:url", namespaces=ns),
            "https://github.com/cogneris-ai/cogneris-api-examples",
        )
        for target in ("source", "target"):
            self.assertEqual(pom.findtext(f"m:properties/m:maven.compiler.{target}", namespaces=ns), "17")
        self.assertEqual(pom.findtext(".//m:requireJavaVersion/m:version", namespaces=ns), "17")
        gradle = (SDKS / "java/build.gradle").read_text()
        self.assertEqual(gradle.count("JavaVersion.VERSION_17"), 2)
        self.assertNotIn("JavaVersion.VERSION_11", gradle)
        properties = (SDKS / "java/gradle/wrapper/gradle-wrapper.properties").read_text()
        self.assertIn("gradle-8.14.5-bin.zip", properties)
        self.assertEqual(properties.count("distributionSha256Sum=6f74b601422d6d6fc4e1f9a1ab6522f642c2fdcbc15ae33ebd30ba3d7198e854"), 1)
        for sdk in ("typescript", "python", "csharp", "java"):
            for legal in ("LICENSE", "NOTICE"):
                self.assertEqual((SDKS / sdk / legal).read_bytes(), (ROOT / legal).read_bytes())
        for legal in ("LICENSE", "NOTICE"):
            self.assertEqual((SDKS / "java/src/main/resources/META-INF" / legal).read_bytes(), (ROOT / legal).read_bytes())
        self.assertTrue((SDKS / "java/src/main/java/ai/cogneris/documentai").is_dir())

    def test_csharp_and_java_generator_scaffolding_is_removed(self):
        removed = {
            "csharp": (".gitignore", ".openapi-generator-ignore", ".openapi-generator", "appveyor.yml", "api", "docs", "docs/scripts", "src/Cogneris.DocumentAI.Test", "Cogneris.DocumentAI.sln", "src/Cogneris.DocumentAI/README.md"),
            "java": (".github", ".gitignore", ".openapi-generator-ignore", ".openapi-generator", ".travis.yml", "api", "docs", "git_push.sh", "build.sbt", "src/test"),
        }
        for sdk, paths in removed.items():
            self.assertTrue((SDKS / sdk).is_dir(), f"missing generated SDK output: sdks/{sdk}")
            for path in paths:
                self.assertFalse((SDKS / sdk / path).exists(), f"unwanted scaffolding: {sdk}/{path}")

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
                ["cogneris_document_ai_sdk-0.2.0-py3-none-any.whl"],
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

    def test_failed_install_and_restore_preserve_the_old_tree_for_manual_recovery(self):
        javascript = r"""
import fs from "node:fs/promises";
import path from "node:path";
import { replaceOutput } from "./scripts/sdk-output-swap.mjs";

const sandbox = process.env.COGNERIS_SWAP_TEST_ROOT;
const temporaryRoot = path.join(sandbox, "generation-temp");
const stagedOutput = path.join(temporaryRoot, "sdks");
const committedOutput = path.join(sandbox, "sdks");
await fs.mkdir(stagedOutput, { recursive: true });
await fs.mkdir(committedOutput, { recursive: true });
await fs.writeFile(path.join(stagedOutput, "marker.txt"), "new SDK tree");
await fs.writeFile(path.join(committedOutput, "marker.txt"), "old SDK tree");

let renameCalls = 0;
const filesystem = {
  mkdtemp: fs.mkdtemp.bind(fs),
  rm: fs.rm.bind(fs),
  rename: async (source, destination) => {
    renameCalls += 1;
    if (renameCalls === 2 || renameCalls === 3) {
      const error = new Error(renameCalls === 2 ? "install denied" : "restore denied");
      error.code = "EACCES";
      throw error;
    }
    return fs.rename(source, destination);
  },
};

let caught;
try {
  await replaceOutput({ committedOutput, stagedOutput, filesystem });
} catch (error) {
  caught = error;
} finally {
  // Mirrors generate-sdks.mjs's unconditional staging cleanup.
  await fs.rm(temporaryRoot, { recursive: true, force: true });
}

const backupRoots = (await fs.readdir(sandbox))
  .filter((entry) => entry.startsWith(".sdk-backup-"));
const recoveryPath = backupRoots.length === 1
  ? path.join(sandbox, backupRoots[0], "sdks")
  : null;
let oldTreeSurvives = false;
if (recoveryPath) {
  oldTreeSurvives =
    (await fs.readFile(path.join(recoveryPath, "marker.txt"), "utf8")) ===
    "old SDK tree";
}

console.log(JSON.stringify({
  errorMessage: caught?.message ?? null,
  oldTreeSurvives,
  recoveryPath,
}));
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            environment = {
                **os.environ,
                "COGNERIS_SWAP_TEST_ROOT": temporary_directory,
            }
            result = subprocess.run(
                ["node", "--input-type=module", "--eval", javascript],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            outcome = json.loads(result.stdout)
            self.assertTrue(outcome["oldTreeSurvives"], outcome)
            self.assertIsNotNone(outcome["recoveryPath"], outcome)
            self.assertIn(outcome["recoveryPath"], outcome["errorMessage"])
            self.assertIn("automatic recovery failed", outcome["errorMessage"])

    def test_generated_artifacts_exclude_internal_platform_and_admin_routes(self):
        generated_text = "\n".join(
            path.read_text(errors="ignore")
            for directory in (SDKS / name for name in ("typescript", "python", "csharp", "java"))
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

    def test_document_envelope_meta_is_the_service_response_meta_in_every_sdk(self):
        # XTRAK-1687: the six /Document/* routes answer with `Envelope`. Its
        # `meta` is the same producer type the job envelopes describe as
        # ServiceResponseMeta (errors, creditsConsumed). An inline two-field
        # copy made the generated C#/Java models drop both at runtime.
        source = (ROOT / "openapi/cogneris-openapi.yaml").read_text()
        self.assertIn("        meta: { $ref: '#/components/schemas/ServiceResponseMeta' }\n        hasErrors:", source)
        expectations = {
            "typescript/src/types.gen.ts": "meta?: ServiceResponseMeta;",
            "python/cogneris_document_ai_sdk/models/envelope.py": "from ..models.service_response_meta import ServiceResponseMeta",
            "csharp/src/Cogneris.DocumentAI/Model/Envelope.cs": "Option<ServiceResponseMeta?> MetaOption",
            "java/src/main/java/ai/cogneris/documentai/model/Envelope.java": "private ServiceResponseMeta meta;",
        }
        for relative_path, expected in expectations.items():
            with self.subTest(sdk=relative_path):
                self.assertIn(expected, (SDKS / relative_path).read_text())
        for orphan in (
            "python/cogneris_document_ai_sdk/models/envelope_meta.py",
            "csharp/src/Cogneris.DocumentAI/Model/EnvelopeMeta.cs",
            "java/src/main/java/ai/cogneris/documentai/model/EnvelopeMeta.java",
        ):
            with self.subTest(orphan=orphan):
                self.assertFalse((SDKS / orphan).exists(), orphan)

    def test_generated_text_has_no_trailing_whitespace(self):
        offenders = []
        for directory in (SDKS / name for name in ("typescript", "python", "csharp", "java")):
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                if b"\0" in path.read_bytes():
                    continue
                if path.read_bytes().endswith((b"\n\n", b"\r\n\r\n")):
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}:blank lines at EOF")
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
