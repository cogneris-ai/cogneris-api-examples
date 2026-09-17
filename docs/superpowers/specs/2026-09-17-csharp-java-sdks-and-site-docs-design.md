# C# and Java SDKs with Public Site Documentation

**Date:** 2026-09-17

**Ticket:** XTRAK-1615

**Status:** Approved architecture, pending written-spec review

**Repositories:** `cogneris-api-examples`, then `cogneris-site`

## Objective

Add production-shaped C#/.NET and Java SDK artifacts to the existing public SDK
pipeline, with the same supported document-processing workflow as the TypeScript
and Python SDKs. After the SDK change is merged and independently verified,
update the public site to document the new languages without implying that the
packages are already available from NuGet or Maven Central.

The work is split into two dependent changes:

1. Generate, package, and test the C# and Java SDKs in
   `cogneris-api-examples`.
2. Use the merged SDK evidence to update documentation and public claims in
   `cogneris-site`.

Each repository receives its own branch, pull request, verification, and merge.
The site change starts only after the SDK pull request is merged.

## Scope

### Included

- A C# package named `Cogneris.DocumentAI`, targeting .NET 8 or newer.
- A Java package with Maven coordinates
  `ai.cogneris:cogneris-document-ai-sdk`, targeting Java 17 or newer.
- Generated low-level API operations and models from
  `openapi/cogneris-openapi.yaml`.
- An idiomatic, hand-maintained `CognerisClient` facade in both languages.
- Apache License 2.0 metadata and packaged `LICENSE` and `NOTICE` files.
- Deterministic generation, manifest hashing, release artifact construction,
  isolated consumer verification, CI coverage, and release dry-run coverage.
- Public documentation pages for both SDKs and updates to the existing SDK
  overview, quickstart, language matrix, claims, sitemap, and LLM corpus.

### Excluded

- Publishing packages to NuGet or Maven Central in this change.
- A Kotlin-specific SDK, C# or Java CLI, mobile SDK, or framework adapter.
- Changes to service access, authentication policy, API behavior, or backend
  implementation.
- Any license grant for trademarks, logos, service access, or backend code.
- Claims that an SDK is installable from a public registry before registry
  publication has independently succeeded.

## Architectural approach

Use OpenAPI Generator 7.25.0 for both new languages. Invoke the pinned generator
through `uvx` with `openapi-generator-cli[jdk4py]`, which provides its own JDK and
does not depend on Java being installed on the contributor host.

This extends the repository's current model:

- the canonical OpenAPI document remains the contract source;
- language generators produce the low-level transport, operations, and models;
- repository-owned overlays provide the stable, ergonomic public client;
- generation occurs in a temporary staging area and replaces outputs only after
  all checks pass;
- committed output hashes record reproducibility in `sdks/manifest.json`.

The generated surface is intentionally not the primary onboarding API. Public
examples use `CognerisClient`; advanced consumers may use the generated types
and operations.

### Alternatives considered

- **Kiota:** rejected because it would expose additional Kiota abstractions and
  adapters in both package dependency graphs, making the new SDKs less aligned
  with the existing lightweight facades.
- **Fully hand-written clients:** rejected because duplicating all schemas and
  operations would increase OpenAPI drift risk and ongoing maintenance cost.
- **Host-installed OpenAPI Generator:** rejected because it introduces an
  undeclared Java dependency and weakens local and CI reproducibility.

## Public client contracts

Both languages expose the same workflow concepts already supported by the
TypeScript and Python SDKs:

- `extract`: synchronously extract a document;
- `submitJob`: submit asynchronous extraction;
- `getJob`: retrieve job state;
- `waitForJob`: poll until a terminal state, honoring server retry guidance;
- `cancelJob`: cancel a job;
- `us` and `eu`: explicit regional endpoint presets;
- bearer-token authentication;
- multipart document upload;
- typed errors that do not disclose authorization values or document contents.

The wire format, envelope handling, terminal job states, retry behavior, and
error sanitization must match the current TypeScript and Python behavior. The
implementation uses idiomatic cancellation and timeout primitives in each
language rather than inventing a cross-language abstraction.

### C# surface

- Package ID and root namespace: `Cogneris.DocumentAI`.
- Minimum supported runtime: .NET 8.
- Async operations follow .NET naming conventions and accept
  `CancellationToken` where network or polling work occurs.
- Configuration makes API key and regional/custom base URL explicit.
- Release artifact: `.nupkg` built from the package project.

### Java surface

- Maven coordinates: `ai.cogneris:cogneris-document-ai-sdk`.
- Root package: `ai.cogneris.documentai`.
- Minimum supported runtime: Java 17.
- Polling and request APIs expose bounded timeout and interruption behavior
  appropriate for Java callers.
- Configuration makes API key and regional/custom base URL explicit.
- Release artifact: `.jar` with its POM metadata.

## Generation and repository layout

Add `csharp` and `java` entries to the generator configuration. Each entry pins:

- generator identity and version;
- package/module coordinates;
- runtime target;
- output directory;
- repository-owned overlay directory;
- legal file sources;
- forbidden-route and generation validation rules.

`scripts/generate-sdks.mjs` will orchestrate all four SDKs as a single atomic
generation transaction. A failure in any language leaves every committed SDK
directory unchanged. Generated output will be normalized to remove volatile
files before hashing and commit.

Expected top-level outputs are:

```text
sdks/
  csharp/
  java/
  python/
  typescript/
  manifest.json
scripts/
  sdk-config/
    csharp/
    java/
```

The precise generated substructure may follow generator conventions, but the
public facade, package metadata, legal files, and test entry points remain owned
by this repository.

## Packaging and licensing

Extend the release builder to construct five independently consumable artifacts:

1. TypeScript SDK tarball;
2. CLI tarball;
3. Python wheel;
4. C# NuGet package;
5. Java JAR and its package metadata.

For the two new artifacts, verification must inspect the built archive rather
than only source files. It must prove:

- exact package identity and version;
- Apache-2.0 SPDX license metadata;
- inclusion of `LICENSE` and `NOTICE`;
- expected runtime target and dependency metadata;
- absence of repository-only source references;
- correspondence between built contents and the generated manifest where
  applicable.

The authorized copyright notice is `Copyright 2026 COGNERIS, INC.`.

This design builds and publishes artifacts to the GitHub release workflow only.
NuGet and Maven Central publishing credentials, namespaces, signing, and owner
readiness are separate release work and remain explicit blockers for registry
availability claims.

## Testing strategy

Testing is layered so source-tree success cannot conceal a broken package.

### Contract and generation tests

- generator versions and language settings are pinned;
- generation is deterministic and atomic;
- generated clients contain the required document and job operations;
- internal/forbidden routes are absent;
- manifest hashes cover C# and Java outputs;
- a deliberately failed generation proves that committed SDKs remain intact.

### Loopback behavior tests

Each facade is tested against a local HTTP server that records requests and
returns controlled responses. Tests prove:

- bearer authorization is emitted correctly without leaking into failures;
- multipart upload contains the expected document and fields;
- synchronous and asynchronous envelopes are decoded correctly;
- polling observes pending and terminal states;
- `Retry-After` is honored within the caller's timeout;
- cancellation stops in-flight or polling work;
- invalid/error responses become safe typed errors.

### Isolated package-consumer tests

Consumers run outside the repository source tree and install only the produced
artifact. The .NET consumer must reference the `.nupkg`, never the SDK project or
a `ProjectReference`. The Java consumer must resolve the built package from an
isolated local repository or staged Maven layout, never compile against the SDK
source directory.

These tests compile and execute against .NET 8 and Java 17, respectively. They
repeat a minimal loopback request so package content and runtime behavior are
both exercised.

### Existing SDK regression coverage

The TypeScript, CLI, and Python artifact checks remain required. The release dry
run and CI workflow fail unless all five artifacts build and pass their isolated
consumer checks.

## CI and release workflow

Update the SDK verification workflow to install only declared tooling and run:

1. repository unit and contract tests;
2. deterministic generation checks;
3. C# build/test on .NET 8;
4. Java build/test on Java 17;
5. all five release package builds;
6. archive metadata and legal-file inspection;
7. isolated package-consumer tests;
8. release dry-run artifact upload.

Registry publication jobs for NuGet and Maven are not added. The workflow must
make that distinction visible so a green build cannot be interpreted as public
registry availability.

## Public site update

The site phase begins only after the SDK pull request is merged and the merged
commit and package verification are available as evidence.

Add:

- `src/docs-dotnet-sdk.html`;
- `src/docs-java-sdk.html`.

Update:

- `src/docs-quickstart.html`;
- the SDK language matrix and navigation;
- `src/document-capture-sdk.html`;
- claim-boundary evidence and checks;
- sitemap `lastmod` values;
- `src/llms-full.txt`;
- the internationalization catalog required by changed English prose.

The new pages show source/build usage and API examples grounded in the merged
SDK. They must explicitly state that NuGet and Maven Central publication is not
yet available. Install commands that would resolve from those public registries
must not be presented as currently working.

The site repository's existing prose, SEO, accessibility, internal-link, claim,
sitemap, and i18n gates remain mandatory. Any new gate is added consistently to
both CI and deployment pipelines.

## Delivery sequence and evidence

### Phase 1: SDK repository

1. Add failing tests for configuration, generation, facades, artifacts, and
   isolated consumers.
2. Implement pinned C# generation and its facade.
3. Implement pinned Java generation and its facade.
4. Extend manifest, release builder, CI, and dry run.
5. Run the complete local verification available on the host.
6. Commit, push, open the SDK pull request, and merge only after required checks
   pass.
7. Record merged commit, CI result, and artifact evidence.

### Phase 2: site repository

1. Create a new branch/worktree from the then-current `origin/main`.
2. Add the two language pages and update shared documentation and claims using
   Phase 1 evidence.
3. Regenerate LLM, sitemap, and i18n outputs.
4. Run all site quality gates.
5. Commit, push, open the site pull request, and merge only after required checks
   pass.
6. Verify the normal post-merge deployment state without bypassing its workflow.

## Failure handling

- Generator or overlay failure: abort the staged generation and preserve every
  existing SDK output.
- Missing runtime or packaging tool: fail verification with the exact missing
  prerequisite; do not commit an unverified artifact path.
- Package-only consumer failure: treat the artifact as unreleasable even if
  source tests pass.
- SDK pull request not merged: do not begin or publish the site claim update.
- Registry package unavailable: retain explicit source/build-only wording.
- Site quality or deployment failure: keep the site branch/PR for remediation
  and do not describe the documentation as live.

## Acceptance criteria

The implementation is complete when:

- both SDKs are generated reproducibly from the canonical OpenAPI contract;
- both facades provide the approved document and async-job workflows;
- `.nupkg` and `.jar` artifacts contain correct identity, version, license, and
  legal files;
- isolated .NET 8 and Java 17 consumers compile and pass loopback behavior tests;
- existing TypeScript, CLI, and Python package proofs remain green;
- SDK CI and release dry run validate all five artifacts;
- the SDK pull request is merged and its evidence is recorded;
- the site documents C# and Java accurately, including registry limitations;
- site checks pass, the site pull request is merged, and deployment status is
  verified;
- no unsupported public-registry, service-access, trademark, or backend-license
  claim is introduced.

## References

- [OpenAPI Generator C# client documentation](https://openapi-generator.tech/docs/generators/csharp/)
- [OpenAPI Generator Java client documentation](https://openapi-generator.tech/docs/generators/java/)
- [OpenAPI Generator CLI installation](https://openapi-generator.tech/docs/installation/)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
