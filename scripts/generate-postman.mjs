import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = path.join(root, "openapi", "cogneris-openapi.yaml");
const outputPath = path.join(
  root,
  "postman",
  "Cogneris-API.postman_collection.json",
);
const deterministicRandomPath = path.join(
  root,
  "scripts",
  "deterministic-random.cjs",
);

function removeUnstableIds(value) {
  if (Array.isArray(value)) {
    return value.map(removeUnstableIds);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== "id" && key !== "_postman_id")
        .map(([key, child]) => [key, removeUnstableIds(child)]),
    );
  }
  return value;
}

// openapi-to-postmanv2 prefixes the description of a required body property
// with "(Required)". That marker is the only required/optional signal left in
// the converted collection, and the converter version is pinned exactly above.
function isRequiredField(field) {
  const description = field.description;
  const content =
    typeof description === "string" ? description : (description?.content ?? "");
  return content.startsWith("(Required)");
}

// Postman sends every selected form field, and so does scripts/smoke-live.mjs.
// The converter selects optional properties and fills them with schema
// placeholders, so an untouched collection posts `ComplementaryPrompt=<string>`
// on the very first extraction a reader runs — and that value is appended
// verbatim to the model prompt. Optional fields therefore ship deselected.
function deselectOptionalFormFields(items) {
  let required = 0;
  let optional = 0;

  for (const item of items) {
    const formdata = item.request?.body?.formdata;
    for (const field of formdata ?? []) {
      if (isRequiredField(field)) {
        delete field.disabled;
        required += 1;
      } else {
        field.disabled = true;
        optional += 1;
      }
    }
    const nested = deselectOptionalFormFields(item.item ?? []);
    required += nested.required;
    optional += nested.optional;
  }

  return { required, optional };
}

// The converter maps a scalar `format: binary` property to Postman's file
// type, but an array of binary falls through to a text field holding the joined
// `<binary>` placeholder. /Document/classifier and /Document/facematch both
// bind IFormFileCollection, so those fields are required and ship selected:
// Postman would post the literal placeholder where the documents belong, and a
// text row offers no file picker for a reader to correct it.
function convertBinaryArrayFieldsToFiles(items) {
  let converted = 0;

  for (const item of items) {
    for (const field of item.request?.body?.formdata ?? []) {
      if (field.type === "file") continue;
      if (!String(field.value ?? "").includes("<binary>")) continue;
      delete field.value;
      field.type = "file";
      // v2.1 allows src to be a string, null or an array; an array is how the
      // format carries a multi-file field. Empty means "reader picks the files".
      field.src = [];
      converted += 1;
    }
    converted += convertBinaryArrayFieldsToFiles(item.item ?? []);
  }

  return converted;
}

const temporaryDirectory = await fs.mkdtemp(
  path.join(os.tmpdir(), "cogneris-postman-"),
);
const generatedPath = path.join(temporaryDirectory, "collection.json");

try {
  const conversion = spawnSync(
    "npx",
    [
      "--yes",
      "openapi-to-postmanv2@6.3.3",
      "-s",
      sourcePath,
      "-o",
      generatedPath,
      "-p",
    ],
    {
      env: {
        ...process.env,
        NODE_OPTIONS: `--require=${deterministicRandomPath}`,
      },
      stdio: "inherit",
    },
  );
  if (conversion.status !== 0) {
    throw new Error(`OpenAPI conversion exited with ${conversion.status}`);
  }

  const generated = JSON.parse(await fs.readFile(generatedPath, "utf8"));
  const collection = removeUnstableIds(generated);
  collection.variable = collection.variable.filter(
    (variable) => variable.key !== "bearerToken",
  );
  collection.variable.push({ key: "bearerToken", value: "", type: "secret" });

  const { required, optional } = deselectOptionalFormFields(collection.item);
  // Positive control. If the converter ever stops emitting the "(Required)"
  // marker, every field reads as optional and the document upload itself would
  // ship deselected — a collection that silently posts nothing. Fail instead.
  if (required === 0 || optional === 0) {
    throw new Error(
      `expected both required and optional form fields, got ${required} required and ${optional} optional — the converter's "(Required)" marker changed`,
    );
  }

  const files = convertBinaryArrayFieldsToFiles(collection.item);
  // Positive control, same reasoning as above. This contract declares two
  // arrays of binary. If the converter ever stops emitting the `<binary>`
  // placeholder, none is found, and the collection would publish those fields
  // as whatever the converter chose instead — silently, since nothing else
  // reads them. Fail instead.
  if (files === 0) {
    throw new Error(
      'no array-of-binary form field found — the converter\'s "<binary>" placeholder changed',
    );
  }

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(collection, null, 2)}\n`);
} finally {
  await fs.rm(temporaryDirectory, { recursive: true, force: true });
}
