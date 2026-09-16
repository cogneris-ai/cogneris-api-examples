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
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
    return hashlib.sha256(file.read_bytes()).hexdigest()


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
        f"cogneris-document-ai-sdk-{version}.tgz": "@cogneris/document-ai-sdk",
        f"cogneris-document-ai-cli-{version}.tgz": "@cogneris/document-ai-cli",
        f"cogneris_document_ai_sdk-{version}-py3-none-any.whl": "cogneris-document-ai-sdk",
    }


def package_metadata(file):
    if file.suffix == ".tgz":
        with tarfile.open(file, "r:gz") as archive:
            members = [member for member in archive.getmembers() if member.name == "package/package.json"]
            require(len(members) == 1 and members[0].isfile(), "invalid npm package metadata")
            return json.load(archive.extractfile(members[0]))
    with zipfile.ZipFile(file) as archive:
        metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        require(len(metadata) == 1, "invalid wheel metadata")
        parsed = email.parser.BytesParser().parsebytes(archive.read(metadata[0]))
        return {"name": parsed["Name"], "version": parsed["Version"]}


def integrity(arguments):
    source_versions(arguments.version)
    directory = Path(arguments.artifacts)
    expected_files = filenames(arguments.version)
    require(directory.is_dir() and not directory.is_symlink(), "artifact directory must be real")
    require({file.name for file in directory.iterdir()} == set(expected_files) | {"manifest.json"},
            "unexpected or missing artifact files")
    require(all(file.is_file() and not file.is_symlink() for file in directory.iterdir()),
            "artifact files must be regular files")
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
        require("publishConfig" not in package, "package cannot override publication registry/configuration")
        if name.endswith("-cli"):
            require(package.get("dependencies", {}).get("@cogneris/document-ai-sdk") == arguments.version,
                    "CLI SDK dependency must exactly match release version")
        metadata[name] = package
    return metadata


def build(arguments):
    source_versions(arguments.version)
    output = Path(arguments.output).absolute()
    require(not output.exists() and not output.is_symlink(), "artifact output already exists; refusing overwrite")
    source = run(["git", "rev-parse", "HEAD"])
    require(re.fullmatch(r"[0-9a-f]{40}", source), "source commit is required")
    with tempfile.TemporaryDirectory(prefix="cogneris-release-build-") as temporary_name:
        temporary = Path(temporary_name)
        checkout = temporary / "checkout"
        staged = temporary / "artifacts"
        staged.mkdir()
        ignored = shutil.ignore_patterns("dist", "node_modules", ".venv", "__pycache__", ".ruff_cache")
        for relative in ("sdks", "cli"):
            shutil.copytree(ROOT / relative, checkout / relative, ignore=ignored)
        (checkout / "package.json").write_text('{"private":true}\n')
        compiler = ROOT / "node_modules/.bin/tsc"
        run([compiler, "-p", checkout / "sdks/typescript/tsconfig.json"], checkout)
        run(["npm", "pack", "./sdks/typescript", "--ignore-scripts", "--pack-destination", staged], checkout)
        sdk_tarball = staged / f"cogneris-document-ai-sdk-{arguments.version}.tgz"
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
            run(["node", "-e", "const s = require('@cogneris/document-ai-sdk'); "
                 "if(typeof s.CognerisClient !== 'function') process.exit(1); "
                 "if(!require.resolve('@cogneris/document-ai-sdk').includes('/node_modules/')) process.exit(1);"],
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
        for name in ("@cogneris/document-ai-sdk", "@cogneris/document-ai-cli"):
            require(metadata[name].get("repository", {}).get("url") == f"git+https://github.com/{repository}.git",
                    "npm repository.url must match the approved GitHub repository before OIDC publication")
        npm_version = tuple(int(part) for part in run(["npm", "--version"]).split("."))
        require(npm_version >= (11, 5, 1), "npm >=11.5.1 is required for trusted publishing")
        require(os.environ.get("REPOSITORY_PRIVATE") == "false", "npm provenance requires a public repository")
        # Trusted publishing cannot bootstrap an unregistered npm package.
        for name in ("@cogneris/document-ai-sdk", "@cogneris/document-ai-cli"):
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
