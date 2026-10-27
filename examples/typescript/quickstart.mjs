import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { CognerisClient, CognerisError } from "@cogneris-ai/document-ai-sdk";

const USAGE = `Usage:
  node quickstart.mjs extract <file> [--hide-values]
  node quickstart.mjs async-file <operation> <file>
  node quickstart.mjs async <operation> <input-reference>`;
const OPERATIONS = new Set(["Extraction", "Classification", "ZeroShot", "Crop", "Split", "Facematch"]);
const HIDE_VALUES = "--hide-values";
// Send every upload with its MIME type: a Blob without `type` goes out as a part the API
// cannot always admit.
const MEDIA_TYPES = new Map([
  [".pdf", "application/pdf"],
  [".png", "image/png"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".tif", "image/tiff"],
  [".tiff", "image/tiff"],
  [".bmp", "image/bmp"],
  [".doc", "application/msword"],
  [".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
]);

class UsageError extends Error {}

function required(value) {
  return typeof value === "string" && value.trim().length > 0 && !value.startsWith("-");
}

function configuration(environment) {
  const apiKey = environment.COGNERIS_API_KEY;
  if (!required(apiKey)) {
    throw new UsageError("Set COGNERIS_API_KEY before running this example.");
  }
  const region = environment.COGNERIS_REGION ?? "eu";
  if (region !== "us" && region !== "eu") {
    throw new UsageError("COGNERIS_REGION must be either us or eu.");
  }
  return { apiKey, region };
}

function command(argumentsList) {
  if (argumentsList[0] === "extract" && (argumentsList.length === 2 || argumentsList.length === 3) &&
      required(argumentsList[1]) && (argumentsList.length === 2 || argumentsList[2] === HIDE_VALUES)) {
    return { kind: "extract", filePath: argumentsList[1], hideValues: argumentsList.length === 3 };
  }
  if (
    argumentsList[0] === "async" &&
    argumentsList.length === 3 &&
    OPERATIONS.has(argumentsList[1]) &&
    required(argumentsList[2])
  ) {
    return { kind: "async", operation: argumentsList[1], inputReference: argumentsList[2] };
  }
  if (argumentsList[0] === "async-file" && argumentsList.length === 3 &&
      OPERATIONS.has(argumentsList[1]) && required(argumentsList[2])) {
    return { kind: "async-file", operation: argumentsList[1], filePath: argumentsList[2] };
  }
  throw new UsageError("Choose a supported example command.");
}

function writeJson(output, value) {
  output.write(`${JSON.stringify(value)}\n`);
}

function mediaType(filePath) {
  const type = MEDIA_TYPES.get(path.extname(filePath).toLowerCase());
  if (!type) {
    throw new UsageError(
      "Unsupported file type. Use PDF, PNG, JPEG, TIFF, BMP, DOC or DOCX, " +
      "and send the file with its MIME type (for example application/pdf).",
    );
  }
  return type;
}

// The fields extraction returned, keyed by your template's field names. Shows fields and values
// (partners' decision, WOR-207): each entry carries the value, its confidence and, when located,
// page and bbox. Values are document content, so --hide-values prints only the field names.
function extractedFields(data, hideValues) {
  const metadata = data?.metadata;
  const fields = metadata && typeof metadata === "object" && !Array.isArray(metadata) ? metadata : {};
  return hideValues ? Object.keys(fields).sort() : fields;
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
      const result = await client.extract(new Blob([new Uint8Array(contents)], { type: mediaType(selected.filePath) }), {
        fileName: path.basename(selected.filePath),
      });
      if (result.hasErrors === true) {
        throw new CognerisError("Cogneris extraction reported an application error.");
      }
      writeJson(io.stdout, {
        operation: "extraction",
        hasErrors: result.hasErrors === true,
        httpStatusCode: typeof result.meta?.httpStatusCode === "number"
          ? result.meta.httpStatusCode
          : null,
        templateId: typeof result.data?.templateId === "string" ? result.data.templateId : null,
        fields: extractedFields(result.data, selected.hideValues),
      });
      return 0;
    }

    let inputReference = selected.inputReference;
    if (selected.kind === "async-file") {
      let contents;
      try { contents = await readFile(selected.filePath); } catch { throw new UsageError("Unable to read the input file."); }
      const artifact = await client.uploadArtifact(new Blob([new Uint8Array(contents)], { type: mediaType(selected.filePath) }), {
        fileName: path.basename(selected.filePath),
      });
      inputReference = artifact.reference;
    }
    const submission = await client.submitJob(selected.operation, inputReference);
    if (typeof submission.jobId !== "string" || submission.jobId.length === 0) {
      throw new CognerisError("Cogneris API response did not include a job ID.");
    }
    const job = await client.waitForJob(submission.jobId);
    if (selected.kind === "async-file" && typeof job.outputReference === "string") {
      await client.downloadArtifact(job.outputReference);
    }
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
