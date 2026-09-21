import hashlib
import importlib.util
import io
import email.parser
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sdk-release.py"


def release_module():
    spec = importlib.util.spec_from_file_location("sdk_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolFailureTests(unittest.TestCase):
    def test_failed_tools_report_categories_without_output_or_environment_data(self):
        release = release_module()
        cases = {
            "unable to create native thread": "native-thread-limit",
            "Gradle build daemon disappeared unexpectedly": "gradle-daemon-disappeared",
            "Could not resolve all files for configuration": "dependency-resolution",
            "There were failing tests": "test-failure",
            "java.lang.OutOfMemoryError: Java heap space": "memory-limit",
            "Compilation failed": "compilation-failure",
            "No space left on device": "disk-limit",
            "unrecognized failure": "unknown",
        }
        sentinel = "PRIVATE_DIAGNOSTIC_TEST_VALUE"
        for message, category in cases.items():
            with self.subTest(category=category):
                environment = dict(os.environ, DIAGNOSTIC_TEST_SECRET=sentinel,
                                   DIAGNOSTIC_TEST_FAILURE=message)
                with self.assertRaises((ValueError, subprocess.CalledProcessError)) as caught:
                    release.run([
                        sys.executable, "-c",
                        "import os,sys; print(os.environ['DIAGNOSTIC_TEST_SECRET']); "
                        "print(os.environ['DIAGNOSTIC_TEST_FAILURE'], file=sys.stderr); sys.exit(17)",
                    ], env=environment)
                diagnostic = str(caught.exception)
                self.assertIn("exit 17", diagnostic)
                self.assertIn(category, diagnostic)
                self.assertNotIn(sentinel, diagnostic)
                self.assertNotIn(message, diagnostic)
                self.assertNotIn("import os", diagnostic)


class ArchiveResourceTests(unittest.TestCase):
    """Real compressed fixtures use small chunks, never huge in-memory payloads."""

    def make_archive(self, file, entries):
        if file.suffix == ".tgz":
            class Spaces:
                def read(self, size):
                    return b" " * size

            with tarfile.open(file, "w:gz", format=tarfile.USTAR_FORMAT) as archive:
                encoded = b'{"name":"test-package","version":"0.1.0"}'
                header = tarfile.TarInfo("package/package.json")
                header.size = len(encoded)
                archive.addfile(header, io.BytesIO(encoded))
                for name, size in entries:
                    header = tarfile.TarInfo(name)
                    header.size = size
                    archive.addfile(header, Spaces())
        else:
            with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("test-0.1.0.dist-info/METADATA", "Name: test-package\nVersion: 0.1.0\n")
                for name, size in entries:
                    with archive.open(name, "w") as member:
                        for offset in range(0, size, 65536):
                            member.write(b" " * min(65536, size - offset))

    def test_archives_reject_compressed_byte_limits_before_opening(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-archive-size-") as directory:
            for suffix in (".tgz", ".whl"):
                with self.subTest(suffix=suffix):
                    file = Path(directory) / ("oversized" + suffix)
                    # Valid archives with sparse unused space stay tiny on disk.
                    # The guard must reject them before archive parsing.
                    if suffix == ".tgz":
                        self.make_archive(file, [])
                        with file.open("r+b") as stream:
                            stream.truncate(16 * 1024 * 1024 + 1)
                    else:
                        with file.open("wb") as stream:
                            stream.seek(16 * 1024 * 1024)
                            with zipfile.ZipFile(stream, "w") as archive:
                                archive.writestr("test.dist-info/METADATA", "Name: test\nVersion: 0.1.0\n")
                    with self.assertRaisesRegex(ValueError, "archive.*limit"):
                        release.package_metadata(file)

    def test_archives_bound_entry_count_and_compressed_expansion(self):
        release = release_module()
        cases = {
            "entries": [(f"package/entry-{index}", 0) for index in range(4096)],
            "entry expansion": [("package/expanded", 4 * 1024 * 1024 + 1)],
            "total expansion": [(f"package/entry-{index}", 4 * 1024 * 1024) for index in range(9)],
        }
        with tempfile.TemporaryDirectory(prefix="cogneris-archive-bounds-") as directory:
            for suffix in (".tgz", ".whl"):
                for label, entries in cases.items():
                    with self.subTest(suffix=suffix, case=label):
                        file = Path(directory) / (label + suffix)
                        self.make_archive(file, entries)
                        self.assertLess(file.stat().st_size, 512 * 1024)
                        with self.assertRaisesRegex(ValueError, "archive.*limit"):
                            release.package_metadata(file)

    def test_package_metadata_and_zip_name_sizes_are_bounded(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-archive-metadata-") as directory:
            for suffix in (".tgz", ".whl"):
                with self.subTest(suffix=suffix):
                    file = Path(directory) / ("metadata" + suffix)
                    if suffix == ".tgz":
                        payload = b'{"name":"test"}' + b" " * (64 * 1024)
                        with tarfile.open(file, "w:gz") as archive:
                            header = tarfile.TarInfo("package/package.json")
                            header.size = len(payload)
                            archive.addfile(header, io.BytesIO(payload))
                    else:
                        with zipfile.ZipFile(file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                            archive.writestr("test.dist-info/METADATA", b"Name: test\n" + b" " * (64 * 1024))
                    with self.assertRaisesRegex(ValueError, "archive.*limit"):
                        release.package_metadata(file)
            file = Path(directory) / "long-name.whl"
            self.make_archive(file, [("x" * 1025, 0)])
            with self.assertRaisesRegex(ValueError, "archive.*limit"):
                release.package_metadata(file)

    def test_zip_directory_and_comment_are_bounded_before_metadata_parsing(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-zip-metadata-") as directory:
            for label in ("directory", "count", "comment"):
                with self.subTest(case=label):
                    file = Path(directory) / (label + ".whl")
                    entries = [(f"package/{index}-" + "x" * 500, 0) for index in range(2000)] if label == "directory" else []
                    self.make_archive(file, entries)
                    data = bytearray(file.read_bytes())
                    end = data.rfind(b"PK\x05\x06")
                    if label == "count":
                        struct.pack_into("<HH", data, end + 8, 4097, 4097)
                    elif label == "comment":
                        struct.pack_into("<H", data, end + 20, 4097)
                        data.extend(b"x" * 4097)
                    file.write_bytes(data)
                    with self.assertRaisesRegex(ValueError, "archive.*limit"):
                        release.package_metadata(file)

    def test_zip64_records_are_rejected_before_zipfile_parsing(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-zip64-") as directory:
            file = Path(directory) / "zip64.whl"
            self.make_archive(file, [])
            data = bytearray(file.read_bytes())
            end = data.rfind(b"PK\x05\x06")
            directory_size = struct.unpack_from("<I", data, end + 12)[0]
            struct.pack_into("<I", data, end + 12, directory_size + 20)
            data[end:end] = b"PK\x06\x07" + b"\0" * 16
            file.write_bytes(data)

            with self.assertRaisesRegex(ValueError, "ZIP64"):
                release.inspect_zip_directory(file)

    def test_file_directory_collisions_are_rejected_in_both_orders(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-archive-collision-") as directory:
            for suffix in (".tgz", ".whl"):
                for names in (("package/a", "package/a/b"), ("package/a/b", "package/a")):
                    with self.subTest(suffix=suffix, names=names):
                        file = Path(directory) / ("collision" + suffix)
                        self.make_archive(file, [(name, 0) for name in names])
                        with self.assertRaisesRegex(ValueError, "collision"):
                            release.package_metadata(file)

    def test_zip_rejects_codecs_outside_the_stored_deflate_resource_policy(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-zip-compression-") as directory:
            for compression in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
                with self.subTest(compression=compression):
                    file = Path(directory) / f"compression-{compression}.whl"
                    with zipfile.ZipFile(file, "w", compression=compression) as archive:
                        archive.writestr("test.dist-info/METADATA", "Name: test\nVersion: 0.1.0\n")
                    with self.assertRaisesRegex(ValueError, "archive.*compression"):
                        release.package_metadata(file)


def clean_checkout(directory):
    """Commit current tracked test inputs in a private repository; never edit ROOT."""
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for name in filter(None, tracked):
        destination = directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    subprocess.run(["git", "init", "-q", "-b", "codex/release-fixture"], cwd=directory, check=True)
    subprocess.run(["git", "add", "."], cwd=directory, check=True)
    subprocess.run(["git", "-c", "user.name=Release tests", "-c", "user.email=release-tests@example.invalid",
                    "-c", "core.hooksPath=/dev/null", "commit", "--no-gpg-sign", "-qm", "Clean release fixture"],
                   cwd=directory, check=True)
    (directory / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
    return directory


def fixture_bundle(directory, tar_member=None, zip_member=None, licensed=True):
    """Self-consistent untrusted archives: no installation or package code execution."""
    directory.mkdir()
    license_contents = (ROOT / "LICENSE").read_bytes()
    notice_contents = (ROOT / "NOTICE").read_bytes()
    for kind in ("sdk", "cli"):
        metadata = {"name": f"@cogneris-ai/document-ai-{kind}", "version": "0.1.0"}
        if licensed:
            metadata["license"] = "Apache-2.0"
        if kind == "cli":
            metadata["dependencies"] = {"@cogneris-ai/document-ai-sdk": "0.1.0"}
        with tarfile.open(directory / f"cogneris-ai-document-ai-{kind}-0.1.0.tgz", "w:gz") as archive:
            encoded = json.dumps(metadata).encode()
            member = tarfile.TarInfo("package/package.json")
            member.size = len(encoded)
            archive.addfile(member, io.BytesIO(encoded))
            if licensed:
                for name, contents in (("LICENSE", license_contents), ("NOTICE", notice_contents)):
                    member = tarfile.TarInfo(f"package/{name}")
                    member.size = len(contents)
                    archive.addfile(member, io.BytesIO(contents))
            if kind == "sdk" and tar_member is not None:
                archive.addfile(tar_member, io.BytesIO(b""))
    with zipfile.ZipFile(directory / "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl", "w") as archive:
        license_metadata = "License-Expression: Apache-2.0\n" if licensed else ""
        archive.writestr("cogneris_document_ai_sdk-0.1.0.dist-info/METADATA",
                         f"Name: cogneris-document-ai-sdk\nVersion: 0.1.0\n{license_metadata}")
        if licensed:
            archive.writestr("cogneris_document_ai_sdk-0.1.0.dist-info/licenses/LICENSE", license_contents)
            archive.writestr("cogneris_document_ai_sdk-0.1.0.dist-info/licenses/NOTICE", notice_contents)
        if zip_member is not None:
            archive.writestr(zip_member, b"")
    nuspec = b"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Cogneris.DocumentAI</id><version>0.1.0</version><authors>COGNERIS, INC.</authors>
    <license type="expression">Apache-2.0</license>
  </metadata>
</package>
"""
    with zipfile.ZipFile(directory / "Cogneris.DocumentAI.0.1.0.nupkg", "w") as archive:
        archive.writestr("Cogneris.DocumentAI.nuspec", nuspec)
        if licensed:
            archive.writestr("LICENSE", license_contents)
            archive.writestr("NOTICE", notice_contents)
    class_bytes = b"\xca\xfe\xba\xbe\x00\x00\x00\x3d"
    with zipfile.ZipFile(directory / "cogneris-document-ai-sdk-0.1.0.jar", "w") as archive:
        if licensed:
            archive.writestr("META-INF/LICENSE", license_contents)
            archive.writestr("META-INF/NOTICE", notice_contents)
        for facade in (
            "CognerisClient", "CognerisException", "CognerisApiException",
            "CognerisTransportException", "CognerisResponseException",
            "CognerisJobTerminalException", "CognerisMaxAttemptsException",
        ):
            archive.writestr(f"ai/cogneris/documentai/{facade}.class", class_bytes)
    (directory / "cogneris-document-ai-sdk-0.1.0.pom").write_text("""\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>ai.cogneris</groupId><artifactId>cogneris-document-ai-sdk</artifactId><version>0.1.0</version>
  <licenses><license><name>Apache-2.0</name><url>https://www.apache.org/licenses/LICENSE-2.0</url></license></licenses>
</project>
""")
    manifest = {"version": "0.1.0", "source": "a" * 40,
                "files": {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in directory.iterdir()}}
    encoded = json.dumps(manifest).encode()
    (directory / "manifest.json").write_bytes(encoded)
    return ["--version", "0.1.0", "--artifacts", str(directory),
            "--manifest-sha256", hashlib.sha256(encoded).hexdigest(), "--source", "a" * 40]


class ReleaseArtifactTests(unittest.TestCase):
    def invoke(self, *arguments, environment=None):
        self.assertTrue(SCRIPT.is_file(), "missing release artifact builder/verifier")
        checkout = getattr(self, "checkout", ROOT)
        return subprocess.run([sys.executable, str(checkout / "scripts/sdk-release.py"), *arguments], cwd=checkout,
                              env=environment, text=True, capture_output=True)

    def test_version_gate_rejects_missing_malformed_and_mismatched_versions(self):
        for version in ("", "v0.1.0", "01.1.0", "0.1", "0.1.0;false", "0.2.0"):
            with self.subTest(version=version):
                result = self.invoke("check-version", "--version", version)
                self.assertNotEqual(result.returncode, 0)
        result = self.invoke("check-version", "--version", "0.1.0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_integrity_gate_rejects_artifacts_without_the_approved_license(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-unlicensed-release-") as directory:
            arguments = fixture_bundle(Path(directory) / "artifacts", licensed=False)
            result = self.invoke("verify", *arguments, "--integrity-only")
            self.assertNotEqual(result.returncode, 0, "unlicensed release artifacts must be rejected")
            self.assertIn("license", result.stderr.lower())

    def test_xml_metadata_rejects_entities_and_oversized_sidecars_before_parsing(self):
        release = release_module()
        entity_xml = b"""<!DOCTYPE project [<!ENTITY leak SYSTEM "file:///etc/passwd">]>
<project xmlns="http://maven.apache.org/POM/4.0.0"><groupId>&leak;</groupId></project>"""
        with tempfile.TemporaryDirectory(prefix="cogneris-release-xml-") as directory:
            root = Path(directory)
            pom = root / "cogneris-document-ai-sdk-0.1.0.pom"
            pom.write_bytes(entity_xml)
            with self.assertRaisesRegex(ValueError, "XML declaration"):
                release.package_metadata(pom)
            package = root / "Cogneris.DocumentAI.0.1.0.nupkg"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("Cogneris.DocumentAI.nuspec", entity_xml)
            with self.assertRaisesRegex(ValueError, "XML declaration"):
                release.package_metadata(package)
            wrong_pom_namespace = b"""\
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:e="https://example.invalid">
  <e:groupId>ai.cogneris</e:groupId><e:artifactId>cogneris-document-ai-sdk</e:artifactId><e:version>0.1.0</e:version>
  <e:licenses><e:license><e:name>Apache-2.0</e:name><e:url>https://www.apache.org/licenses/LICENSE-2.0</e:url></e:license></e:licenses>
</project>"""
            pom.write_bytes(wrong_pom_namespace)
            with self.assertRaisesRegex(ValueError, "Maven POM"):
                release.package_metadata(pom)
            wrong_nuspec_namespace = b"""\
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd" xmlns:e="https://example.invalid">
  <e:metadata><e:id>Cogneris.DocumentAI</e:id><e:version>0.1.0</e:version>
    <e:authors>COGNERIS, INC.</e:authors><e:license type="expression">Apache-2.0</e:license></e:metadata>
</package>"""
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("Cogneris.DocumentAI.nuspec", wrong_nuspec_namespace)
                archive.writestr("LICENSE", (ROOT / "LICENSE").read_bytes())
                archive.writestr("NOTICE", (ROOT / "NOTICE").read_bytes())
            with self.assertRaisesRegex(ValueError, "NuGet package metadata"):
                release.package_metadata(package)
            expansion = "x" * 10_000
            pom_text = f"""<?xml version="1.0" encoding="UTF-16"?>
<!DOCTYPE project [<!ENTITY payload "{expansion}">]>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <groupId>&payload;</groupId><artifactId>cogneris-document-ai-sdk</artifactId><version>0.1.0</version>
  <licenses><license><name>Apache-2.0</name><url>https://www.apache.org/licenses/LICENSE-2.0</url></license></licenses>
</project>"""
            nuspec_text = f"""<?xml version="1.0" encoding="UTF-16"?>
<!DOCTYPE package [<!ENTITY payload "{expansion}">]>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata><id>&payload;</id><version>0.1.0</version><authors>COGNERIS, INC.</authors>
    <license type="expression">Apache-2.0</license></metadata>
</package>"""
            for encoding, byte_order_mark in (
                ("utf-16-le", b"\xff\xfe"), ("utf-16-be", b"\xfe\xff")
            ):
                with self.subTest(encoding=encoding, artifact="pom"):
                    pom.write_bytes(byte_order_mark + pom_text.encode(encoding))
                    with self.assertRaisesRegex(ValueError, "XML encoding"):
                        release.package_metadata(pom)
                with self.subTest(encoding=encoding, artifact="nuspec"):
                    with zipfile.ZipFile(package, "w") as archive:
                        archive.writestr(
                            "Cogneris.DocumentAI.nuspec",
                            byte_order_mark + nuspec_text.encode(encoding),
                        )
                        archive.writestr("LICENSE", (ROOT / "LICENSE").read_bytes())
                        archive.writestr("NOTICE", (ROOT / "NOTICE").read_bytes())
                    with self.assertRaisesRegex(ValueError, "XML encoding"):
                        release.package_metadata(package)
            pom.write_bytes(b" " * (64 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "metadata.*limit"):
                release.package_metadata(pom)

    def test_nuget_install_proof_rejects_non_package_and_byte_mismatch(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-nuget-proof-") as directory:
            root = Path(directory)
            staged = root / "Cogneris.DocumentAI.0.1.0.nupkg"
            staged.write_bytes(b"approved built package")
            cache = root / "cache"
            relative = "cogneris.documentai/0.1.0"
            installed = cache / relative / "cogneris.documentai.0.1.0.nupkg"
            installed.parent.mkdir(parents=True)
            installed.write_bytes(staged.read_bytes())
            assets = root / "project.assets.json"

            def write_assets(kind):
                assets.write_text(json.dumps({
                    "libraries": {
                        "Cogneris.DocumentAI/0.1.0": {"type": kind, "path": relative},
                    },
                }))

            write_assets("package")
            release.verify_nuget_install(assets, cache, staged, "Cogneris.DocumentAI", "0.1.0")
            write_assets("project")
            with self.assertRaisesRegex(ValueError, "package-only"):
                release.verify_nuget_install(assets, cache, staged, "Cogneris.DocumentAI", "0.1.0")
            write_assets("package")
            installed.write_bytes(b"different package bytes")
            with self.assertRaisesRegex(ValueError, "digest"):
                release.verify_nuget_install(assets, cache, staged, "Cogneris.DocumentAI", "0.1.0")

    def test_nuget_source_mapping_reserves_cogneris_for_the_staged_feed(self):
        release = release_module()
        with tempfile.TemporaryDirectory(prefix="cogneris-nuget-config-") as directory:
            root = Path(directory)
            staged = root / "staged"
            staged.mkdir()
            config = root / "NuGet.config"
            release.write_nuget_config(config, staged)
            tree = ET.parse(config)
            sources = {
                item.attrib["key"]: item.attrib["value"]
                for item in tree.findall("./packageSources/add")
            }
            self.assertEqual(sources, {
                "cogneris-staged": str(staged),
                "nuget.org": "https://api.nuget.org/v3/index.json",
            })
            mappings = {
                source.attrib["key"]: {package.attrib["pattern"] for package in source}
                for source in tree.findall("./packageSourceMapping/packageSource")
            }
            self.assertEqual(mappings, {
                "cogneris-staged": {"Cogneris.DocumentAI"},
                "nuget.org": {"Microsoft.*", "Polly", "Polly.*", "System.*"},
            })

    def test_built_artifacts_carry_the_approved_apache_license_and_notice(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-license-test-") as directory:
            self.checkout = clean_checkout(Path(directory) / "checkout")
            license_file = self.checkout / "LICENSE"
            notice_file = self.checkout / "NOTICE"
            self.assertTrue(license_file.is_file(), "repository must carry the approved Apache-2.0 text")
            self.assertTrue(notice_file.is_file(), "repository must carry the approved Cogneris notice")
            approved_license = license_file.read_bytes()
            approved_notice = notice_file.read_bytes()

            output = Path(directory) / "artifacts"
            result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            for package in ("sdk", "cli"):
                with self.subTest(package=package):
                    archive = output / f"cogneris-ai-document-ai-{package}-0.1.0.tgz"
                    with tarfile.open(archive, "r:gz") as contents:
                        metadata = json.load(contents.extractfile("package/package.json"))
                        self.assertEqual(metadata["license"], "Apache-2.0")
                        self.assertIn("package/LICENSE", contents.getnames())
                        self.assertIn("package/NOTICE", contents.getnames())
                        self.assertEqual(contents.extractfile("package/LICENSE").read(), approved_license)
                        self.assertEqual(contents.extractfile("package/NOTICE").read(), approved_notice)

            wheel = output / "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl"
            with zipfile.ZipFile(wheel) as contents:
                metadata_name = next(name for name in contents.namelist() if name.endswith(".dist-info/METADATA"))
                metadata = email.parser.BytesParser().parsebytes(contents.read(metadata_name))
                self.assertEqual(metadata["License-Expression"], "Apache-2.0")
                licenses = {
                    name.rsplit("/", 1)[-1]: contents.read(name)
                    for name in contents.namelist()
                    if ".dist-info/licenses/" in name and not name.endswith("/")
                }
                self.assertEqual(licenses, {"LICENSE": approved_license, "NOTICE": approved_notice})

            package = output / "Cogneris.DocumentAI.0.1.0.nupkg"
            with zipfile.ZipFile(package) as contents:
                nuspecs = [name for name in contents.namelist() if name.endswith(".nuspec")]
                self.assertEqual(nuspecs, ["Cogneris.DocumentAI.nuspec"])
                nuspec = ET.fromstring(contents.read(nuspecs[0]))
                self.assertEqual(nuspec.findtext(".//{*}id"), "Cogneris.DocumentAI")
                self.assertEqual(nuspec.findtext(".//{*}version"), "0.1.0")
                self.assertEqual(nuspec.findtext(".//{*}authors"), "COGNERIS, INC.")
                license_metadata = nuspec.find(".//{*}license")
                self.assertIsNotNone(license_metadata)
                self.assertEqual(license_metadata.attrib, {"type": "expression"})
                self.assertEqual(license_metadata.text, "Apache-2.0")
                self.assertEqual(contents.read("LICENSE"), approved_license)
                self.assertEqual(contents.read("NOTICE"), approved_notice)

            jar = output / "cogneris-document-ai-sdk-0.1.0.jar"
            with zipfile.ZipFile(jar) as contents:
                self.assertEqual(contents.read("META-INF/LICENSE"), approved_license)
                self.assertEqual(contents.read("META-INF/NOTICE"), approved_notice)
                for facade in (
                    "CognerisClient", "CognerisException", "CognerisApiException",
                    "CognerisTransportException", "CognerisResponseException",
                    "CognerisJobTerminalException", "CognerisMaxAttemptsException",
                ):
                    class_file = f"ai/cogneris/documentai/{facade}.class"
                    self.assertIn(class_file, contents.namelist())
                    bytecode = contents.read(class_file)
                    self.assertEqual(bytecode[:4], b"\xca\xfe\xba\xbe")
                    self.assertEqual(int.from_bytes(bytecode[6:8], "big"), 61)

            pom = ET.parse(output / "cogneris-document-ai-sdk-0.1.0.pom")
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            self.assertEqual(pom.findtext("m:groupId", namespaces=ns), "ai.cogneris")
            self.assertEqual(pom.findtext("m:artifactId", namespaces=ns), "cogneris-document-ai-sdk")
            self.assertEqual(pom.findtext("m:version", namespaces=ns), "0.1.0")
            self.assertEqual(pom.findtext("m:licenses/m:license/m:name", namespaces=ns), "Apache-2.0")
            self.assertEqual(
                pom.findtext("m:licenses/m:license/m:url", namespaces=ns),
                "https://www.apache.org/licenses/LICENSE-2.0",
            )

    def test_real_artifacts_install_and_reject_tampering_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-release-test-") as directory:
            self.checkout = clean_checkout(Path(directory) / "checkout")
            output = Path(directory) / "artifacts"
            result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest_bytes = (output / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            digest = hashlib.sha256(manifest_bytes).hexdigest()
            self.assertEqual(set(manifest["files"]), {
                "cogneris-ai-document-ai-sdk-0.1.0.tgz", "cogneris-ai-document-ai-cli-0.1.0.tgz",
                "cogneris_document_ai_sdk-0.1.0-py3-none-any.whl",
                "Cogneris.DocumentAI.0.1.0.nupkg",
                "cogneris-document-ai-sdk-0.1.0.jar",
                "cogneris-document-ai-sdk-0.1.0.pom",
            })
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

            for artifact_name in manifest["files"]:
                with self.subTest(tampered_artifact=artifact_name):
                    tampered = output / artifact_name
                    original = tampered.read_bytes()
                    tampered.write_bytes(original + b"tampered")
                    result = self.invoke("verify", *arguments)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("digest", result.stderr.lower())
                    tampered.write_bytes(original)

            artifact = output / "cogneris-ai-document-ai-sdk-0.1.0.tgz"
            original = artifact.read_bytes()
            # A self-consistent checksum is insufficient if package metadata lies.
            with tarfile.open(artifact, "w:gz") as archive:
                encoded = json.dumps({"name": "@cogneris-ai/document-ai-sdk", "version": "9.9.9",
                                      "license": "Apache-2.0"}).encode()
                member = tarfile.TarInfo("package/package.json")
                member.size = len(encoded)
                archive.addfile(member, io.BytesIO(encoded))
                for name in ("LICENSE", "NOTICE"):
                    contents = (ROOT / name).read_bytes()
                    member = tarfile.TarInfo(f"package/{name}")
                    member.size = len(contents)
                    archive.addfile(member, io.BytesIO(contents))
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
                       SDK_PYPI_TRUSTED_PUBLISHING_READY="true", GITHUB_REPOSITORY="cogneris-ai/not-the-repo")
            result = self.invoke("check-publish", *arguments, "--registry", "npm", environment=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("repository", result.stderr.lower())

    def test_archive_gate_rejects_unsafe_paths_links_devices_and_duplicates_without_extracting(self):
        paths = ("/absolute", "../escape", "package/../../escape", "package\\escape",
                 "C:/escape", "package/C:escape", "package//ambiguous", "package/./ambiguous")
        cases = []
        for name in paths:
            cases.append(("tar path " + name, tarfile.TarInfo(name), None))
            cases.append(("zip path " + name, None, zipfile.ZipInfo(name)))
        for name, kind in (("symlink", tarfile.SYMTYPE), ("hardlink", tarfile.LNKTYPE),
                           ("fifo", tarfile.FIFOTYPE), ("device", tarfile.CHRTYPE),
                           ("block", tarfile.BLKTYPE), ("unknown", b"Z")):
            member = tarfile.TarInfo("package/unsafe")
            member.type = kind
            if name in {"symlink", "hardlink"}:
                member.linkname = "../../escape"
            cases.append(("tar " + name, member, None))
        for name, mode in (("symlink", stat.S_IFLNK), ("fifo", stat.S_IFIFO), ("device", stat.S_IFCHR),
                           ("block", stat.S_IFBLK), ("socket", stat.S_IFSOCK)):
            member = zipfile.ZipInfo("unsafe")
            member.create_system = 3
            member.external_attr = (mode | 0o644) << 16
            cases.append(("zip " + name, None, member))
        # PKWARE Unix (0x000d) variable data can carry a hardlink target even for a regular file.
        member = zipfile.ZipInfo("hardlink")
        member.create_system = 3
        member.external_attr = (stat.S_IFREG | 0o644) << 16
        member.extra = struct.pack("<HH", 0x000d, 20) + b"\0" * 12 + b"../other"
        cases.append(("zip hardlink metadata", None, member))
        cases.append(("tar duplicate", tarfile.TarInfo("package/package.json"), None))
        cases.append(("zip case collision", None, zipfile.ZipInfo("COGNERIS_DOCUMENT_AI_SDK-0.1.0.dist-info/metadata")))
        with tempfile.TemporaryDirectory(prefix="cogneris-unsafe-archives-") as directory:
            for index, (label, tar_member, zip_member) in enumerate(cases):
                with self.subTest(archive=label):
                    arguments = fixture_bundle(Path(directory) / str(index), tar_member, zip_member)
                    result = self.invoke("verify", *arguments, "--integrity-only")
                    self.assertNotEqual(result.returncode, 0, "unsafe archive was accepted")
                    self.assertIn("unsafe archive", result.stderr.lower())
            self.assertFalse((Path(directory) / "escape").exists())

    def test_build_rejects_dirty_staged_deleted_and_untracked_packaged_inputs_before_packaging(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-dirty-release-") as directory:
            self.checkout = clean_checkout(Path(directory) / "checkout")
            cases = (("sdks/typescript/src/index.ts", "modified"),
                     ("sdks/python/README.md", "modified"),
                     ("cli/package.json", "staged"),
                     ("cli/package.json", "staged-only"),
                     ("sdks/typescript/src/index.ts", "assume-unchanged"),
                     ("sdks/python/CHANGELOG.md", "deleted"),
                     ("sdks/typescript/src/untracked.ts", "untracked"),
                     ("sdks/python/cogneris_document_ai_sdk/untracked.py", "untracked"),
                     ("package-lock.json", "modified"))
            for index, (name, mutation) in enumerate(cases):
                with self.subTest(path=name, mutation=mutation):
                    file = self.checkout / name
                    original = file.read_bytes() if file.exists() else None
                    if mutation == "deleted":
                        file.unlink()
                    else:
                        file.write_bytes((original or b"") + b"\n")
                    if mutation in {"staged", "staged-only"}:
                        subprocess.run(["git", "add", name], cwd=self.checkout, check=True)
                    if mutation == "staged-only":
                        file.write_bytes(original)
                    if mutation == "assume-unchanged":
                        subprocess.run(["git", "update-index", "--assume-unchanged", name], cwd=self.checkout, check=True)
                    output = Path(directory) / f"artifacts-{index}"
                    try:
                        result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("dirty or untracked build inputs", result.stderr.lower())
                        self.assertFalse(output.exists(), "dirty source must fail before artifact creation")
                    finally:
                        if original is None:
                            file.unlink()
                        else:
                            file.write_bytes(original)
                        if mutation == "assume-unchanged":
                            subprocess.run(["git", "update-index", "--no-assume-unchanged", name], cwd=self.checkout, check=True)
                        if mutation in {"staged", "staged-only"}:
                            subprocess.run(["git", "add", name], cwd=self.checkout, check=True)

    def test_tar_alternate_link_metadata_cannot_hide_in_a_regular_member(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-pax-link-") as directory:
            member = tarfile.TarInfo("package/alternate-link")
            member.pax_headers = {"SCHILY.filetype": "symlink", "SCHILY.linkpath": "../../escape"}
            arguments = fixture_bundle(Path(directory) / "artifacts", tar_member=member)
            result = self.invoke("verify", *arguments, "--integrity-only")
            self.assertNotEqual(result.returncode, 0, "alternate link metadata was accepted")
            self.assertIn("unsafe archive", result.stderr.lower())

    def test_build_preserves_and_ignores_unrelated_files_and_excluded_outputs(self):
        with tempfile.TemporaryDirectory(prefix="cogneris-clean-release-") as directory:
            self.checkout = clean_checkout(Path(directory) / "checkout")
            sentinels = [self.checkout / name for name in ("unrelated-note.txt", "cli/dist/sentinel", "sdks/python/__pycache__/sentinel")]
            for file in sentinels:
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b"unrelated pre-existing bytes")
            output = Path(directory) / "artifacts"
            result = self.invoke("build", "--version", "0.1.0", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((output / "manifest.json").read_text())["source"],
                             subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.checkout).decode().strip())
            for file in sentinels:
                self.assertEqual(file.read_bytes(), b"unrelated pre-existing bytes")


if __name__ == "__main__":
    unittest.main()
