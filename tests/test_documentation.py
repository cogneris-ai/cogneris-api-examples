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


def markdown_section_containing(document, offset):
    headings = list(re.finditer(r"^## ", document, re.MULTILINE))
    start = max((heading.start() for heading in headings if heading.start() <= offset), default=0)
    end = min((heading.start() for heading in headings if heading.start() > offset), default=len(document))
    return document[start:end]


def assert_no_unbound_package_install_guidance(test_case, document):
    dotnet_commands = re.findall(
        r"^dotnet add package Cogneris\.DocumentAI[^\n]*$",
        document,
        re.MULTILINE,
    )
    for command in dotnet_commands:
        test_case.assertEqual(
            command.count('--source "$COGNERIS_RELEASE"'),
            1,
            "Every Cogneris.DocumentAI install must use the exact local release source",
        )

    dependency_blocks = re.finditer(r"<dependency>.*?</dependency>", document, re.DOTALL)
    for match in dependency_blocks:
        block = match.group(0)
        if not (
            "<groupId>ai.cogneris</groupId>" in block
            and "<artifactId>cogneris-document-ai-sdk</artifactId>" in block
        ):
            continue
        section = markdown_section_containing(document, match.start())
        if section.startswith("## Package availability\n"):
            test_case.assertIn(
                "https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/",
                section,
                "Public Maven installation must identify the verified registry release",
            )
            test_case.assertIn("<version>0.1.0</version>", block)
            continue
        test_case.assertIn(
            "<url>file://${env.COGNERIS_MAVEN_REPOSITORY}</url>",
            section,
            "Every Cogneris Maven dependency must be bound to the explicit local repository",
        )
        test_case.assertIn("cogneris-document-ai-sdk-0.1.0.jar", section)
        test_case.assertIn("cogneris-document-ai-sdk-0.1.0.pom", section)


def assert_documented_local_package_sources(test_case, readme):
    assert_no_unbound_package_install_guidance(test_case, readme)
    dotnet = re.search(r"^## \.NET 8.*?(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL)
    test_case.assertIsNotNone(dotnet, "README must have a .NET 8 section")
    dotnet_commands = re.findall(
        r"^dotnet add package Cogneris\.DocumentAI[^\n]*$",
        dotnet.group(0),
        re.MULTILINE,
    )
    test_case.assertTrue(dotnet_commands, "README must show local NuGet installation")
    test_case.assertTrue(
        all('--source "$COGNERIS_RELEASE"' in command for command in dotnet_commands),
        "Every dotnet add command must bind the exact local release source",
    )

    java = re.search(r"^## Java 17.*?(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL)
    test_case.assertIsNotNone(java, "README must have a Java 17 section")
    for term in (
        "COGNERIS_MAVEN_REPOSITORY",
        "cogneris-document-ai-sdk-0.1.0.jar",
        "cogneris-document-ai-sdk-0.1.0.pom",
        "<dependency>",
        "<repository>",
        "file://${env.COGNERIS_MAVEN_REPOSITORY}",
    ):
        test_case.assertIn(term, java.group(0), f"Java guidance lacks local source binding: {term}")


class DocumentationContractTests(unittest.TestCase):
    def test_readme_is_the_complete_truthful_quickstart(self):
        readme = (ROOT / "README.md").read_text().lower()
        required_terms = (
            "@cogneris-ai/document-ai-sdk",
            "cogneris-document-ai-sdk",
            "@cogneris-ai/document-ai-cli",
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
            "available on maven central",
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
        self.assertIn("security/advisories/new", support)
        self.assertIn("privately report", support)
        self.assertNotIn("does not yet", support)
        for term in ("semantic versioning", "2026-08-07", "deprecation", "openapi"):
            self.assertIn(term, versioning)
        self.assertIn("published on maven central", versioning)
        self.assertIn("public artifact integrity", versioning)

    def test_readme_documents_csharp_and_java_from_explicit_local_sources(self):
        readme = (ROOT / "README.md").read_text()
        for term in (
            "Cogneris.DocumentAI",
            "net8.0",
            ".NET 8",
            "Cogneris.DocumentAI.0.1.0.nupkg",
            "ai.cogneris:cogneris-document-ai-sdk",
            "Java 17",
            "cogneris-document-ai-sdk-0.1.0.jar",
            "cogneris-document-ai-sdk-0.1.0.pom",
            "is available on Maven Central",
        ):
            self.assertIn(term, readme, f"README is missing C#/Java term: {term}")

        assert_documented_local_package_sources(self, readme)
        for relative in ("RELEASING.md", "VERSIONING.md", "SUPPORT.md"):
            assert_no_unbound_package_install_guidance(
                self,
                (ROOT / relative).read_text(),
            )

    def test_local_source_guard_rejects_registry_and_unbound_install_guidance(self):
        readme = (ROOT / "README.md").read_text()
        mutations = {
            "public Maven dependency uses an unverified version": readme.replace(
                "<version>0.1.0</version>", "<version>0.2.0</version>", 1,
            ),
            "public Maven dependency lacks the verified registry link": readme.replace(
                "https://repo.maven.apache.org/maven2/ai/cogneris/cogneris-document-ai-sdk/0.1.0/",
                "https://example.invalid/unverified", 1,
            ),
            "NuGet.org presented as the package source": readme.replace(
                '--source "$COGNERIS_RELEASE"',
                "--source https://api.nuget.org/v3/index.json",
                1,
            ),
            "bare dotnet install outside the named section": readme + """

## Accidental C# appendix

```bash
dotnet add package Cogneris.DocumentAI --version 0.1.0
```
""",
            "unbound Maven dependency outside the named section": readme + """

## Accidental Java appendix

```xml
<dependency>
  <groupId>ai.cogneris</groupId>
  <artifactId>cogneris-document-ai-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```
""",
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label):
                with self.assertRaises(AssertionError):
                    assert_documented_local_package_sources(self, mutated)

    def test_java_first_result_has_a_concrete_package_only_compile_and_run_path(self):
        readme = (ROOT / "README.md").read_text()
        java = re.search(r"^## Java 17.*?(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(java, "README must have a Java 17 section")
        for term in (
            "Apache Maven 3.9",
            '<maven.compiler.release>17</maven.compiler.release>',
            'mkdir -p "$COGNERIS_JAVA_CONSUMER/src/main/java"',
            '"$COGNERIS_JAVA_CONSUMER/src/main/java/Quickstart.java"',
            "mvn --batch-mode compile dependency:build-classpath",
            "-Dmdep.outputFile=target/runtime-classpath.txt",
            'java -cp "target/classes:$COGNERIS_JAVA_CLASSPATH" Quickstart extract',
        ):
            self.assertIn(term, java.group(0), f"Java first-result path is missing: {term}")

    def test_release_documents_exact_five_family_six_file_dry_run(self):
        releasing = (ROOT / "RELEASING.md").read_text()
        for term in (
            "five package families",
            "six package files",
            "cogneris-ai-document-ai-sdk-0.1.0.tgz",
            "cogneris-ai-document-ai-cli-0.1.0.tgz",
            "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl",
            "Cogneris.DocumentAI.0.1.0.nupkg",
            "cogneris-document-ai-sdk-0.1.0.jar",
            "cogneris-document-ai-sdk-0.1.0.pom",
            "full JDK 17 with `javac`",
            "not a full compiler JDK",
            "No repository workflow publishes to NuGet or Maven Central",
        ):
            self.assertIn(term, releasing, f"Release policy is missing: {term}")

    def test_csharp_and_java_examples_cover_the_public_facades(self):
        csharp_path = ROOT / "examples/dotnet/Quickstart.cs"
        java_path = ROOT / "examples/java/Quickstart.java"
        self.assertTrue(csharp_path.is_file(), "C# facade example is missing")
        self.assertTrue(java_path.is_file(), "Java facade example is missing")
        csharp = csharp_path.read_text()
        java = java_path.read_text()
        for term in (
            "CognerisRegion.Us",
            "CognerisRegion.Eu",
            "ExtractAsync",
            "SubmitJobAsync",
            "GetJobAsync",
            "WaitForJobAsync",
            "CancelJobAsync",
        ):
            self.assertIn(term, csharp, f"C# example does not exercise facade member: {term}")
        for term in (
            "CognerisClient.Region.US",
            "CognerisClient.Region.EU",
            ".extract(",
            ".submitJob(",
            ".getJob(",
            ".waitForJob(",
            ".cancelJob(",
        ):
            self.assertIn(term, java, f"Java example does not exercise facade member: {term}")

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
            checkout = temporary / "checkout"
            release = temporary / "release"
            consumer = temporary / "consumer"
            ignored = shutil.ignore_patterns(
                "dist", "node_modules", ".venv", "__pycache__", ".ruff_cache"
            )
            shutil.copytree(ROOT / "sdks", checkout / "sdks", ignore=ignored)
            shutil.copytree(ROOT / "cli", checkout / "cli", ignore=ignored)
            shutil.copytree(ROOT / "examples", checkout / "examples", ignore=ignored)
            (checkout / "package.json").write_text('{"private":true}\n')
            release.mkdir()

            sentinel_contents = b"pre-existing-build-output-must-survive\x00\xff"
            sdk_sentinel = checkout / "sdks/typescript/dist/pre-existing-sentinel.bin"
            cli_sentinel = checkout / "cli/dist/pre-existing-sentinel.bin"
            sdk_sentinel.parent.mkdir(parents=True)
            cli_sentinel.parent.mkdir(parents=True)
            sdk_sentinel.write_bytes(sentinel_contents)
            cli_sentinel.write_bytes(sentinel_contents)

            typescript = ROOT / "node_modules/.bin/tsc"
            subprocess.run(
                [str(typescript), "-p", str(checkout / "sdks/typescript/tsconfig.json")],
                cwd=checkout / "sdks/typescript",
                check=True,
                capture_output=True,
                text=True,
            )
            sdk_tarball = subprocess.run(
                [
                    "npm", "pack", "./sdks/typescript", "--pack-destination",
                    str(release), "--silent",
                ],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip().splitlines()[-1]
            subprocess.run(
                [
                    "npm", "install", "--ignore-scripts", "--no-audit", "--no-fund",
                    "--no-save", str(release / sdk_tarball),
                ],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    str(typescript), "-p", str(checkout / "cli/tsconfig.json"),
                    "--typeRoots", str(ROOT / "node_modules/@types"),
                ],
                cwd=checkout / "cli",
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["npm", "pack", "./cli", "--pack-destination", str(release), "--silent"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", str(release)],
                cwd=checkout / "sdks/python",
                check=True,
                capture_output=True,
                text=True,
            )

            environment = dict(os.environ)
            environment.update(
                {
                    "COGNERIS_CHECKOUT": str(checkout),
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

            self.assertEqual(sdk_sentinel.read_bytes(), sentinel_contents)
            self.assertEqual(cli_sentinel.read_bytes(), sentinel_contents)


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
