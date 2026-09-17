# SDK release workflow

The registry names are `@cogneris-ai/document-ai-sdk`,
`@cogneris-ai/document-ai-cli`, and `cogneris-document-ai-sdk`. All three
packages remain unpublished until the first authorized release completes.

For local generation, builds, and verification, install Node.js 24, npm 10+,
Python 3.12, and `uv`/`uvx` on `PATH`, then run `npm ci`. The TypeScript
generator requires Node.js >=22.18.0; the installed SDK and CLI require only
Node.js >=20.0.0 for their built-in `File`/`fetch` runtime and npm 9+ for local
installation. The Python wheel requires Python `>=3.9,<4.0`; uv is used for
building and isolated verification here, and is not needed for ordinary Python
runtime use or installation of an existing wheel with pip. `uv build` resolves
the wheel build backend declared in `pyproject.toml`.

Python generation uses `openapi-python-client==0.26.2` with an explicit
`uvx --with ruff==0.13.3` dependency pin from `scripts/sdk-config/generators.json`.
This is the formatter version resolved by the existing generator environment;
the manifest records both pins. Do not upgrade the formatter independently
without regenerating and checking the committed SDK output.

`.github/workflows/release-sdks.yml` accepts only a manual `workflow_dispatch`.
Supply the exact SemVer already committed in all three package versions (currently
`0.1.0`, without a `v` prefix). The default `dry_run: true` executes public validation
scripts, packs both npm packages, builds the Python wheel, installs those exact
artifacts in a fresh consumer, and uploads them with a SHA-256 manifest for 14 days.
It requires no publishing credentials or OIDC permission. Dry runs upload unsigned
integrity metadata; they do not claim a signed provenance attestation.

One build supplies the Python 3.9–3.14 compatibility matrix. Every matrix job
verifies and installs the same wheel and runs installed SDK/example loopback tests;
it does not regenerate SDKs or rebuild packages. The full Node 24/Python 3.12 job
retains the Postman tests and runs a high-severity dependency audit, SDK drift,
SDK verification, CLI build/tests, documentation/examples, and the aggregate suite.
These are the currently tested Python minors within the package's declared
`>=3.9,<4.0` range.

Build outputs include an immutable Actions artifact ID and the manifest digest.
Consumers require that exact ID, independently compare the manifest digest, verify
all package digests, source commit, names, versions, and the CLI's exact SDK
dependency. Publication jobs do not rebuild or install package code. They publish
the verified tarballs or a byte-for-byte copy of the verified wheel.

## External gates before a real release

An owner must complete these steps outside this workflow:

1. Confirm package-name ownership and public distribution/license permission.
   Keep the owner-approved GitHub Security Advisories channel documented in
   `SUPPORT.md` enabled. Configure `sdk-release` as a protected GitHub environment
   with an owner review gate and deployment restricted to `main`. YAML referencing
   an environment cannot itself create its reviewer protection. Only then set the
   environment configuration variable `SDK_RELEASE_READY` to the string `true`.
2. For npm, confirm ownership/bootstrap of **both** `@cogneris-ai` package names.
   Their committed metadata must use
   `git+https://github.com/cogneris-ai/cogneris-api-examples.git`. Register a
   trusted publisher for each package, specifying this repository,
   `release-sdks.yml`, and `sdk-release`; authorize direct `npm publish` explicitly.
   Initial npm registration/bootstrap needs an owner-controlled process outside
   this workflow; there is no token-based bootstrap fallback here. Confirm the
   repository is public for npm provenance, then set the environment configuration variable
   `SDK_NPM_TRUSTED_PUBLISHING_READY` to `true`.
3. For PyPI, register a pending or existing trusted publisher for
   `cogneris-document-ai-sdk`, this repository, `release-sdks.yml`, and environment
   `sdk-release`. Set `SDK_PYPI_TRUSTED_PUBLISHING_READY` to `true` only after the
   registry configuration is complete.

Real jobs require `dry_run: false`, the `main` ref, successful build and all Python
compatibility jobs, and the protected environment. They alone receive
`id-token: write`. No long-lived tokens, secret inputs, or fallback credentials
are configured. npm requires CLI >=11.5.1, a GitHub-hosted runner, and matching
repository metadata; PyPI authenticates through the pinned PyPA publishing action.
The registry's OIDC exchange is the final authority and fails if its trusted
publisher configuration does not match. Readiness variables are owner declarations,
not proof that a remote publisher is configured. npm's OIDC status cannot be tested
with `npm whoami`.

npm publishes with provenance; PyPI publishes with PEP 740 attestations. No GitHub
attestation permission is requested because no GitHub attestation API is used.
The two registry jobs are independent: a release can partially succeed, and an
already published version is not overwritten or silently skipped. Resolve a
partial release with an owner-reviewed recovery decision.

Local artifact checks (no registry publication):

```bash
release_root=$(mktemp -d)
npm run pack:sdks -- --version 0.1.0 --output "$release_root/artifacts"
manifest_sha=$(shasum -a 256 "$release_root/artifacts/manifest.json" | cut -d ' ' -f 1)
npm run verify:artifacts -- --version 0.1.0 --artifacts "$release_root/artifacts" \
  --manifest-sha256 "$manifest_sha" --source "$(git rev-parse HEAD)"
npm run test:workflows
```

The artifact builder refuses existing output directories and builds only in
owned temporary copies. Packaged source trees, the release builder, and root
dependency declarations must match the committed `HEAD`, including the index;
modified, deleted, staged, or untracked build inputs fail before packaging.
The builder uses a verified snapshot of Git object bytes, so a later source edit
cannot silently enter an artifact labeled with the earlier commit. Unrelated
files and excluded dependency/cache/build directories are preserved and excluded.

Verification inspects archive metadata without filesystem extraction. Only
regular files and canonical empty directory markers are accepted; links, special
files, unsafe or colliding paths, tar PAX extensions, and ZIP extra metadata are
rejected. The current package builders need no such extensions. Local and central
ZIP headers must agree, preventing alternate filename/link interpretations.
Inspection caps each archive at 16 MiB, 4,096 entries, 4 MiB per uncompressed
entry, and 32 MiB total uncompressed content. Package/manifest metadata is
limited to 64 KiB, names to 1 KiB, ZIP comments to 4 KiB, and the ZIP central
directory to 1 MiB. Only stored/deflate ZIP compression is accepted, avoiding
codecs with additional dictionary memory requirements. Size checks precede
archive hashing or bulk metadata reads;
tar extension headers are rejected before their payload is parsed. These
conservative limits cover the current npm and uv output without extraction.
Registry dependency downloads may be needed for clean installation; tests contact
only loopback API fixtures.

References: [npm trusted publishing](https://docs.npmjs.com/trusted-publishers/),
[npm provenance](https://docs.npmjs.com/generating-provenance-statements/),
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
[PyPI attestations](https://docs.pypi.org/attestations/).
