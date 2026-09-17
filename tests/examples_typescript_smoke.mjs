import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { cp, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test, { after, before } from "node:test";
import { pathToFileURL, fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const temporaryDirectory = await mkdtemp(path.join(os.tmpdir(), "cogneris-ts-example-"));
const sdkDirectory = path.join(temporaryDirectory, "sdk");
const consumerDirectory = path.join(temporaryDirectory, "consumer");
const documentMarker = "document-content-must-not-be-logged";
const extractedMarker = "extracted-field-must-not-be-logged";
const responseMarker = "raw-response-must-not-be-logged";
const apiKey = "test-api-key-must-not-be-logged";
const jobId = "11111111-1111-4111-8111-111111111111";

let sdk;
let example;
let server;
let baseUrl;
let requests = [];

function json(response, status, body, headers = {}) {
  response.writeHead(status, { "Content-Type": "application/json", ...headers });
  response.end(JSON.stringify(body));
}

before(async () => {
  await cp(path.join(root, "sdks", "typescript"), sdkDirectory, {
    recursive: true,
    filter: (source) => !source.includes(`${path.sep}dist${path.sep}`) &&
      !source.endsWith(`${path.sep}dist`),
  });
  execFileSync(
    path.join(root, "node_modules", ".bin", "tsc"),
    ["-p", path.join(sdkDirectory, "tsconfig.json")],
    { cwd: sdkDirectory, stdio: "pipe" },
  );
  const packedName = execFileSync(
    "npm",
    ["pack", "--pack-destination", temporaryDirectory, "--silent"],
    { cwd: sdkDirectory, encoding: "utf8" },
  ).trim().split("\n").at(-1);

  await cp(
    path.join(root, "examples", "typescript", "quickstart.mjs"),
    path.join(consumerDirectory, "quickstart.mjs"),
  );
  await writeFile(
    path.join(consumerDirectory, "package.json"),
    `${JSON.stringify({ private: true, type: "module" })}\n`,
  );
  execFileSync(
    "npm",
    ["install", "--ignore-scripts", "--no-audit", "--no-fund", path.join(temporaryDirectory, packedName)],
    { cwd: consumerDirectory, stdio: "pipe" },
  );
  const requireFromInstall = createRequire(path.join(consumerDirectory, "package.json"));
  sdk = requireFromInstall("@cogneris-ai/document-ai-sdk");
  example = await import(pathToFileURL(path.join(consumerDirectory, "quickstart.mjs")));

  server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    requests.push({
      authorization: request.headers.authorization,
      body: body.toString(),
      method: request.method,
      path: request.url,
    });
    if (request.method === "POST" && request.url === "/Document/extraction") {
      if (body.includes("application-error-document")) {
        json(response, 200, {
          data: { metadata: { secretField: extractedMarker } },
          meta: { httpStatusCode: 200, messages: [responseMarker] },
          hasErrors: true,
        });
      } else if (body.includes("error-document")) {
        json(response, 500, { title: responseMarker, detail: extractedMarker });
      } else {
        json(response, 200, {
          data: { metadata: { secretField: extractedMarker } },
          meta: { httpStatusCode: 200 },
          hasErrors: false,
        });
      }
      return;
    }
    if (request.method === "POST" && request.url === "/api/v1/document-jobs") {
      json(response, 202, {
        jobId,
        status: "Queued",
        statusUrl: `/api/v1/document-jobs/${jobId}`,
        retryAfterSeconds: 0,
      }, { "Retry-After": "0" });
      return;
    }
    if (request.method === "GET" && request.url === `/api/v1/document-jobs/${jobId}`) {
      json(response, 200, {
        jobId,
        operation: "Extraction",
        status: "Succeeded",
        outputReference: responseMarker,
      });
      return;
    }
    json(response, 404, { title: responseMarker });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  if (server) await new Promise((resolve) => server.close(resolve));
  await rm(temporaryDirectory, { recursive: true, force: true });
});

function capture() {
  let stdout = "";
  let stderr = "";
  return {
    io: {
      stdout: { write: (value) => { stdout += String(value); } },
      stderr: { write: (value) => { stderr += String(value); } },
    },
    read: () => ({ stdout, stderr }),
  };
}

async function invoke(argumentsList, fileContents = documentMarker) {
  const filePath = path.join(temporaryDirectory, "sample.pdf");
  await writeFile(filePath, fileContents);
  const output = capture();
  const regions = [];
  const exitCode = await example._runExampleForTesting({
    argumentsList: argumentsList.map((value) => value === "$FILE" ? filePath : value),
    environment: { COGNERIS_API_KEY: apiKey, COGNERIS_REGION: "eu" },
    io: output.io,
    _createClientForTesting: (options) => {
      regions.push(options.region);
      return new sdk.CognerisClient({ ...options, _baseUrlForTesting: baseUrl });
    },
  });
  return { exitCode, regions, ...output.read() };
}

test("installed SDK quickstart runs sync upload and emits only a safe summary", async () => {
  requests = [];
  const result = await invoke(["extract", "$FILE"]);
  assert.equal(result.exitCode, 0, result.stderr);
  assert.deepEqual(result.regions, ["eu"]);
  assert.deepEqual(JSON.parse(result.stdout), {
    operation: "extraction",
    hasErrors: false,
    httpStatusCode: 200,
  });
  assert.equal(result.stderr, "");
  assert.equal(requests.at(-1).authorization, `Bearer ${apiKey}`);
  assert.match(requests.at(-1).body, new RegExp(documentMarker));
  for (const sensitive of [apiKey, documentMarker, extractedMarker, responseMarker]) {
    assert.equal((result.stdout + result.stderr).includes(sensitive), false);
  }
});

test("installed SDK quickstart submits and polls without printing output references", async () => {
  requests = [];
  const inputReference = "private/input/reference.pdf";
  const result = await invoke(["async", "Extraction", inputReference]);
  assert.equal(result.exitCode, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), {
    operation: "Extraction",
    jobId,
    status: "Succeeded",
  });
  assert.equal(result.stderr, "");
  assert.deepEqual(JSON.parse(requests.find((request) =>
    request.method === "POST" && request.path === "/api/v1/document-jobs").body), {
    operation: "Extraction",
    inputReference,
  });
  assert.equal(result.stdout.includes(responseMarker), false);
  assert.equal(result.stdout.includes(inputReference), false);
});

test("quickstart reports controlled errors without raw bodies or credentials", async () => {
  const result = await invoke(["extract", "$FILE"], "error-document");
  assert.equal(result.exitCode, 1);
  assert.equal(result.stdout, "");
  assert.equal(result.stderr, "Cogneris API request failed with HTTP 500.\n");
  for (const sensitive of [apiKey, extractedMarker, responseMarker]) {
    assert.equal(result.stderr.includes(sensitive), false);
  }
});

test("quickstart treats a 200 application-error envelope as a safe failure", async () => {
  const result = await invoke(["extract", "$FILE"], "application-error-document");
  assert.equal(result.exitCode, 1);
  assert.equal(result.stdout, "");
  assert.equal(result.stderr, "Cogneris extraction reported an application error.\n");
  for (const sensitive of [apiKey, extractedMarker, responseMarker]) {
    assert.equal(result.stderr.includes(sensitive), false);
  }
});

test("documented invocation has no public base URL input", async () => {
  const source = await readFile(path.join(root, "examples", "typescript", "quickstart.mjs"), "utf8");
  assert.equal(source.includes("COGNERIS_BASE_URL"), false);
  assert.equal(source.includes("--base-url"), false);
});
