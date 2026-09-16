import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { CognerisClient, CognerisError } from "@cogneris/document-ai-sdk";

const USAGE = `Usage:
  node quickstart.mjs extract <file>
  node quickstart.mjs async <operation> <input-reference>`;
const OPERATIONS = new Set(["Extraction", "Classification", "ZeroShot", "Crop", "Split"]);

class UsageError extends Error {}

function required(value) {
  return typeof value === "string" && value.trim().length > 0 && !value.startsWith("-");
}

function configuration(environment) {
  const apiKey = environment.COGNERIS_API_KEY;
  if (!required(apiKey)) {
    throw new UsageError("Set COGNERIS_API_KEY before running this example.");
  }
  const region = environment.COGNERIS_REGION ?? "us";
  if (region !== "us" && region !== "eu") {
    throw new UsageError("COGNERIS_REGION must be either us or eu.");
  }
  return { apiKey, region };
}

function command(argumentsList) {
  if (argumentsList[0] === "extract" && argumentsList.length === 2 && required(argumentsList[1])) {
    return { kind: "extract", filePath: argumentsList[1] };
  }
  if (
    argumentsList[0] === "async" &&
    argumentsList.length === 3 &&
    OPERATIONS.has(argumentsList[1]) &&
    required(argumentsList[2])
  ) {
    return { kind: "async", operation: argumentsList[1], inputReference: argumentsList[2] };
  }
  throw new UsageError("Choose a supported example command.");
}

function writeJson(output, value) {
  output.write(`${JSON.stringify(value)}\n`);
}

export async function _runExampleForTesting({
  argumentsList,
  environment,
  io,
  _createClientForTesting,
}) {
  try {
    const selected = command(argumentsList);
    const options = configuration(environment);
    const createClient = _createClientForTesting ?? ((clientOptions) => new CognerisClient(clientOptions));
    const client = createClient(options);

    if (selected.kind === "extract") {
      let contents;
      try {
        contents = await readFile(selected.filePath);
      } catch {
        throw new UsageError("Unable to read the input file.");
      }
      const result = await client.extract(new Blob([new Uint8Array(contents)]), {
        fileName: path.basename(selected.filePath),
      });
      writeJson(io.stdout, {
        operation: "extraction",
        hasErrors: result.hasErrors === true,
        httpStatusCode: typeof result.meta?.httpStatusCode === "number"
          ? result.meta.httpStatusCode
          : null,
      });
      return 0;
    }

    const submission = await client.submitJob(selected.operation, selected.inputReference);
    if (typeof submission.jobId !== "string" || submission.jobId.length === 0) {
      throw new CognerisError("Cogneris API response did not include a job ID.");
    }
    const job = await client.waitForJob(submission.jobId);
    writeJson(io.stdout, {
      operation: selected.operation,
      jobId: submission.jobId,
      status: job.status ?? null,
    });
    return 0;
  } catch (error) {
    if (error instanceof UsageError) {
      io.stderr.write(`${error.message}\n${USAGE}\n`);
      return 2;
    }
    if (error instanceof CognerisError) {
      io.stderr.write(`${error.message}\n`);
      return 1;
    }
    io.stderr.write("Cogneris example failed.\n");
    return 1;
  }
}

const isDirectInvocation = process.argv[1] &&
  path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));
if (isDirectInvocation) {
  process.exitCode = await _runExampleForTesting({
    argumentsList: process.argv.slice(2),
    environment: process.env,
    io: { stdout: process.stdout, stderr: process.stderr },
  });
}
