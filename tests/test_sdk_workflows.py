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
REQUIRED = {"npm test", "npm run check:sdks", "npm run verify:sdks",
            "npm run test:cli", "npm run build:cli", "npm run test:docs",
            "npm run pack:sdks", "npm run verify:artifacts"}
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


def runs(job):
    return "\n".join(step.get("run", "") for step in job["steps"])


def contract(document, source, release):
    assert document["permissions"] == {"contents": "read"}
    for job_name, job in document["jobs"].items():
        publish = release and job_name in {"publish-npm", "publish-pypi"}
        assert job.get("permissions") == ({"contents": "read", "id-token": "write"}
                                      if publish else {"contents": "read"})
        assert not job.get("continue-on-error")
        for step in job["steps"]:
            if "uses" in step:
                action, sha = step["uses"].split("@")
                assert action in ALLOWED_ACTIONS
                assert re.fullmatch(r"[0-9a-f]{40}", sha)
                assert re.search(re.escape(step["uses"]) + r"\s+# v\d[^\n]*", source)
                if action == "actions/checkout":
                    assert step["with"]["persist-credentials"] is False
                if action == "actions/setup-node":
                    assert str(step["with"]["node-version"]) == "24"
            assert not step.get("continue-on-error")
    assert "secrets." not in source
    main = document["jobs"]["build" if release else "postman"]
    assert "if" not in main
    for command in REQUIRED:
        assert any(re.search(r"(?m)^\s*" + re.escape(command) + r"(?:\s+--\s+.*)?\s*$",
                             step.get("run", "")) and "if" not in step
                   for step in main["steps"]), command
    compatibility = document["jobs"]["python-compatibility"]
    assert "if" not in compatibility
    assert all("if" not in step for step in compatibility["steps"])
    assert set(compatibility["strategy"]["matrix"]["python"]) == {
        "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"}
    assert compatibility["needs"] == ["build" if release else "postman"]
    assert "--python-only" in runs(compatibility)
    assert "--manifest-sha256" in runs(compatibility)
    assert "pack:sdks" not in runs(compatibility)
    if not release:
        assert set(document["on"]) == {"push", "pull_request"}
        assert document["on"]["push"]["branches"] == ["main"]
        return
    assert isinstance(document["on"], dict) and set(document["on"]) == {"workflow_dispatch"}
    inputs = document["on"]["workflow_dispatch"]["inputs"]
    assert inputs["version"]["required"] is True and inputs["version"]["type"] == "string"
    assert "default" not in inputs["version"]
    assert inputs["dry_run"]["type"] == "boolean" and inputs["dry_run"]["default"] is True
    assert set(document["jobs"]) == {"build", "python-compatibility", "publish-npm", "publish-pypi"}
    assert "check-version" in runs(main)
    assert main["outputs"]["manifest-sha256"] == "${{ steps.manifest.outputs.sha256 }}"
    assert main["outputs"]["artifact-id"] == "${{ steps.artifacts.outputs.artifact-id }}"
    for job_name in ("publish-npm", "publish-pypi"):
        job = document["jobs"][job_name]
        assert job["if"] == "${{ inputs.dry_run == false && github.ref == 'refs/heads/main' }}"
        assert job["environment"] == "sdk-release"
        assert set(job["needs"]) == {"build", "python-compatibility"}
        body = runs(job)
        assert "--manifest-sha256" in body and '"$RELEASE_VERSION"' in body
        assert "--source" in body and "check-publish" in body
        assert "npm ci" not in body and "pack:sdks" not in body and "uv build" not in body
        download = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/download-artifact@"))
        assert download["with"]["artifact-ids"] == "${{ needs.build.outputs.artifact-id }}"
        assert job["env"]["RELEASE_VERSION"] == "${{ inputs.version }}"
        assert job["env"]["SDK_RELEASE_READY"] == "${{ vars.SDK_RELEASE_READY }}"
        checks = next(i for i, step in enumerate(job["steps"]) if "check-publish" in step.get("run", ""))
        assert "if" not in job["steps"][checks]
        if job_name == "publish-npm":
            publish = next(i for i, step in enumerate(job["steps"]) if "npm publish" in step.get("run", ""))
            assert "--provenance" in body and "--ignore-scripts" in body
            assert "https://registry.npmjs.org" in body
        else:
            publish = next(i for i, step in enumerate(job["steps"]) if step.get("uses", "").startswith("pypa/gh-action-pypi-publish@"))
            assert job["steps"][publish]["with"]["attestations"] is True
            assert job["steps"][publish]["with"]["packages-dir"] == "${{ runner.temp }}/pypi/"
        assert checks < publish
    for job_name in ("build", "python-compatibility"):
        assert "npm publish" not in runs(document["jobs"][job_name])
        assert not any(step.get("uses", "").startswith("pypa/") for step in document["jobs"][job_name]["steps"])


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
