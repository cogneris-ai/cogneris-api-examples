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
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIRECTORIES = ("sdks/typescript", "sdks/python", "cli")
BUILD_FILES = ("LICENSE", "NOTICE", "package.json", "package-lock.json", "scripts/sdk-release.py")
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
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(arguments, cwd=ROOT, env=None):
    return subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env,
                          check=True, text=True, capture_output=True).stdout.strip()


def digest(file):
    value = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            value.update(chunk)
    return value.hexdigest()


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


def filenames(version):
    return {
        f"cogneris-ai-document-ai-sdk-{version}.tgz": "@cogneris-ai/document-ai-sdk",
        f"cogneris-ai-document-ai-cli-{version}.tgz": "@cogneris-ai/document-ai-cli",
        f"cogneris_document_ai_sdk-{version}-py3-none-any.whl": "cogneris-document-ai-sdk",
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
    inspect_zip_directory(file)
    with zipfile.ZipFile(file) as archive:
        members = inspect_zip(archive)
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
    expected_files = filenames(arguments.version)
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
    for filename, name in expected_files.items():
        file = directory / filename
        require(digest(file) == manifest["files"][filename], "artifact digest mismatch")
        package = package_metadata(file)
        require(package["name"] == name and package["version"] == arguments.version,
                "artifact package identity/version mismatch")
        require(package.get("license") == "Apache-2.0",
                "artifact license metadata must be Apache-2.0")
        require(package.get("license_text") == approved_license,
                "artifact LICENSE must match approved license")
        require(package.get("notice_text") == approved_notice,
                "artifact NOTICE must match approved notice")
        require("publishConfig" not in package, "package cannot override publication registry/configuration")
        if name.endswith("-cli"):
            require(package.get("dependencies", {}).get("@cogneris-ai/document-ai-sdk") == arguments.version,
                    "CLI SDK dependency must exactly match release version")
        metadata[name] = package
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
        require({file.name for file in staged.iterdir()} == set(filenames(arguments.version)),
                f"built filenames do not match exact release version: {sorted(file.name for file in staged.iterdir())}")
        manifest = {"version": arguments.version, "source": source,
                    "files": {file.name: digest(file) for file in sorted(staged.iterdir())}}
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        # copytree refuses an existing destination; no user output is removed.
        shutil.copytree(staged, output)
    print(f"Built 3 packages; manifest SHA-256: {digest(output / 'manifest.json')}")


def clean_install(arguments):
    directory = Path(arguments.artifacts).resolve()
    environment = {key: value for key, value in os.environ.items()
                   if key not in {"PYTHONPATH", "VIRTUAL_ENV", "COGNERIS_API_KEY"}}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["COGNERIS_REPOSITORY_ROOT_FOR_TESTING"] = str(ROOT)
    with tempfile.TemporaryDirectory(prefix="cogneris-release-consumer-") as temporary_name:
        consumer = Path(temporary_name)
        run(["uv", "venv", "--python", sys.executable, consumer / "venv"], consumer, environment)
        python = consumer / "venv/bin/python"
        wheel = directory / f"cogneris_document_ai_sdk-{arguments.version}-py3-none-any.whl"
        run(["uv", "pip", "install", "--python", python, wheel], consumer, environment)
        run([python, ROOT / "tests/sdk_python_installed_smoke.py", "-v"], consumer, environment)
        run([python, ROOT / "tests/examples_python_installed_smoke.py", "-v"], consumer, environment)
        if not arguments.python_only:
            (consumer / "package.json").write_text('{"private":true}\n')
            tarballs = [directory / name for name in filenames(arguments.version) if name.endswith(".tgz")]
            run(["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", *tarballs], consumer, environment)
            run(["node", "-e", "const s = require('@cogneris-ai/document-ai-sdk'); "
                 "if(typeof s.CognerisClient !== 'function') process.exit(1); "
                 "if(!require.resolve('@cogneris-ai/document-ai-sdk').includes('/node_modules/')) process.exit(1);"],
                consumer, environment)
            invoked = subprocess.run([str(consumer / "node_modules/.bin/cogneris"), "jobs", "get", "job-id"],
                                     cwd=consumer, env=environment, capture_output=True, text=True)
            require(invoked.returncode == 2 and not invoked.stdout, "installed CLI configuration smoke failed")
    print("Exact artifacts passed clean installation and installed Python SDK/example loopback tests.")


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
