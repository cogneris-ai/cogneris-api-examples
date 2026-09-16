import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { cp, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test, { after, before } from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sdkDirectory = path.join(root, "sdks", "typescript");
const temporaryDirectory = await mkdtemp(path.join(os.tmpdir(), "cogneris-ts-sdk-smoke-"));
const packageDirectory = path.join(temporaryDirectory, "package");
let sdk;
let server;
let baseUrl;
let requests = [];
let pollingCounts = new Map();

const jobId = "11111111-1111-4111-8111-111111111111";
const failedJobId = "22222222-2222-4222-8222-222222222222";
const endlessJobId = "33333333-3333-4333-8333-333333333333";

function json(response, status, body, headers = {}) {
  response.writeHead(status, { "Content-Type": "application/json", ...headers });
  response.end(JSON.stringify(body));
}

before(async () => {
  await cp(sdkDirectory, packageDirectory, {
    recursive: true,
    filter: (source) => !source.includes(`${path.sep}dist${path.sep}`) && !source.endsWith(`${path.sep}dist`),
  });
  execFileSync(
    path.join(root, "node_modules", ".bin", "tsc"),
    ["-p", path.join(packageDirectory, "tsconfig.json")],
    { cwd: packageDirectory, stdio: "pipe" },
  );
  const packedName = execFileSync(
    "npm",
    ["pack", "--pack-destination", temporaryDirectory, "--silent"],
    { cwd: packageDirectory, encoding: "utf8" },
  ).trim().split("\n").at(-1);
  await writeFile(
    path.join(temporaryDirectory, "package.json"),
    `${JSON.stringify({ private: true })}\n`,
  );
  execFileSync(
    "npm",
    ["install", "--ignore-scripts", "--no-audit", "--no-fund", path.join(temporaryDirectory, packedName)],
    { cwd: temporaryDirectory, stdio: "pipe" },
  );
  const requireFromInstall = createRequire(path.join(temporaryDirectory, "package.json"));
  sdk = requireFromInstall("@cogneris/document-ai-sdk");

  server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    requests.push({
      authorization: request.headers.authorization,
      body,
      contentType: request.headers["content-type"],
      method: request.method,
      path: request.url,
    });

    if (request.method === "POST" && request.url === "/Document/extraction") {
      if (body.includes("reject-this-document")) {
        json(response, 415, { code: "unsupported_media_type", title: "Unsupported document" });
      } else {
        json(response, 200, { data: { accepted: true }, meta: { status: 200 }, hasErrors: false });
      }
      return;
    }
    if (request.method === "POST" && request.url === "/api/v1/document-jobs") {
      json(
        response,
        202,
        { jobId, status: "Queued", statusUrl: `/api/v1/document-jobs/${jobId}`, retryAfterSeconds: 1 },
        { Location: `/api/v1/document-jobs/${jobId}`, "Retry-After": "1" },
      );
      return;
    }
    if (request.method === "GET" && request.url?.startsWith("/api/v1/document-jobs/")) {
      const id = request.url.split("/").at(-1);
      const count = (pollingCounts.get(id) ?? 0) + 1;
      pollingCounts.set(id, count);
      if (id === failedJobId) {
        json(response, 200, { jobId: id, operation: "Extraction", status: "Failed", failureCode: "processing_failed", retryable: false });
      } else if (id === endlessJobId) {
        json(response, 200, { jobId: id, operation: "Extraction", status: "Processing" }, { "Retry-After": "0" });
      } else if (count === 1) {
        json(response, 200, { jobId: id, operation: "Extraction", status: "Processing" }, { "Retry-After": "1" });
      } else {
        json(response, 200, { jobId: id, operation: "Extraction", status: "Succeeded", outputReference: "result/ref" });
      }
      return;
    }
    if (request.method === "POST" && request.url === `/api/v1/document-jobs/${jobId}/cancel`) {
      json(response, 200, { jobId, operation: "Extraction", status: "Cancelled" });
      return;
    }
    json(response, 404, { code: "not_found", title: "Not found" });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
  await rm(temporaryDirectory, { recursive: true, force: true });
});

test("installed package exports the maintained helper surface", () => {
  assert.equal(typeof sdk.CognerisClient, "function");
  assert.equal(typeof sdk.CognerisError, "function");
  assert.equal(typeof sdk.CognerisApiError, "function");
  assert.equal(typeof sdk.CognerisJobTerminalError, "function");
  assert.equal(typeof sdk.CognerisMaxAttemptsError, "function");
  assert.equal(new sdk.CognerisApiError("test") instanceof sdk.CognerisError, true);
  assert.equal(sdk.cognerisBaseUrl("us"), "https://api-us.cogneris.ai");
  assert.equal(sdk.cognerisBaseUrl("eu"), "https://api-eu.cogneris.ai");
  assert.throws(() => sdk.cognerisBaseUrl("apac"), /us.*eu/);
  assert.deepEqual(sdk.COGNERIS_REGION_URLS, {
    us: "https://api-us.cogneris.ai",
    eu: "https://api-eu.cogneris.ai",
  });
});

test("client sends bearer auth and multipart bytes without including them in errors", async () => {
  requests = [];
  const client = new sdk.CognerisClient({
    apiKey: "test-api-key",
    region: "us",
    _baseUrlForTesting: baseUrl,
  });
  const result = await client.extract(new Blob(["ordinary-document"]), { fileName: "sample.pdf" });
  assert.equal(result.data.accepted, true);
  const upload = requests.at(-1);
  assert.equal(upload.authorization, "Bearer test-api-key");
  assert.match(upload.contentType, /^multipart\/form-data; boundary=/);
  assert.match(upload.body.toString(), /ordinary-document/);
  assert.match(upload.body.toString(), /sample\.pdf/);

  await assert.rejects(
    () => client.extract(new Blob(["reject-this-document"]), { fileName: "bad.exe" }),
    (error) => {
      assert.equal(error instanceof sdk.CognerisApiError, true);
      assert.equal(error.status, 415);
      assert.equal(error.code, "unsupported_media_type");
      assert.doesNotMatch(error.message, /reject-this-document|test-api-key/);
      return true;
    },
  );
});

test("job helpers submit, honor Retry-After, stop on success, and cancel", async () => {
  requests = [];
  pollingCounts = new Map();
  const client = new sdk.CognerisClient({ apiKey: "test-api-key", region: "eu", _baseUrlForTesting: baseUrl });
  const submission = await client.submitJob("Extraction", "input/ref");
  assert.equal(submission.jobId, jobId);
  const submitted = requests.at(-1);
  assert.deepEqual(JSON.parse(submitted.body.toString()), { operation: "Extraction", inputReference: "input/ref" });

  const started = Date.now();
  const job = await client.waitForJob(jobId, { maxAttempts: 3 });
  assert.equal(job.status, "Succeeded");
  assert.equal(pollingCounts.get(jobId), 2);
  assert.ok(Date.now() - started >= 900, "Retry-After: 1 should delay the next poll");

  const cancelled = await client.cancelJob(jobId);
  assert.equal(cancelled.status, "Cancelled");
  assert.equal(requests.every((request) => request.authorization === "Bearer test-api-key"), true);
});

test("wait surfaces terminal failures and bounded-attempt exhaustion as typed errors", async () => {
  pollingCounts = new Map();
  const client = new sdk.CognerisClient({ apiKey: "test-api-key", _baseUrlForTesting: baseUrl });
  await assert.rejects(
    () => client.waitForJob(failedJobId, { maxAttempts: 3 }),
    (error) => {
      assert.equal(error instanceof sdk.CognerisJobTerminalError, true);
      assert.equal(error.job.status, "Failed");
      assert.equal(error.failureCode, "processing_failed");
      return true;
    },
  );
  await assert.rejects(
    () => client.waitForJob(endlessJobId, { maxAttempts: 2 }),
    (error) => {
      assert.equal(error instanceof sdk.CognerisMaxAttemptsError, true);
      assert.equal(error.attempts, 2);
      return true;
    },
  );
  assert.equal(pollingCounts.get(endlessJobId), 2);
});
