import assert from "node:assert/strict";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { cp, lstat, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const typescript = path.join(root, "node_modules", ".bin", "tsc");
const temporaryDirectories = [];

let installation;

function run(command, argumentsList, options = {}) {
  return execFileSync(command, argumentsList, {
    encoding: "utf8",
    stdio: "pipe",
    ...options,
  });
}

async function copyPackage(source, destination) {
  await cp(source, destination, {
    recursive: true,
    filter: (entry) => {
      const relative = path.relative(source, entry);
      return !relative.split(path.sep).includes("dist") &&
        !relative.split(path.sep).includes("node_modules");
    },
  });
}

async function installedPackages() {
  if (installation) return installation;
  installation = (async () => {
    const temporaryDirectory = await mkdtemp(path.join(os.tmpdir(), "cogneris-cli-smoke-"));
    temporaryDirectories.push(temporaryDirectory);
    const sdkDirectory = path.join(temporaryDirectory, "sdk");
    const cliDirectory = path.join(temporaryDirectory, "cli");
    const consumerDirectory = path.join(temporaryDirectory, "consumer");
    await copyPackage(path.join(root, "sdks", "typescript"), sdkDirectory);
    await copyPackage(path.join(root, "cli"), cliDirectory);

    run(typescript, ["-p", path.join(sdkDirectory, "tsconfig.json")], {
      cwd: sdkDirectory,
    });
    await writeFile(
      path.join(temporaryDirectory, "package.json"),
      `${JSON.stringify({
        private: true,
        dependencies: {
          "@cogneris-ai/document-ai-sdk": `file:${sdkDirectory}`,
        },
      }, null, 2)}\n`,
    );
    run("npm", ["install", "--ignore-scripts", "--no-audit", "--no-fund"], {
      cwd: temporaryDirectory,
    });
    run(typescript, [
      "-p",
      path.join(cliDirectory, "tsconfig.json"),
      "--typeRoots",
      path.join(root, "node_modules", "@types"),
    ], {
      cwd: cliDirectory,
    });

    const sdkTarball = run(
      "npm",
      ["pack", "--pack-destination", temporaryDirectory, "--silent"],
      { cwd: sdkDirectory },
    ).trim().split("\n").at(-1);
    const cliTarball = run(
      "npm",
      ["pack", "--pack-destination", temporaryDirectory, "--silent"],
      { cwd: cliDirectory },
    ).trim().split("\n").at(-1);

    await mkdir(consumerDirectory, { recursive: true });
    await writeFile(
      path.join(consumerDirectory, "package.json"),
      `${JSON.stringify({
        private: true,
        dependencies: {
          "@cogneris-ai/document-ai-cli": `file:${path.join(temporaryDirectory, cliTarball)}`,
          "@cogneris-ai/document-ai-sdk": `file:${path.join(temporaryDirectory, sdkTarball)}`,
        },
      }, null, 2)}\n`,
    );
    run("npm", ["install", "--ignore-scripts", "--no-audit", "--no-fund"], {
      cwd: consumerDirectory,
    });

    const requireFromInstall = createRequire(path.join(consumerDirectory, "package.json"));
    const cliPackagePath = requireFromInstall.resolve(
      "@cogneris-ai/document-ai-cli/package.json",
    );
    return {
      bin: path.join(consumerDirectory, "node_modules", ".bin", "cogneris"),
      cli: requireFromInstall(path.join(path.dirname(cliPackagePath), "dist", "run.js")),
      consumerDirectory,
      sdk: requireFromInstall("@cogneris-ai/document-ai-sdk"),
    };
  })();
  return installation;
}

function captureIo() {
  let stdout = "";
  let stderr = "";
  return {
    io: {
      stderr: { write: (value) => { stderr += String(value); } },
      stdout: { write: (value) => { stdout += String(value); } },
    },
    read: () => ({ stderr, stdout }),
  };
}

async function invoke(argumentsList, options = {}) {
  const { cli } = await installedPackages();
  const capture = captureIo();
  const code = await cli._runCliForTesting(argumentsList, {
    env: options.env ?? { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET" },
    io: capture.io,
    _createClientForTesting: options.clientFactory,
  });
  return { code, ...capture.read() };
}

function json(response, status, body, headers = {}) {
  response.writeHead(status, { "Content-Type": "application/json", ...headers });
  response.end(JSON.stringify(body));
}

function serviceEnvelope(status, data) {
  return {
    data,
    meta: { httpStatusCode: status, messages: [] },
    hasErrors: false,
  };
}

async function listen(server) {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  return `http://127.0.0.1:${address.port}`;
}

after(async () => {
  await Promise.all(
    temporaryDirectories.map((directory) => rm(directory, { recursive: true, force: true })),
  );
});

test("CLI package has the public identity, binary, and exact SDK dependency", async () => {
  const packageJson = JSON.parse(await readFile(path.join(root, "cli", "package.json"), "utf8"));
  assert.equal(packageJson.name, "@cogneris-ai/document-ai-cli");
  assert.equal(packageJson.version, "0.1.0");
  assert.deepEqual(packageJson.bin, { cogneris: "dist/bin.js" });
  assert.equal(packageJson.dependencies["@cogneris-ai/document-ai-sdk"], "0.1.0");
  assert.deepEqual(packageJson.repository, {
    type: "git",
    url: "git+https://github.com/cogneris-ai/cogneris-api-examples.git",
  });
});

test("installed packages declare the Node runtime needed for File and fetch uploads", async () => {
  const { consumerDirectory } = await installedPackages();
  for (const name of ["document-ai-sdk", "document-ai-cli"]) {
    const packageJson = JSON.parse(await readFile(
      path.join(consumerDirectory, "node_modules", "@cogneris-ai", name, "package.json"), "utf8",
    ));
    assert.deepEqual(packageJson.engines, { node: ">=20.0.0" });
  }
  assert.equal(typeof File, "function");
  assert.equal(typeof fetch, "function");
});

test("build leaves a durable installed SDK after temporary cleanup", async () => {
  const checkout = await mkdtemp(path.join(os.tmpdir(), "cogneris-cli-build-checkout-"));
  temporaryDirectories.push(checkout);
  for (const relative of ["cli", "sdks/typescript", "scripts/build-cli.mjs", "package.json", "package-lock.json"]) {
    const destination = path.join(checkout, relative);
    await mkdir(path.dirname(destination), { recursive: true });
    await copyPackage(path.join(root, relative), destination);
  }
  run("npm", ["ci", "--ignore-scripts", "--no-audit", "--no-fund"], { cwd: checkout });
  run(process.execPath, [path.join(checkout, "scripts", "build-cli.mjs")], { cwd: checkout });

  const dependencyPath = path.join(
    checkout,
    "node_modules",
    "@cogneris-ai",
    "document-ai-sdk",
  );
  assert.equal((await lstat(dependencyPath)).isSymbolicLink(), false);
  assert.equal((await lstat(await realpath(dependencyPath))).isDirectory(), true);

  const result = spawnSync(
    process.execPath,
    [
      "-e",
      `const { _runCliForTesting } = require(${JSON.stringify(path.join(checkout, "cli", "dist", "run.js"))});
       const io = { stdout: { write() {} }, stderr: { write() {} } };
       const client = { getJob: async (jobId) => ({ jobId, status: "Succeeded" }) };
       _runCliForTesting(["jobs", "get", "built-job"], {
         env: { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET" }, io,
         _createClientForTesting: () => client,
       }).then((code) => { process.exitCode = code; });`,
    ],
    { cwd: checkout, encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, "");
});

test("installed CLI delegates every public command to CognerisClient", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "cogneris-cli-input-"));
  temporaryDirectories.push(directory);
  const filePath = path.join(directory, "sample.pdf");
  await writeFile(filePath, "test-document-bytes");
  const calls = [];
  const clientFactory = (options) => {
    calls.push(["constructor", options]);
    return {
      cancelJob: async (jobId) => {
        calls.push(["cancelJob", jobId]);
        return { jobId, status: "Cancelled" };
      },
      extract: async (file, extractOptions) => {
        calls.push(["extract", await file.text(), extractOptions]);
        return { data: { accepted: true }, hasErrors: false };
      },
      getJob: async (jobId) => {
        calls.push(["getJob", jobId]);
        return { jobId, status: "Processing" };
      },
      submitJob: async (operation, inputReference) => {
        calls.push(["submitJob", operation, inputReference]);
        return { jobId: "job-submit", status: "Queued" };
      },
      waitForJob: async (jobId) => {
        calls.push(["waitForJob", jobId]);
        return { jobId, status: "Succeeded" };
      },
    };
  };

  const commands = [
    [
      ["--region", "eu", "extract", filePath],
      ["extract", "test-document-bytes", { fileName: "sample.pdf" }],
    ],
    [
      ["jobs", "submit", "--operation", "Facematch", "--input-reference", "artifact://bucket/input.pdf"],
      ["submitJob", "Facematch", "artifact://bucket/input.pdf"],
    ],
    [["jobs", "get", "job-get"], ["getJob", "job-get"]],
    [["jobs", "wait", "job-wait"], ["waitForJob", "job-wait"]],
    [["jobs", "cancel", "job-cancel"], ["cancelJob", "job-cancel"]],
  ];

  for (const [argumentsList, expectedCall] of commands) {
    calls.length = 0;
    const result = await invoke(argumentsList, { clientFactory });
    assert.equal(result.code, 0, result.stderr);
    assert.equal(result.stderr, "");
    assert.doesNotThrow(() => JSON.parse(result.stdout));
    assert.deepEqual(calls.at(-1), expectedCall);
    assert.equal(calls[0][0], "constructor");
  }
  assert.deepEqual(calls[0][1], { apiKey: "xtkt_live_TEST_ONLY_NOT_A_SECRET", region: "us" });
});

test("region precedence is option, environment, then us and rejects all other values", async () => {
  const constructed = [];
  const clientFactory = (options) => {
    constructed.push(options);
    return { getJob: async (jobId) => ({ jobId, status: "Succeeded" }) };
  };

  assert.equal((await invoke(["jobs", "get", "one"], {
    env: { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET", COGNERIS_REGION: "eu" },
    clientFactory,
  })).code, 0);
  assert.equal((await invoke(["--region", "us", "jobs", "get", "two"], {
    env: { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET", COGNERIS_REGION: "eu" },
    clientFactory,
  })).code, 0);
  assert.equal((await invoke(["jobs", "get", "three"], {
    env: { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET" },
    clientFactory,
  })).code, 0);
  assert.deepEqual(constructed.map(({ region }) => region), ["eu", "us", "us"]);

  for (const [argumentsList, env] of [
    [["--region", "apac", "jobs", "get", "job"], { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET" }],
    [["jobs", "get", "job"], { COGNERIS_API_KEY: "xtkt_live_TEST_ONLY_NOT_A_SECRET", COGNERIS_REGION: "constructor" }],
  ]) {
    const result = await invoke(argumentsList, { env, clientFactory });
    assert.equal(result.code, 2);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /region.*us.*eu/i);
    assert.doesNotMatch(result.stderr, /apac|constructor/);
  }
});

test("credential validation rejects missing and unsafe values without echoing them", async () => {
  const unsafeValues = [undefined, "", "   ", "key with space", "key\nline", "key\tvalue", "key\u007fvalue", "clé"];
  for (const unsafeValue of unsafeValues) {
    const env = unsafeValue === undefined ? {} : { COGNERIS_API_KEY: unsafeValue };
    const result = await invoke(["jobs", "get", "job"], { env });
    assert.equal(result.code, 2);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /COGNERIS_API_KEY/);
    if (unsafeValue) assert.equal(result.stderr.includes(unsafeValue), false);
  }
});

test("credentials require the public prefix and suffix before client creation or transport", async (context) => {
  let constructions = 0;
  let requests = 0;
  const server = createServer((_request, response) => {
    requests += 1;
    json(response, 200, { jobId: "unexpected", status: "Succeeded" });
  });
  const baseUrl = await listen(server);
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const { sdk } = await installedPackages();
  const clientFactory = (options) => {
    constructions += 1;
    return new sdk.CognerisClient({ ...options, _baseUrlForTesting: baseUrl });
  };
  for (const value of ["garbage", "xtkt_test_SENTINEL", "xtkt_live_", "XTKT_live_SENTINEL",
    "xtkt_live_" + "x".repeat(4096), "xtkt_live_BAD VALUE", "xtkt_live_BAD\nVALUE",
    "xtkt_live_BAD\tVALUE", "xtkt_live_BAD\u007fVALUE", "xtkt_live_clé"]) {
    const result = await invoke(["jobs", "get", "unused-job"], {
      env: { COGNERIS_API_KEY: value }, clientFactory,
    });
    assert.equal(result.code, 2);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /COGNERIS_API_KEY/);
    assert.equal(result.stderr.includes(value), false);
  }
  assert.equal(constructions, 0);
  assert.equal(requests, 0);

  // No stronger suffix alphabet is specified by the public contract.
  for (const value of ["xtkt_live_x", "xtkt_live_TEST:!~+/@=._-sentinel", "xtkt_live_" + "x".repeat(4086)]) {
    const result = await invoke(["jobs", "get", "valid-job"], {
      env: { COGNERIS_API_KEY: value }, clientFactory,
    });
    assert.equal(result.code, 0, result.stderr);
  }
  assert.equal(constructions, 3);
  assert.equal(requests, 3);
});

test("usage failures stay on stderr and do not expose credential arguments or internal commands", async () => {
  const credential = "xtkt_live_TEST_ONLY_ARGUMENT_SENTINEL";
  for (const argumentsList of [
    ["--api-key", credential, "jobs", "get", "job"],
    ["--base-url", "http://127.0.0.1:1", "jobs", "get", "job"],
    ["jobs", "submit", "--operation", "Schema", "--input-reference", "ref"],
    ["schemas", "list"],
    ["jobs", "get"],
  ]) {
    const result = await invoke(argumentsList);
    assert.equal(result.code, 2);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /Usage:/);
    assert.equal(result.stderr.includes(credential), false);
    assert.doesNotMatch(result.stderr, /schema|evidence|cost|destination|webhook|admin/i);
  }
});

test("strict grammar rejects option-like values, duplicates, sentinels, and extras without SDK calls", async () => {
  let clientConstructions = 0;
  const clientFactory = () => {
    clientConstructions += 1;
    return {
      extract: async () => ({ hasErrors: false }),
      getJob: async () => ({ jobId: "unexpected", status: "Succeeded" }),
      submitJob: async () => ({ jobId: "unexpected", status: "Queued" }),
    };
  };
  const invalidInvocations = [
    ["jobs", "get", "--help"],
    ["jobs", "get", "--"],
    ["jobs", "get", "job-id", "extra"],
    ["jobs", "get", "--unknown"],
    ["extract", "--help"],
    ["extract", "--", "input.pdf"],
    ["--region", "--help", "jobs", "get", "job-id"],
    ["--region", "us", "--region", "eu", "jobs", "get", "job-id"],
    ["--region=us", "jobs", "get", "job-id"],
    ["jobs", "submit", "--operation"],
    ["jobs", "submit", "--input-reference"],
    ["jobs", "submit", "--operation", "Extraction", "--input-reference"],
    ["jobs", "submit", "--operation", "Extraction", "--input-reference", "--base-url"],
    ["jobs", "submit", "--operation", "--input-reference", "reference"],
    ["jobs", "submit", "--operation", "Extraction", "--operation", "Split", "--input-reference", "reference"],
    ["jobs", "submit", "--operation", "Extraction", "--input-reference", "one", "--input-reference", "two"],
    ["jobs", "submit", "--operation", "Extraction", "--input-reference", "reference", "extra"],
    ["jobs", "submit", "--", "--operation", "Extraction", "--input-reference", "reference"],
  ];

  for (const argumentsList of invalidInvocations) {
    const result = await invoke(argumentsList, { clientFactory });
    assert.equal(result.code, 2, JSON.stringify(argumentsList));
    assert.equal(result.stdout, "");
    assert.match(result.stderr, /Usage:/);
  }
  assert.equal(clientConstructions, 0);
});

test("installed CLI uses the SDK loopback seam for multipart and job requests", async (context) => {
  const requests = [];
  let waitCount = 0;
  const server = createServer(async (request, response) => {
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
      json(response, 200, { data: { accepted: true }, meta: { status: 200 }, hasErrors: false });
    } else if (request.method === "POST" && request.url === "/api/v1/document-jobs") {
      json(response, 202, serviceEnvelope(202, {
        jobId: "submitted-job",
        status: "Queued",
        statusUrl: "/api/v1/document-jobs/submitted-job",
        retryAfterSeconds: 0,
      }), { "Retry-After": "0" });
    } else if (request.method === "POST" && request.url === "/api/v1/document-jobs/cancel-job/cancel") {
      json(response, 202, serviceEnvelope(202, { jobId: "cancel-job", cancellationRequested: true }));
    } else if (request.method === "GET" && request.url === "/api/v1/document-jobs/wait-job") {
      waitCount += 1;
      json(response, 200, serviceEnvelope(200, {
        jobId: "wait-job",
        operation: "Extraction",
        status: waitCount === 1 ? "Processing" : "Succeeded",
      }), { "Retry-After": "0" });
    } else if (request.method === "GET" && request.url === "/api/v1/document-jobs/get-job") {
      json(response, 200, serviceEnvelope(200, { jobId: "get-job", operation: "Extraction", status: "Processing" }));
    } else {
      json(response, 404, { code: "not-found" });
    }
  });
  const baseUrl = await listen(server);
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const { sdk } = await installedPackages();
  const clientFactory = (options) => new sdk.CognerisClient({
    ...options,
    _baseUrlForTesting: baseUrl,
  });
  const directory = await mkdtemp(path.join(os.tmpdir(), "cogneris-cli-loopback-"));
  temporaryDirectories.push(directory);
  const filePath = path.join(directory, "input.pdf");
  await writeFile(filePath, "document-sentinel");

  for (const argumentsList of [
    ["extract", filePath],
    ["jobs", "submit", "--operation", "Extraction", "--input-reference", "artifact://bucket/input.pdf"],
    ["jobs", "get", "get-job"],
    ["jobs", "wait", "wait-job"],
    ["jobs", "cancel", "cancel-job"],
  ]) {
    const result = await invoke(argumentsList, { clientFactory });
    assert.equal(result.code, 0, result.stderr);
    assert.equal(result.stderr, "");
    assert.doesNotThrow(() => JSON.parse(result.stdout));
  }

  assert.equal(requests.every(({ authorization }) => authorization === "Bearer xtkt_live_TEST_ONLY_NOT_A_SECRET"), true);
  const extraction = requests.find(({ path: requestPath }) => requestPath === "/Document/extraction");
  assert.match(extraction.contentType, /^multipart\/form-data; boundary=/);
  assert.match(extraction.body.toString(), /document-sentinel/);
  assert.match(extraction.body.toString(), /input\.pdf/);
  const submission = requests.find(({ path: requestPath }) => requestPath === "/api/v1/document-jobs");
  assert.deepEqual(JSON.parse(submission.body.toString()), {
    inputReference: "artifact://bucket/input.pdf",
    operation: "Extraction",
  });
  assert.equal(waitCount, 2);
});

test("file and SDK failures use safe exit codes and never leak response or credentials", async (context) => {
  const apiKey = "xtkt_live_TEST_ONLY_REFLECTED_SENTINEL";
  const document = "document-reflected-sentinel";
  const server = createServer(async (request, response) => {
    for await (const _chunk of request) { /* consume request */ }
    json(response, 500, { code: apiKey, title: document, detail: request.headers.authorization });
  });
  const baseUrl = await listen(server);
  context.after(() => new Promise((resolve) => server.close(resolve)));
  const { sdk } = await installedPackages();
  const clientFactory = (options) => new sdk.CognerisClient({
    ...options,
    _baseUrlForTesting: baseUrl,
  });

  const missing = await invoke(["extract", path.join(os.tmpdir(), "missing-cogneris-input")]);
  assert.equal(missing.code, 2);
  assert.equal(missing.stdout, "");
  assert.match(missing.stderr, /unable to read input file/i);

  const failed = await invoke(["jobs", "get", "failed-job"], {
    env: { COGNERIS_API_KEY: apiKey },
    clientFactory,
  });
  assert.equal(failed.code, 1);
  assert.equal(failed.stdout, "");
  assert.match(failed.stderr, /HTTP 500/);
  assert.equal(failed.stderr.includes(apiKey), false);
  assert.equal(failed.stderr.includes(document), false);
  assert.doesNotMatch(failed.stderr, /authorization|at .*\(|Error:/i);
});

test("packaged cogneris binary enforces configuration without stdout or stack traces", async () => {
  const { bin, consumerDirectory } = await installedPackages();
  const result = spawnSync(bin, ["jobs", "get", "job-id"], {
    cwd: consumerDirectory,
    encoding: "utf8",
    env: Object.fromEntries(
      Object.entries(process.env).filter(([key]) => key !== "COGNERIS_API_KEY"),
    ),
  });
  assert.equal(result.status, 2);
  assert.equal(result.stdout, "");
  assert.match(result.stderr, /COGNERIS_API_KEY/);
  assert.doesNotMatch(result.stderr, /at .*\(|Error:/);
});

test("installed binary handles success, API and application failures, and broken stdout without reflection", async (context) => {
  const apiKey = "xtkt_live_TEST_ONLY_BINARY_SENTINEL";
  const serverDetail = "binary-server-detail-sentinel";
  const resultBody = "binary-result-body-sentinel";
  const document = "binary-private-document-sentinel";
  const fileName = "binary-private-filename-sentinel.pdf";
  let releaseBrokenPipeResponse;
  const brokenPipeResponseReleased = new Promise((resolve) => {
    releaseBrokenPipeResponse = resolve;
  });
  let observeBrokenPipeRequest;
  const brokenPipeRequestObserved = new Promise((resolve) => {
    observeBrokenPipeRequest = resolve;
  });
  const server = createServer(async (request, response) => {
    for await (const _chunk of request) { /* consume request */ }
    if (request.url === "/api/v1/document-jobs/success-job") {
      json(response, 200, serviceEnvelope(200, { jobId: "success-job", operation: "Extraction", status: "Succeeded" }));
    } else if (request.url === "/api/v1/document-jobs/failure-job") {
      json(response, 500, { code: apiKey, title: serverDetail });
    } else if (request.url === "/Document/extraction") {
      json(response, 200, {
        hasErrors: true,
        title: serverDetail,
        fields: { fileName, authorization: apiKey },
        data: { raw: resultBody, contents: document },
      });
    } else if (request.url === "/api/v1/document-jobs/broken-pipe-job") {
      observeBrokenPipeRequest();
      await brokenPipeResponseReleased;
      json(response, 200, serviceEnvelope(200, {
        jobId: "broken-pipe-job",
        operation: "Extraction",
        status: "Succeeded",
        outputReference: resultBody.repeat(200_000),
      }));
    } else {
      json(response, 404, { code: "not-found" });
    }
  });
  const baseUrl = await listen(server);
  context.after(() => new Promise((resolve) => server.close(resolve)));

  const { bin, consumerDirectory } = await installedPackages();
  const preloadPath = path.join(consumerDirectory, "cli-loopback-preload.cjs");
  await writeFile(
    preloadPath,
    `const Module = require("node:module");
const originalLoad = Module._load;
const sdk = originalLoad.call(Module, "@cogneris-ai/document-ai-sdk", module, false);
class LoopbackCognerisClient extends sdk.CognerisClient {
  constructor(options) {
    super({ ...options, _baseUrlForTesting: process.env.TEST_COGNERIS_BASE_URL });
  }
}
const replacement = { ...sdk, CognerisClient: LoopbackCognerisClient };
Module._load = function(request, parent, isMain) {
  return request === "@cogneris-ai/document-ai-sdk"
    ? replacement
    : originalLoad.call(this, request, parent, isMain);
};
`,
  );
  const childEnvironment = {
    ...process.env,
    COGNERIS_API_KEY: apiKey,
    NODE_OPTIONS: `--require=${preloadPath}`,
    TEST_COGNERIS_BASE_URL: baseUrl,
  };
  const runBinary = (argumentsList) => new Promise((resolve, reject) => {
    const child = spawn(bin, argumentsList, {
      cwd: consumerDirectory,
      env: childEnvironment,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.once("error", reject);
    child.once("close", (status) => resolve({ status, stderr, stdout }));
  });

  const succeeded = await runBinary(["jobs", "get", "success-job"]);
  assert.equal(succeeded.status, 0, succeeded.stderr);
  assert.equal(succeeded.stderr, "");
  assert.deepEqual(JSON.parse(succeeded.stdout), {
    jobId: "success-job",
    operation: "Extraction",
    status: "Succeeded",
  });

  const failed = await runBinary(["jobs", "get", "failure-job"]);
  assert.equal(failed.status, 1);
  assert.equal(failed.stdout, "");
  assert.match(failed.stderr, /HTTP 500/);
  assert.equal(failed.stderr.includes(apiKey), false);
  assert.equal(failed.stderr.includes(serverDetail), false);
  assert.doesNotMatch(failed.stderr, /at .*\(|Error:/);

  const filePath = path.join(consumerDirectory, fileName);
  await writeFile(filePath, document);
  const applicationFailure = await runBinary(["extract", filePath]);
  assert.equal(applicationFailure.status, 1);
  assert.equal(applicationFailure.stdout, "");
  assert.equal(applicationFailure.stderr, "Cogneris extraction failed.\n");
  for (const sentinel of [apiKey, serverDetail, resultBody, document, fileName]) {
    assert.equal((applicationFailure.stdout + applicationFailure.stderr).includes(sentinel), false);
  }

  const child = spawn(bin, ["jobs", "get", "broken-pipe-job"], {
    cwd: consumerDirectory,
    env: childEnvironment,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let brokenPipeStderr = "";
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk) => { brokenPipeStderr += chunk; });
  await brokenPipeRequestObserved;
  child.stdout.destroy();
  releaseBrokenPipeResponse();
  const brokenPipeStatus = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("close", resolve);
  });
  assert.equal(brokenPipeStatus, 1);
  assert.match(brokenPipeStderr, /output failed/i);
  assert.equal(brokenPipeStderr.includes(apiKey), false);
  assert.equal(brokenPipeStderr.includes(serverDetail), false);
  assert.equal(brokenPipeStderr.includes(resultBody), false);
  assert.doesNotMatch(brokenPipeStderr, /at .*\(|Error:/);
});
