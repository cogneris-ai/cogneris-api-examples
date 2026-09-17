"""Security contracts for the executable GitHub workflow configuration."""
import copy
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ACTIONS = {"actions/checkout", "actions/setup-node", "actions/setup-python",
                   "actions/upload-artifact", "actions/download-artifact",
                   "pypa/gh-action-pypi-publish"}


class WorkflowLoader(yaml.SafeLoader):
    # YAML 1.2 booleans: a GitHub `on` key is never the boolean True.
    yaml_implicit_resolvers = {
        key: [(tag, regex) for tag, regex in values if tag != "tag:yaml.org,2002:bool"]
        for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }

    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate workflow key")
        return super().construct_mapping(node, deep=deep)


WorkflowLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf")
)


def parse(text):
    return yaml.load(text, Loader=WorkflowLoader)


def command(block, **fields):
    return {"run": block.strip(), **fields}


def action(name, settings, **fields):
    return {"uses": name, "with": settings, **fields}


ARTIFACT_ARGUMENTS = (
    '--version "$RELEASE_VERSION" --artifacts "$RUNNER_TEMP/sdk-release" '
    '--manifest-sha256 "$MANIFEST_SHA256" --source "$GITHUB_SHA"'
)
CHECK_VERSION = 'python scripts/sdk-release.py check-version --version "$RELEASE_VERSION"'
VERSION_OUTPUT = """version=$(node -p "require('./cli/package.json').version")
python scripts/sdk-release.py check-version --version "$version"
echo "RELEASE_VERSION=$version" >> "$GITHUB_ENV"
echo "version=$version" >> "$GITHUB_OUTPUT" """
MANIFEST_OUTPUT = 'echo "sha256=$(sha256sum "$RUNNER_TEMP/sdk-release/manifest.json" | cut -d \' \' -f 1)" >> "$GITHUB_OUTPUT"'
PYTHON_ENV = {"PYTHONDONTWRITEBYTECODE": "1"}
READ_ONLY = {"contents": "read"}


def checkout_step():
    return action("actions/checkout", {"persist-credentials": False})


def node_step():
    return action("actions/setup-node", {"node-version": 24, "package-manager-cache": False})


def python_step(matrix=False):
    return action("actions/setup-python", {"python-version": "${{ matrix.python }}" if matrix else "3.12"})


def download_step(build):
    return action("actions/download-artifact", {
        "artifact-ids": "${{ needs." + build + ".outputs.artifact-id }}",
        "path": "${{ runner.temp }}/sdk-release",
    })


def expected_jobs(release):
    """Allowlist complete executable blocks, step order, and all execution fields.

    Deliberately do not parse arbitrary shell or accept a matching line inside a
    larger program. Any new shell/control flow needs an explicit contract review.
    Presentation-only step names and the terminal YAML newline are normalized.
    """
    build = "build" if release else "postman"
    version = "${{ inputs.version }}" if release else "${{ needs.postman.outputs.version }}"
    main_steps = [
        checkout_step(), node_step(), python_step(),
        command("python -m pip install uv==0.10.10"),
        command(CHECK_VERSION) if release else command(VERSION_OUTPUT, id="version"),
        *[command(body) for body in ("npm ci", "npm run audit:deps", "npm run check:sdks", "npm run verify:sdks",
                                    "npm run test:cli", "npm run build:cli", "npm run test:docs", "npm test")],
        command('npm run pack:sdks -- --version "$RELEASE_VERSION" --output "$RUNNER_TEMP/sdk-release"'),
        command(MANIFEST_OUTPUT, id="manifest"),
        command("npm run verify:artifacts -- " + ARTIFACT_ARGUMENTS,
                env={"MANIFEST_SHA256": "${{ steps.manifest.outputs.sha256 }}"}),
        action("actions/upload-artifact", {
            "name": "sdk-release-${{ github.run_id }}-${{ github.run_attempt }}",
            "path": "${{ runner.temp }}/sdk-release/",
            "if-no-files-found": "error", "retention-days": 14,
        }, id="artifacts"),
    ]
    outputs = {"artifact-id": "${{ steps.artifacts.outputs.artifact-id }}",
               "manifest-sha256": "${{ steps.manifest.outputs.sha256 }}"}
    if not release:
        outputs["version"] = "${{ steps.version.outputs.version }}"
    jobs = {
        build: {
            "runs-on": "ubuntu-latest", "permissions": READ_ONLY,
            "outputs": outputs,
            "env": dict(PYTHON_ENV, **({"RELEASE_VERSION": version} if release else {})),
            "steps": main_steps,
        },
        "python-compatibility": {
            "needs": [build], "runs-on": "ubuntu-latest", "permissions": READ_ONLY,
            "strategy": {"fail-fast": False, "matrix": {"python": ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]}},
            "env": dict(PYTHON_ENV, RELEASE_VERSION=version,
                        MANIFEST_SHA256="${{ needs." + build + ".outputs.manifest-sha256 }}"),
            "steps": [checkout_step(), python_step(matrix=True),
                      command("python -m pip install uv==0.10.10"), download_step(build),
                      command("python scripts/sdk-release.py verify " + ARTIFACT_ARGUMENTS + " --python-only")],
        },
    }
    if release:
        for registry in ("npm", "pypi"):
            env = dict(PYTHON_ENV, RELEASE_VERSION=version,
                       MANIFEST_SHA256="${{ needs.build.outputs.manifest-sha256 }}",
                       SDK_RELEASE_READY="${{ vars.SDK_RELEASE_READY }}")
            env["SDK_" + registry.upper() + "_TRUSTED_PUBLISHING_READY"] = (
                "${{ vars.SDK_" + registry.upper() + "_TRUSTED_PUBLISHING_READY }}")
            steps = [checkout_step()]
            if registry == "npm":
                env.update(NPM_CONFIG_USERCONFIG="/dev/null",
                           NPM_CONFIG_GLOBALCONFIG="${{ github.workspace }}/../sdk-release-global.npmrc",
                           REPOSITORY_PRIVATE="${{ github.event.repository.private }}")
                steps.append(node_step())
            steps.extend([
                python_step(), download_step(build),
                command("python scripts/sdk-release.py verify " + ARTIFACT_ARGUMENTS + " --integrity-only\n"
                        "python scripts/sdk-release.py check-publish " + ARTIFACT_ARGUMENTS + " --registry " + registry),
            ])
            if registry == "npm":
                steps.append(command(
                    'npm publish "./cogneris-ai-document-ai-sdk-$RELEASE_VERSION.tgz" --registry https://registry.npmjs.org --access public --provenance --ignore-scripts\n'
                    'npm publish "./cogneris-ai-document-ai-cli-$RELEASE_VERSION.tgz" --registry https://registry.npmjs.org --access public --provenance --ignore-scripts',
                    **{"working-directory": "${{ runner.temp }}/sdk-release"}))
            else:
                steps.extend([
                    command('mkdir "$RUNNER_TEMP/pypi"\n'
                            'cp "$RUNNER_TEMP/sdk-release/cogneris_document_ai_sdk-$RELEASE_VERSION-py3-none-any.whl" "$RUNNER_TEMP/pypi/"'),
                    action("pypa/gh-action-pypi-publish", {
                        "packages-dir": "${{ runner.temp }}/pypi/", "attestations": True,
                    }),
                ])
            jobs["publish-" + registry] = {
                "if": "${{ inputs.dry_run == false && github.ref == 'refs/heads/main' }}",
                "needs": ["build", "python-compatibility"], "environment": "sdk-release",
                "runs-on": "ubuntu-latest", "permissions": {"contents": "read", "id-token": "write"},
                "env": env, "steps": steps,
            }
    return jobs


def contract(document, source, release):
    assert set(document) == ({"name", "on", "permissions", "jobs", "concurrency"} if release
                             else {"name", "on", "permissions", "jobs"})
    assert document["permissions"] == READ_ONLY
    if release:
        assert isinstance(document["on"], dict) and set(document["on"]) == {"workflow_dispatch"}
        assert set(document["on"]["workflow_dispatch"]) == {"inputs"}
        inputs = copy.deepcopy(document["on"]["workflow_dispatch"]["inputs"])
        for value in inputs.values():
            value.pop("description", None)
        assert inputs == {"version": {"required": True, "type": "string"},
                          "dry_run": {"required": True, "type": "boolean", "default": True}}
        assert document["concurrency"] == {"group": "sdk-release", "cancel-in-progress": False}
    else:
        assert document["on"] == {"pull_request": None, "push": {"branches": ["main"]}}
    actual = copy.deepcopy(document["jobs"])
    for job in actual.values():
        for step in job["steps"]:
            step.pop("name", None)  # Only a UI label; all execution fields are compared below.
            if "uses" in step:
                name, sha = step["uses"].split("@")
                assert name in ALLOWED_ACTIONS
                assert re.fullmatch(r"[0-9a-f]{40}", sha)
                assert re.search(re.escape(step["uses"]) + r"[ \t]+# v\d[^\n]*", source)
                step["uses"] = name
            if "run" in step:
                step["run"] = step["run"].strip()
    expected = expected_jobs(release)
    assert set(actual) == set(expected)
    for name, job in expected.items():
        assert actual[name] == job, "workflow execution contract changed: " + name


class SdkWorkflowTests(unittest.TestCase):
    def load(self, name):
        file = ROOT / ".github/workflows" / name
        self.assertTrue(file.is_file(), f"missing workflow: {name}")
        source = file.read_text()
        return parse(source), source

    def test_validation_runs_public_gates_and_installs_the_built_artifacts(self):
        document, source = self.load("validate.yml")
        contract(document, source, False)

    def test_release_is_manual_dry_by_default_and_uses_protected_oidc_jobs(self):
        document, source = self.load("release-sdks.yml")
        contract(document, source, True)

    def test_contract_rejects_trigger_permission_gate_and_integrity_regressions(self):
        original, source = self.load("release-sdks.yml")
        mutations = [
            lambda d: d.update({"on": "workflow_dispatch"}),
            lambda d: d.update({"on": ["workflow_dispatch", "push"]}),
            lambda d: d["on"].update({"release": {"types": ["published"]}}),
            lambda d: d.update(permissions="write-all"),
            lambda d: d["jobs"]["build"].update(permissions={"contents": "read", "id-token": "write"}),
            lambda d: d["jobs"]["publish-npm"].update({"if": "${{ always() }}"}),
            lambda d: d["jobs"]["publish-pypi"].pop("environment"),
            lambda d: d["jobs"]["publish-npm"].update(needs=["build"]),
            lambda d: d["on"]["workflow_dispatch"]["inputs"]["dry_run"].update(default=False),
            lambda d: d["jobs"]["build"]["steps"][0].update(uses="actions/checkout@main"),
            lambda d: d["jobs"]["build"].update(steps=[s for s in d["jobs"]["build"]["steps"] if s.get("run") != "npm run test:docs"]),
            lambda d: d["jobs"]["build"].update(steps=[s for s in d["jobs"]["build"]["steps"] if "check-version" not in s.get("run", "")]),
            lambda d: d["jobs"]["publish-npm"].update(steps=[s for s in d["jobs"]["publish-npm"]["steps"] if "check-publish" not in s.get("run", "")]),
            lambda d: d["jobs"]["publish-pypi"].update(steps=[s for s in d["jobs"]["publish-pypi"]["steps"] if "--manifest-sha256" not in s.get("run", "")]),
            lambda d: d["jobs"]["python-compatibility"].update({"if": "${{ false }}"}),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaises((AssertionError, KeyError, ValueError, TypeError, StopIteration)):
                    contract(changed, source, True)

    def test_yaml_rejects_duplicate_keys_and_python_object_construction(self):
        with self.assertRaises(ValueError):
            parse("on: {workflow_dispatch: {}}\non: push\n")
        with self.assertRaises(yaml.constructor.ConstructorError):
            parse("!!python/object/apply:os.system ['false']")

    def test_contract_rejects_nonexecuting_gates_and_untrusted_source_bindings(self):
        def change_runs(document, job, transform):
            for step in document["jobs"][job]["steps"]:
                if "run" in step:
                    step["run"] = transform(step["run"])

        def replace_gate(document, wrapper):
            change_runs(document, "publish-pypi", lambda body: wrapper(body) if "check-publish" in body else body)

        mutations = {
            "echoed publication guards": lambda d: replace_gate(d, lambda body: "\n".join("echo " + line for line in body.splitlines())),
            "disabled full tests": lambda d: change_runs(d, "build", lambda body: "if false; then\n  npm test\nfi" if body == "npm test" else body),
            "self-claimed source": lambda d: change_runs(d, "publish-pypi", lambda body: body.replace('"$GITHUB_SHA"', '"$(python -c \'import json,os; print(json.load(open(os.environ["RUNNER_TEMP"]+"/sdk-release/manifest.json"))["source"])\')"')),
            "ignored guard failure": lambda d: replace_gate(d, lambda body: "\n".join(line + " || true" for line in body.splitlines())),
            "guarded by false branch": lambda d: replace_gate(d, lambda body: "if false; then\n" + body + "\nfi"),
            "source environment override": lambda d: d["jobs"]["publish-pypi"]["env"].update(GITHUB_SHA="0" * 40),
            "digest from artifact environment": lambda d: d["jobs"]["publish-pypi"]["env"].update(MANIFEST_SHA256="${{ inputs.version }}"),
            "run shell turned into echo": lambda d: next(s for s in d["jobs"]["publish-pypi"]["steps"] if "check-publish" in s.get("run", "")).update(shell="echo {0}"),
            "workflow defaults disable shell": lambda d: d.update(defaults={"run": {"shell": "echo {0}"}}),
            "untrusted checkout ref": lambda d: d["jobs"]["publish-pypi"]["steps"][0]["with"].update(ref="untrusted"),
            "echoed compatibility verification": lambda d: change_runs(d, "python-compatibility", lambda body: "echo " + body if "--python-only" in body else body),
            "skipped download": lambda d: next(s for s in d["jobs"]["publish-pypi"]["steps"] if s.get("uses", "").startswith("actions/download-artifact@")).update({"if": "${{ false }}"}),
            "publish before verification": lambda d: d["jobs"]["publish-pypi"]["steps"].insert(0, d["jobs"]["publish-pypi"]["steps"].pop()),
        }
        original, source = self.load("release-sdks.yml")
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaises((AssertionError, KeyError, ValueError, TypeError, StopIteration)):
                    contract(changed, source, True)

    def test_validation_rejects_test_commands_hidden_in_inactive_shell(self):
        document, source = self.load("validate.yml")
        next(step for step in document["jobs"]["postman"]["steps"] if step.get("run") == "npm test")["run"] = "if false; then\n npm test\nfi"
        with self.assertRaises(AssertionError):
            contract(document, source, False)

    def test_npm_release_disables_ambient_npmrc_without_breaking_the_cli(self):
        document, _ = self.load("release-sdks.yml")
        with tempfile.TemporaryDirectory(prefix="cogneris-npm-config-") as directory:
            env = dict(os.environ)
            for name in ("NPM_CONFIG_USERCONFIG", "NPM_CONFIG_GLOBALCONFIG"):
                env[name] = document["jobs"]["publish-npm"]["env"][name].replace("${{ github.workspace }}", directory + "/checkout")
            result = subprocess.run(["npm", "config", "get", "registry"], cwd=directory,
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "https://registry.npmjs.org/")


if __name__ == "__main__":
    unittest.main()
