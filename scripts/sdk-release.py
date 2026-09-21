"""Build once, verify exact package bytes, and fail closed before publication.

This helper never publishes and never reads publishing credentials. All package
builds and consumer installs use owned temporary directories.
"""
import argparse
import email.parser
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIRECTORIES = ("sdks/typescript", "sdks/python", "sdks/csharp", "sdks/java", "cli")
BUILD_FILES = ("LICENSE", "NOTICE", "package.json", "package-lock.json",
               "scripts/sdk-release.py", "scripts/run-java.py")
EXCLUDED_BUILD_NAMES = {"dist", "node_modules", ".venv", "__pycache__", ".ruff_cache"}
# Current packages are small source distributions. These limits bound parsing,
# hashing and decompression before any dependency installer sees the archives.
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 4096
MAX_ENTRY_BYTES = 4 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_METADATA_BYTES = 64 * 1024
MAX_NAME_BYTES = 1024
MAX_ZIP_DIRECTORY_BYTES = 1024 * 1024
MAX_COMMENT_BYTES = 4096
MAVEN_NAMESPACE = "http://maven.apache.org/POM/4.0.0"
NUGET_NAMESPACE = "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(arguments, cwd=ROOT, env=None, *, diagnostic_context="external"):
    require(diagnostic_context in {"external", "java-build", "java-consumer"},
            "unsupported diagnostic context")
    try:
        return subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env,
                              check=True, text=True, capture_output=True).stdout.strip()
    except subprocess.CalledProcessError as error:
        # Dependency output and command arguments can contain credentials. Only
        # emit fixed categories, never excerpts from the captured tool output.
        output = ((error.stdout or "") + "\n" + (error.stderr or "")).lower()
        patterns = {
            "native-thread-limit": ("unable to create native thread", "resource temporarily unavailable"),
            "gradle-daemon-disappeared": ("gradle build daemon disappeared",),
            "memory-limit": ("outofmemoryerror", "java heap space", "cannot allocate memory"),
            "dependency-resolution": ("could not resolve", "could not get resource", "could not get '"),
            "test-failure": ("there were failing tests",),
            "compilation-failure": ("compilation failed",),
            "disk-limit": ("no space left on device",),
            "network-timeout": ("timed out", "sockettimeoutexception"),
            "http-download-failure": ("server returned http response code", "http error",),
            "distribution-integrity": ("verification of gradle distribution failed",),
        }
        categories = [name for name, markers in patterns.items()
                      if any(marker in output for marker in markers)]
        category = ", ".join(categories) or "unknown"
        raise ValueError(f"{diagnostic_context} tool failed (exit {error.returncode}; {category})") from None


def digest(file):
    value = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            value.update(chunk)
    return value.hexdigest()


def parse_xml(contents):
    require(len(contents) <= MAX_METADATA_BYTES, "XML metadata size limit exceeded")
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("unsupported XML encoding; UTF-8 is required") from error
    require("\0" not in text, "unsupported XML encoding; UTF-8 is required")
    uppercase = text.upper()
    require("<!DOCTYPE" not in uppercase and "<!ENTITY" not in uppercase,
            "unsafe XML declaration is forbidden")
    try:
        return ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("invalid XML package metadata") from error


def one_xml_text(parent, path, message):
    elements = parent.findall(path)
    require(len(elements) == 1 and elements[0].text is not None, message)
    value = elements[0].text.strip()
    require(bool(value), message)
    return value


def source_versions(version):
    require(SEMVER.fullmatch(version), "version must be explicit SemVer without a v prefix")
    for package in (ROOT / "sdks/typescript/package.json", ROOT / "cli/package.json"):
        require(json.loads(package.read_text())["version"] == version,
                "package version does not exactly match release input")
    # Match the unique top-level project version; this fixed generated metadata
    # is also independently checked in the built wheel's standard METADATA.
    versions = re.findall(r'^version = "([^"]+)"$',
                          (ROOT / "sdks/python/pyproject.toml").read_text(), re.MULTILINE)
    require(versions == [version], "Python package version does not exactly match release input")
    csharp = parse_xml(
        (ROOT / "sdks/csharp/src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj").read_bytes()
    )
    require(one_xml_text(csharp, ".//Version", "invalid C# package version") == version,
            "C# package version does not exactly match release input")
    java = parse_xml((ROOT / "sdks/java/pom.xml").read_bytes())
    require(one_xml_text(java, f"{{{MAVEN_NAMESPACE}}}version", "invalid Java package version") == version,
            "Java package version does not exactly match release input")


def artifacts(version):
    return {
        f"cogneris-ai-document-ai-sdk-{version}.tgz": {
            "kind": "npm", "name": "@cogneris-ai/document-ai-sdk", "legal": True, "license": True,
        },
        f"cogneris-ai-document-ai-cli-{version}.tgz": {
            "kind": "npm", "name": "@cogneris-ai/document-ai-cli", "legal": True, "license": True,
        },
        f"cogneris_document_ai_sdk-{version}-py3-none-any.whl": {
            "kind": "wheel", "name": "cogneris-document-ai-sdk", "legal": True, "license": True,
        },
        f"Cogneris.DocumentAI.{version}.nupkg": {
            "kind": "nuget", "name": "Cogneris.DocumentAI", "legal": True, "license": True,
        },
        f"cogneris-document-ai-sdk-{version}.jar": {
            "kind": "java-jar", "legal": True, "license": False,
        },
        f"cogneris-document-ai-sdk-{version}.pom": {
            "kind": "maven-pom", "name": "ai.cogneris:cogneris-document-ai-sdk",
            "legal": False, "license": True,
        },
    }


def archive_path(name, directory, seen, ancestors):
    """Validate portable logical paths without normalizing away unsafe syntax."""
    require(len(name.encode("utf-8")) <= MAX_NAME_BYTES, "archive name size limit exceeded")
    logical = name[:-1] if directory and name.endswith("/") else name
    parts = logical.split("/")
    require(logical and not any(character in logical for character in ("\\", ":"))
            and all(ord(character) >= 32 and ord(character) != 127 for character in logical)
            and all(part not in {"", ".", ".."} and part.rstrip(". ") == part for part in parts),
            "unsafe archive path")
    folded = logical.casefold()
    require(folded not in seen, "unsafe archive duplicate or case-colliding path")
    parents = ["/".join(parts[:index]).casefold() for index in range(1, len(parts))]
    require(all(seen.get(parent) != "file" for parent in parents), "unsafe archive file/directory collision")
    require(directory or folded not in ancestors,
            "unsafe archive file/directory collision")
    seen[folded] = "directory" if directory else "file"
    # Each bounded-length name contributes its parents once. Avoid rescanning
    # all previous names for every entry (quadratic for large archives).
    ancestors.update(parents)


class BoundedTarInfo(tarfile.TarInfo):
    @classmethod
    def frombuf(cls, buf, encoding, errors):
        member = super().frombuf(buf, encoding, errors)
        # TarInfo processes PAX/GNU extension payloads while reading a header,
        # before callers can inspect the returned member. Reject at that boundary.
        require(member.type in {tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE},
                "unsafe archive non-regular tar member")
        require(0 <= member.size <= MAX_ENTRY_BYTES, "archive entry size limit exceeded")
        require(len(member.name.encode("utf-8")) <= MAX_NAME_BYTES, "archive name size limit exceeded")
        if member.name == "package/package.json":
            require(member.size <= MAX_METADATA_BYTES, "archive package metadata size limit exceeded")
        return member


def inspect_tar(archive):
    seen = {}
    ancestors = set()
    members = []
    total = 0
    for member in archive:
        require(len(members) < MAX_ARCHIVE_ENTRIES, "archive entry count limit exceeded")
        require(0 <= member.size <= MAX_ENTRY_BYTES, "archive entry size limit exceeded")
        total += member.size
        require(total <= MAX_TOTAL_UNCOMPRESSED_BYTES, "archive expanded size limit exceeded")
        directory = member.type == tarfile.DIRTYPE
        require((member.type in {tarfile.REGTYPE, tarfile.AREGTYPE} or directory)
                and member.sparse is None and not member.linkname and not member.pax_headers,
                "unsafe archive non-regular tar member")
        require(not directory or member.size == 0, "unsafe archive directory payload")
        archive_path(member.name, directory, seen, ancestors)
        require(member.name == "package/" or member.name.startswith("package/"),
                "unsafe archive npm root")
        members.append(member)
    return members


def inspect_zip_directory(file):
    # ZipFile reads the entire central directory at construction time. Inspect
    # its fixed footer first, before allocating directory bytes/ZipInfo objects.
    with file.open("rb") as stream:
        size = file.stat().st_size
        stream.seek(max(0, size - 65557))  # ZIP's 22-byte footer + uint16 comment
        tail = stream.read(65557)
    end = tail.rfind(b"PK\x05\x06")
    require(end >= 0 and len(tail) >= end + 22, "unsafe archive missing ZIP footer")
    # zipfile checks for a ZIP64 locator immediately before the classic footer
    # and may follow its offsets before returning control to our entry bounds.
    # Release wheels are deliberately small, so reject ZIP64 before constructing
    # ZipFile rather than trusting the classic footer's smaller declarations.
    require(end < 20 or tail[end - 20:end - 16] != b"PK\x06\x07",
            "unsafe archive ZIP64 directory")
    _, disk, directory_disk, disk_count, count, directory_size, offset, comment_size = struct.unpack(
        "<4s4H2IH", tail[end:end + 22])
    require(count <= MAX_ARCHIVE_ENTRIES, "archive entry count limit exceeded")
    require(directory_size <= MAX_ZIP_DIRECTORY_BYTES, "archive ZIP directory size limit exceeded")
    require(comment_size <= MAX_COMMENT_BYTES, "archive comment size limit exceeded")
    require(disk == directory_disk == 0 and disk_count == count,
            "unsafe archive multidisk or ZIP64 directory")
    require(end + 22 + comment_size == len(tail)
            and offset + directory_size == size - len(tail) + end,
            "unsafe archive inconsistent ZIP directory")


def inspect_zip(archive):
    seen = {}
    ancestors = set()
    members = archive.infolist()
    require(len(members) <= MAX_ARCHIVE_ENTRIES, "archive entry count limit exceeded")
    total = 0
    for member in members:
        require(member.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                "unsafe archive unsupported ZIP compression")
        require(0 <= member.file_size <= MAX_ENTRY_BYTES, "archive entry size limit exceeded")
        total += member.file_size
        require(total <= MAX_TOTAL_UNCOMPRESSED_BYTES, "archive expanded size limit exceeded")
        require(len(member.comment) <= MAX_COMMENT_BYTES, "archive comment size limit exceeded")
        mode = stat.S_IFMT(member.external_attr >> 16)
        directory = member.is_dir()
        require(member.orig_filename == member.filename, "unsafe archive ambiguous ZIP filename")
        require(mode in ({0, stat.S_IFDIR} if directory else {0, stat.S_IFREG}),
                "unsafe archive non-regular ZIP member")
        require(not (member.external_attr & 0x10) or directory, "unsafe archive ZIP directory mode")
        require(not directory or member.file_size == 0, "unsafe archive directory payload")
        archive_path(member.filename, directory, seen, ancestors)
        # Our generated wheels require no ZIP extra metadata. In particular,
        # PKWARE/ASi Unix extras can encode hardlinks even with a regular mode.
        require(not member.extra and not member.flag_bits & 1, "unsafe archive ZIP extension or encryption")
        archive.fp.seek(member.header_offset)
        header = archive.fp.read(30)
        require(len(header) == 30, "unsafe archive truncated ZIP header")
        signature, _, flags, compression, _, _, _, _, _, name_size, extra_size = struct.unpack("<4s5H3I2H", header)
        require(name_size <= MAX_NAME_BYTES, "archive name size limit exceeded")
        require(signature == b"PK\x03\x04" and extra_size == 0 and flags == member.flag_bits
                and compression == member.compress_type, "unsafe archive inconsistent ZIP local header")
        raw_name = archive.fp.read(name_size)
        require(raw_name.decode("utf-8" if flags & 0x800 else "cp437") == member.filename,
                "unsafe archive inconsistent ZIP local filename")
        # Opening a stream validates offsets/overlap without extracting a file.
        with archive.open(member):
            pass
    return members


def package_metadata(file):
    require(file.is_file() and not file.is_symlink(), "package metadata must be a real file")
    if file.suffix == ".pom":
        require(file.stat().st_size <= MAX_METADATA_BYTES, "XML metadata size limit exceeded")
        root = parse_xml(file.read_bytes())
        maven = f"{{{MAVEN_NAMESPACE}}}"
        require(root.tag == f"{maven}project",
                "invalid Maven POM namespace")
        group = one_xml_text(root, f"{maven}groupId", "invalid Maven POM groupId")
        artifact = one_xml_text(root, f"{maven}artifactId", "invalid Maven POM artifactId")
        license_element = root.findall(f"{maven}licenses/{maven}license")
        require(len(license_element) == 1, "invalid Maven POM license metadata")
        return {
            "name": f"{group}:{artifact}",
            "version": one_xml_text(root, f"{maven}version", "invalid Maven POM version"),
            "license": one_xml_text(
                license_element[0], f"{maven}name", "invalid Maven POM license name"
            ),
            "license_url": one_xml_text(
                license_element[0], f"{maven}url", "invalid Maven POM license URL"
            ),
        }
    require(file.stat().st_size <= MAX_ARCHIVE_BYTES, "archive byte size limit exceeded")
    if file.suffix == ".tgz":
        with tarfile.open(file, "r:gz", tarinfo=BoundedTarInfo) as archive:
            members = inspect_tar(archive)
            metadata = [member for member in members if member.name == "package/package.json"]
            require(len(metadata) == 1 and metadata[0].isfile(), "invalid npm package metadata")
            require(metadata[0].size <= MAX_METADATA_BYTES, "archive package metadata size limit exceeded")
            parsed = json.loads(archive.extractfile(metadata[0]).read(MAX_METADATA_BYTES + 1))
            for name in ("LICENSE", "NOTICE"):
                legal = [member for member in members if member.name == f"package/{name}"]
                require(len(legal) == 1 and legal[0].isfile(), f"approved license {name} is missing")
                require(legal[0].size <= MAX_METADATA_BYTES, f"approved license {name} size limit exceeded")
                parsed[f"{name.lower()}_text"] = archive.extractfile(legal[0]).read(MAX_METADATA_BYTES + 1)
            return parsed
    require(file.suffix in {".whl", ".nupkg", ".jar"}, "unsupported package artifact type")
    inspect_zip_directory(file)
    with zipfile.ZipFile(file) as archive:
        members = inspect_zip(archive)
        if file.suffix == ".nupkg":
            metadata = [member for member in members if member.filename.endswith(".nuspec")]
            require(len(metadata) == 1 and not metadata[0].is_dir(), "invalid NuGet package metadata")
            require(metadata[0].file_size <= MAX_METADATA_BYTES,
                    "archive package metadata size limit exceeded")
            root = parse_xml(archive.read(metadata[0]))
            nuget = f"{{{NUGET_NAMESPACE}}}"
            require(root.tag == f"{nuget}package", "invalid NuGet package metadata namespace")
            sections = root.findall(f"{nuget}metadata")
            require(len(sections) == 1, "invalid NuGet package metadata")
            section = sections[0]
            license_elements = section.findall(f"{nuget}license")
            require(len(license_elements) == 1
                    and license_elements[0].attrib == {"type": "expression"}
                    and (license_elements[0].text or "").strip(),
                    "invalid NuGet license metadata")
            package = {
                "name": one_xml_text(section, f"{nuget}id", "invalid NuGet package id"),
                "version": one_xml_text(section, f"{nuget}version", "invalid NuGet package version"),
                "authors": one_xml_text(section, f"{nuget}authors", "invalid NuGet package authors"),
                "license": license_elements[0].text.strip(),
            }
            repositories = section.findall(f"{nuget}repository")
            require(len(repositories) <= 1, "invalid NuGet repository metadata")
            if repositories:
                package["repository"] = dict(repositories[0].attrib)
            for name in ("LICENSE", "NOTICE"):
                legal = [member for member in members if member.filename == name]
                require(len(legal) == 1 and not legal[0].is_dir(),
                        f"approved license {name} is missing")
                require(legal[0].file_size <= MAX_METADATA_BYTES,
                        f"approved license {name} size limit exceeded")
                package[f"{name.lower()}_text"] = archive.read(legal[0])
            return package
        if file.suffix == ".jar":
            package = {}
            for name in ("LICENSE", "NOTICE"):
                member_name = f"META-INF/{name}"
                legal = [member for member in members if member.filename == member_name]
                require(len(legal) == 1 and not legal[0].is_dir(),
                        f"approved license {name} is missing")
                require(legal[0].file_size <= MAX_METADATA_BYTES,
                        f"approved license {name} size limit exceeded")
                package[f"{name.lower()}_text"] = archive.read(legal[0])
            for facade in (
                "CognerisClient", "CognerisException", "CognerisApiException",
                "CognerisTransportException", "CognerisResponseException",
                "CognerisJobTerminalException", "CognerisMaxAttemptsException",
            ):
                class_name = f"ai/cogneris/documentai/{facade}.class"
                classes = [member for member in members if member.filename == class_name]
                require(len(classes) == 1 and not classes[0].is_dir(),
                        f"Java facade class is missing: {facade}")
                require(classes[0].file_size >= 8, "invalid Java class metadata")
                header = archive.read(classes[0])[:8]
                require(header[:4] == b"\xca\xfe\xba\xbe"
                        and int.from_bytes(header[6:8], "big") == 61,
                        "Java artifact must contain Java 17 class files")
            return package
        metadata = [member for member in members if member.filename.endswith(".dist-info/METADATA")]
        require(len(metadata) == 1, "invalid wheel metadata")
        require(metadata[0].file_size <= MAX_METADATA_BYTES, "archive package metadata size limit exceeded")
        with archive.open(metadata[0]) as stream:
            parsed = email.parser.BytesParser().parsebytes(stream.read(MAX_METADATA_BYTES + 1))
        package = {"name": parsed["Name"], "version": parsed["Version"],
                   "license": parsed["License-Expression"]}
        for name in ("LICENSE", "NOTICE"):
            legal = [member for member in members
                     if member.filename.endswith(f".dist-info/licenses/{name}")]
            require(len(legal) == 1 and not legal[0].is_dir(), f"approved license {name} is missing")
            require(legal[0].file_size <= MAX_METADATA_BYTES, f"approved license {name} size limit exceeded")
            package[f"{name.lower()}_text"] = archive.read(legal[0])
        return package


def integrity(arguments):
    source_versions(arguments.version)
    directory = Path(arguments.artifacts)
    approved_license = (ROOT / "LICENSE").read_bytes()
    approved_notice = (ROOT / "NOTICE").read_bytes()
    expected_files = artifacts(arguments.version)
    require(directory.is_dir() and not directory.is_symlink(), "artifact directory must be real")
    require({file.name for file in directory.iterdir()} == set(expected_files) | {"manifest.json"},
            "unexpected or missing artifact files")
    require(all(file.is_file() and not file.is_symlink() for file in directory.iterdir()),
            "artifact files must be regular files")
    require((directory / "manifest.json").stat().st_size <= MAX_METADATA_BYTES,
            "archive manifest size limit exceeded")
    for filename in expected_files:
        require((directory / filename).stat().st_size <= MAX_ARCHIVE_BYTES,
                "archive byte size limit exceeded")
    require(re.fullmatch(r"[0-9a-f]{64}", arguments.manifest_sha256 or ""), "manifest digest is required")
    require(digest(directory / "manifest.json") == arguments.manifest_sha256, "manifest digest mismatch")
    manifest = json.loads((directory / "manifest.json").read_text())
    require(re.fullmatch(r"[0-9a-f]{40}", arguments.source or ""), "source commit is required")
    require(manifest["source"] == arguments.source, "source commit mismatch")
    require(manifest["version"] == arguments.version, "manifest version mismatch")
    require(set(manifest["files"]) == set(expected_files), "manifest artifact set mismatch")
    metadata = {}
    for filename, descriptor in expected_files.items():
        file = directory / filename
        require(digest(file) == manifest["files"][filename], "artifact digest mismatch")
        package = package_metadata(file)
        if "name" in descriptor:
            require(package.get("name") == descriptor["name"]
                    and package.get("version") == arguments.version,
                    "artifact package identity/version mismatch")
        if descriptor["license"]:
            require(package.get("license") == "Apache-2.0",
                    "artifact license metadata must be Apache-2.0")
        if descriptor["kind"] == "maven-pom":
            require(package.get("license_url") == "https://www.apache.org/licenses/LICENSE-2.0",
                    "Maven POM license URL must identify Apache-2.0")
        if descriptor["kind"] == "nuget":
            require(package.get("authors") == "COGNERIS, INC.",
                    "NuGet package authors must identify COGNERIS, INC.")
            repository = package.get("repository", {})
            require(repository.get("type") == "git"
                    and repository.get("url") == "https://github.com/cogneris-ai/cogneris-api-examples.git",
                    "NuGet repository metadata must identify the approved repository")
        if descriptor["legal"]:
            require(package.get("license_text") == approved_license,
                    "artifact LICENSE must match approved license")
            require(package.get("notice_text") == approved_notice,
                    "artifact NOTICE must match approved notice")
        require("publishConfig" not in package, "package cannot override publication registry/configuration")
        if descriptor.get("name", "").endswith("-cli"):
            require(package.get("dependencies", {}).get("@cogneris-ai/document-ai-sdk") == arguments.version,
                    "CLI SDK dependency must exactly match release version")
        if "name" in descriptor:
            metadata[descriptor["name"]] = package
    return metadata


def clean_build_snapshot():
    """Bind actual packaged inputs to HEAD, then build from those immutable bytes.

    Only copied source trees and the build script/dependency declarations matter.
    Excluded caches/outputs and unrelated files elsewhere are neither rejected nor
    copied. Explicit byte comparisons also catch assume-unchanged index entries.
    """
    error = "dirty or untracked build inputs; commit relevant sources before packaging"
    source = run(["git", "rev-parse", "HEAD"])
    require(re.fullmatch(r"[0-9a-f]{40}", source), "source commit is required")
    relevant = (*BUILD_DIRECTORIES, *BUILD_FILES)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", source, "--", *relevant], cwd=ROOT)
    require(staged.returncode == 0, error)
    entries = subprocess.check_output(["git", "ls-tree", "-rz", "--full-tree", source, "--", *relevant], cwd=ROOT)
    expected = {}
    for entry in filter(None, entries.split(b"\0")):
        metadata, encoded_path = entry.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split()
        relative = encoded_path.decode()
        if EXCLUDED_BUILD_NAMES.intersection(Path(relative).parts):
            continue
        require(kind == "blob" and mode in {"100644", "100755"}, error)
        expected[relative] = (mode, object_id)
    actual = set(BUILD_FILES)
    for relative in BUILD_DIRECTORIES:
        directory = ROOT / relative
        require(directory.is_dir() and not directory.is_symlink(), error)
        for current, directories, files in os.walk(directory, followlinks=False):
            directories[:] = [name for name in directories if name not in EXCLUDED_BUILD_NAMES]
            require(all(not (Path(current) / name).is_symlink() for name in directories), error)
            for name in files:
                if name not in EXCLUDED_BUILD_NAMES:
                    actual.add((Path(current) / name).relative_to(ROOT).as_posix())
    require(actual == set(expected), error)
    snapshot = {}
    for relative, (mode, object_id) in expected.items():
        file = ROOT / relative
        require(file.is_file() and not file.is_symlink(), error)
        committed = subprocess.check_output(["git", "cat-file", "blob", object_id], cwd=ROOT)
        require(file.read_bytes() == committed, error)
        require(bool(file.stat().st_mode & 0o111) == (mode == "100755"), error)
        snapshot[relative] = (committed, mode)
    return source, snapshot


def java_command(checkout, *tasks, project_directory=None):
    project = Path(project_directory) if project_directory else checkout / "sdks/java"
    return [
        sys.executable,
        checkout / "scripts/run-java.py",
        "--",
        "sh",
        checkout / "sdks/java/gradlew",
        "--no-daemon",
        "--console=plain",
        "--project-dir",
        project,
        *tasks,
    ]


def write_nuget_config(file, staged_source):
    staged = Path(staged_source)
    require(staged.is_dir() and not staged.is_symlink(), "staged NuGet source must be a real directory")
    configuration = ET.Element("configuration")
    sources = ET.SubElement(configuration, "packageSources")
    ET.SubElement(sources, "clear")
    ET.SubElement(sources, "add", key="cogneris-staged", value=str(staged))
    ET.SubElement(
        sources, "add", key="nuget.org", value="https://api.nuget.org/v3/index.json"
    )
    mappings = ET.SubElement(configuration, "packageSourceMapping")
    staged_mapping = ET.SubElement(mappings, "packageSource", key="cogneris-staged")
    ET.SubElement(staged_mapping, "package", pattern="Cogneris.DocumentAI")
    public_mapping = ET.SubElement(mappings, "packageSource", key="nuget.org")
    for pattern in ("Microsoft.*", "Polly", "Polly.*", "System.*"):
        ET.SubElement(public_mapping, "package", pattern=pattern)
    ET.ElementTree(configuration).write(file, encoding="utf-8", xml_declaration=True)


def verify_nuget_install(assets_file, package_cache, staged_package, package_id, version):
    assets_path = Path(assets_file)
    staged_path = Path(staged_package)
    cache = Path(package_cache)
    require(assets_path.is_file() and not assets_path.is_symlink(),
            "NuGet restore assets must be a real file")
    require(assets_path.stat().st_size <= MAX_ARCHIVE_BYTES,
            "NuGet restore assets size limit exceeded")
    require(staged_path.is_file() and not staged_path.is_symlink(),
            "staged NuGet package must be a real file")
    assets = json.loads(assets_path.read_text())
    identity = f"{package_id}/{version}"
    library = assets.get("libraries", {}).get(identity)
    require(isinstance(library, dict) and library.get("type") == "package",
            "NuGet consumer did not resolve a package-only dependency")
    relative = f"{package_id.casefold()}/{version}"
    require(library.get("path") == relative, "NuGet consumer resolved an unexpected package path")
    installed = cache / relative / f"{package_id.casefold()}.{version}.nupkg"
    require(installed.is_file() and not installed.is_symlink(),
            "installed NuGet package must be a real file")
    require(installed.stat().st_size <= MAX_ARCHIVE_BYTES,
            "installed NuGet package size limit exceeded")
    require(digest(installed) == digest(staged_path),
            "installed NuGet package digest does not match the staged artifact")
    return installed


def build(arguments):
    output = Path(arguments.output).absolute()
    require(not output.exists() and not output.is_symlink(), "artifact output already exists; refusing overwrite")
    source, snapshot = clean_build_snapshot()
    source_versions(arguments.version)
    with tempfile.TemporaryDirectory(prefix="cogneris-release-build-") as temporary_name:
        temporary = Path(temporary_name)
        checkout = temporary / "checkout"
        staged = temporary / "artifacts"
        staged.mkdir()
        # Use HEAD's verified bytes, never a second read of mutable source files.
        for relative, (contents, mode) in snapshot.items():
            if any(relative.startswith(directory + "/") for directory in BUILD_DIRECTORIES):
                file = checkout / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(contents)
                file.chmod(0o755 if mode == "100755" else 0o644)
        for legal_file in ("LICENSE", "NOTICE"):
            contents, _ = snapshot[legal_file]
            (checkout / "cli" / legal_file).write_bytes(contents)
        runner = checkout / "scripts/run-java.py"
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_bytes(snapshot["scripts/run-java.py"][0])
        runner.chmod(0o644)
        (checkout / "package.json").write_text('{"private":true}\n')
        compiler = ROOT / "node_modules/.bin/tsc"
        run([compiler, "-p", checkout / "sdks/typescript/tsconfig.json"], checkout)
        run(["npm", "pack", "./sdks/typescript", "--ignore-scripts", "--pack-destination", staged], checkout)
        sdk_tarball = staged / f"cogneris-ai-document-ai-sdk-{arguments.version}.tgz"
        run(["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "--no-save", sdk_tarball], checkout)
        run([compiler, "-p", checkout / "cli/tsconfig.json", "--typeRoots", ROOT / "node_modules/@types"], checkout)
        run(["npm", "pack", "./cli", "--ignore-scripts", "--pack-destination", staged], checkout)
        wheels = temporary / "wheel-build"
        run(["uv", "build", "--wheel", "--out-dir", wheels], checkout / "sdks/python")
        # uv also creates an output-directory .gitignore; it is not a release artifact.
        wheel = wheels / f"cogneris_document_ai_sdk-{arguments.version}-py3-none-any.whl"
        shutil.copyfile(wheel, staged / wheel.name)
        package_environment = dict(os.environ)
        package_environment["NUGET_PACKAGES"] = str(temporary / "nuget-packages")
        run([
            os.environ.get("COGNERIS_DOTNET", "dotnet"), "pack",
            checkout / "sdks/csharp/src/Cogneris.DocumentAI/Cogneris.DocumentAI.csproj",
            "-c", "Release", "-o", staged,
        ], checkout, package_environment)
        package_environment["GRADLE_USER_HOME"] = str(temporary / "gradle-home")
        run(java_command(
            checkout, "clean", "test", "jar", "generatePomFileForMavenPublication"
        ), checkout, package_environment, diagnostic_context="java-build")
        java_build = checkout / "sdks/java/build"
        shutil.copyfile(
            java_build / f"libs/cogneris-document-ai-sdk-{arguments.version}.jar",
            staged / f"cogneris-document-ai-sdk-{arguments.version}.jar",
        )
        shutil.copyfile(
            java_build / "publications/maven/pom-default.xml",
            staged / f"cogneris-document-ai-sdk-{arguments.version}.pom",
        )
        require({file.name for file in staged.iterdir()} == set(artifacts(arguments.version)),
                f"built filenames do not match exact release version: {sorted(file.name for file in staged.iterdir())}")
        manifest = {"version": arguments.version, "source": source,
                    "files": {file.name: digest(file) for file in sorted(staged.iterdir())}}
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        # copytree refuses an existing destination; no user output is removed.
        shutil.copytree(staged, output)
    print(f"Built 5 package families; manifest SHA-256: {digest(output / 'manifest.json')}")


def clean_install(arguments):
    directory = Path(arguments.artifacts).resolve()
    environment = {key: value for key, value in os.environ.items()
                   if key not in {"PYTHONPATH", "VIRTUAL_ENV", "COGNERIS_API_KEY"}}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"] = str(ROOT)
    with tempfile.TemporaryDirectory(prefix="cogneris-release-consumer-") as temporary_name:
        # Resolve macOS's /var -> /private/var alias before binding package
        # caches; package-only consumers compare the actual loaded code source.
        consumer = Path(temporary_name).resolve()
        run(["uv", "venv", "--python", sys.executable, consumer / "venv"], consumer, environment)
        python = consumer / "venv/bin/python"
        wheel = directory / f"cogneris_document_ai_sdk-{arguments.version}-py3-none-any.whl"
        run(["uv", "pip", "install", "--python", python, wheel], consumer, environment)
        run([python, ROOT / "tests/sdk_python_installed_smoke.py", "-v"], consumer, environment)
        run([python, ROOT / "tests/examples_python_installed_smoke.py", "-v"], consumer, environment)
        if not arguments.python_only:
            (consumer / "package.json").write_text('{"private":true}\n')
            tarballs = [directory / name for name in artifacts(arguments.version) if name.endswith(".tgz")]
            run(["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", *tarballs], consumer, environment)
            run(["node", "-e", "const s = require('@cogneris-ai/document-ai-sdk'); "
                 "if(typeof s.CognerisClient !== 'function') process.exit(1); "
                 "if(!require.resolve('@cogneris-ai/document-ai-sdk').includes('/node_modules/')) process.exit(1);"],
                consumer, environment)
            invoked = subprocess.run([str(consumer / "node_modules/.bin/cogneris"), "jobs", "get", "job-id"],
                                     cwd=consumer, env=environment, capture_output=True, text=True)
            require(invoked.returncode == 2 and not invoked.stdout, "installed CLI configuration smoke failed")

            nuget_source = consumer / "nuget-source"
            nuget_source.mkdir()
            staged_nuget = nuget_source / f"Cogneris.DocumentAI.{arguments.version}.nupkg"
            shutil.copyfile(
                directory / f"Cogneris.DocumentAI.{arguments.version}.nupkg",
                staged_nuget,
            )
            csharp_consumer = shutil.copytree(
                ROOT / "tests/fixtures/csharp-consumer", consumer / "csharp-consumer"
            )
            for fixture in csharp_consumer.iterdir():
                require("ProjectReference" not in fixture.read_text()
                        and str(ROOT) not in fixture.read_text(),
                        "C# release consumer must be package-only")
            csharp_environment = dict(environment)
            nuget_cache = consumer / "nuget-cache"
            csharp_environment["NUGET_PACKAGES"] = str(nuget_cache)
            nuget_config = consumer / "NuGet.config"
            write_nuget_config(nuget_config, nuget_source)
            dotnet = os.environ.get("COGNERIS_DOTNET", "dotnet")
            run([
                dotnet, "restore", csharp_consumer,
                "--configfile", nuget_config,
            ], consumer, csharp_environment)
            verify_nuget_install(
                csharp_consumer / "obj/project.assets.json",
                nuget_cache,
                staged_nuget,
                "Cogneris.DocumentAI",
                arguments.version,
            )
            run([
                dotnet, "run", "--project", csharp_consumer,
                "--configuration", "Release", "--no-restore",
            ], consumer, csharp_environment)

            maven_repository = consumer / "maven-repository"
            coordinates = maven_repository / "ai/cogneris/cogneris-document-ai-sdk" / arguments.version
            coordinates.mkdir(parents=True)
            java_jar = coordinates / f"cogneris-document-ai-sdk-{arguments.version}.jar"
            java_pom = coordinates / f"cogneris-document-ai-sdk-{arguments.version}.pom"
            shutil.copyfile(directory / java_jar.name, java_jar)
            shutil.copyfile(directory / java_pom.name, java_pom)
            java_consumer = shutil.copytree(
                ROOT / "tests/fixtures/java-consumer", consumer / "java-consumer"
            )
            for fixture in java_consumer.rglob("*"):
                if fixture.is_file():
                    require("sdks/java" not in fixture.read_text()
                            and str(ROOT) not in fixture.read_text(),
                            "Java release consumer must be package-only")
            java_environment = dict(environment)
            java_environment["COGNERIS_MAVEN_REPOSITORY"] = str(maven_repository)
            java_environment["GRADLE_USER_HOME"] = str(consumer / "gradle-home")
            java_output = run(
                java_command(ROOT, "test", project_directory=java_consumer),
                consumer,
                java_environment,
                diagnostic_context="java-consumer",
            )
            require(f"Resolved Maven artifact: {java_jar}" in java_output,
                    "Java consumer did not resolve the staged Maven artifact")
    print("Exact artifacts passed clean installation and all installed SDK/example loopback tests.")


def check_publish(arguments, metadata):
    require(os.environ.get("SDK_RELEASE_READY") == "true",
            "SDK_RELEASE_READY must confirm registry ownership, licensing, security contact and protected environment setup")
    ready = f"SDK_{arguments.registry.upper()}_TRUSTED_PUBLISHING_READY"
    require(os.environ.get(ready) == "true", f"{ready} must confirm the registry trusted publisher setup")
    if arguments.registry == "npm":
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        for name in ("@cogneris-ai/document-ai-sdk", "@cogneris-ai/document-ai-cli"):
            require(metadata[name].get("repository", {}).get("url") == f"git+https://github.com/{repository}.git",
                    "npm repository.url must match the approved GitHub repository before OIDC publication")
        npm_version = tuple(int(part) for part in run(["npm", "--version"]).split("."))
        require(npm_version >= (11, 5, 1), "npm >=11.5.1 is required for trusted publishing")
        require(os.environ.get("REPOSITORY_PRIVATE") == "false", "npm provenance requires a public repository")
        # Trusted publishing cannot bootstrap an unregistered npm package.
        for name in ("@cogneris-ai/document-ai-sdk", "@cogneris-ai/document-ai-cli"):
            with urllib.request.urlopen(f"https://registry.npmjs.org/{name}", timeout=20) as response:
                require(json.load(response).get("name") == name, "npm registry ownership/bootstrap gate failed")
    require(os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_REF") == "refs/heads/main",
            "publication requires a GitHub Actions run on main")
    require("ACTIONS_ID_TOKEN_REQUEST_URL" in os.environ and "ACTIONS_ID_TOKEN_REQUEST_TOKEN" in os.environ,
            "GitHub OIDC capability is absent")
    require(not any(key in os.environ for key in ("NPM_TOKEN", "NODE_AUTH_TOKEN", "TWINE_PASSWORD", "PYPI_API_TOKEN")),
            "long-lived publishing credential environment variables are forbidden")
    print("Local publication prerequisites verified; the registry must still authenticate the OIDC identity.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check-version", "build", "verify", "check-publish"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--output")
    parser.add_argument("--artifacts")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--source")
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--integrity-only", action="store_true")
    parser.add_argument("--registry", choices=("npm", "pypi"))
    arguments = parser.parse_args()
    if arguments.command == "check-version":
        source_versions(arguments.version)
    elif arguments.command == "build":
        require(arguments.output, "--output is required")
        build(arguments)
    else:
        require(arguments.artifacts, "--artifacts is required")
        metadata = integrity(arguments)
        if arguments.command == "check-publish":
            require(arguments.registry, "--registry is required")
            check_publish(arguments, metadata)
        elif not arguments.integrity_only:
            clean_install(arguments)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        # Do not print subprocess output: dependency tools may include environment data.
        print(f"Release gate failed: {error}", file=sys.stderr)
        sys.exit(1)
