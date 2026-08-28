import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const collectionPath = path.join(
  root,
  "postman",
  "Cogneris-API.postman_collection.json",
);

function argument(name) {
  const index = process.argv.indexOf(name);
  return index === -1 ? undefined : process.argv[index + 1];
}

const key = process.env.COGNERIS_KEY ?? "";
if (!key.startsWith("xtkt_live_")) {
  console.error("COGNERIS_KEY must start with xtkt_live_");
  process.exit(2);
}

const file = argument("--file");
if (!file) {
  console.error("--file must point to a document to extract");
  process.exit(2);
}

const absoluteFile = path.resolve(file);
const stat = await fs.stat(absoluteFile).catch(() => undefined);
if (!stat?.isFile()) {
  console.error(`document does not exist: ${absoluteFile}`);
  process.exit(2);
}

const collection = JSON.parse(await fs.readFile(collectionPath, "utf8"));
let extraction;
function findExtraction(items) {
  for (const item of items) {
    if (item.request?.url?.path?.join("/") === "Document/extraction") {
      extraction = item.request;
      return;
    }
    findExtraction(item.item ?? []);
  }
}
findExtraction(collection.item);

const fileField = extraction?.body?.formdata?.find((field) => field.key === "file");
if (!fileField) {
  console.error("collection has no Document/extraction file field");
  process.exit(2);
}
const form = new FormData();
for (const field of extraction.body.formdata) {
  if (field.type === "file") {
    form.append(field.key, new Blob([await fs.readFile(absoluteFile)]), path.basename(absoluteFile));
  } else if (!field.disabled) {
    form.append(field.key, field.value ?? "");
  }
}

const collectionBaseUrl = collection.variable.find(
  (variable) => variable.key === "baseUrl",
)?.value;
const baseUrl = argument("--base-url") ?? collectionBaseUrl;
const requestUrl = `${baseUrl.replace(/\/$/, "")}/${extraction.url.path.join("/")}`;
const response = await fetch(requestUrl, {
  method: extraction.method,
  headers: { Authorization: `Bearer ${key}` },
  body: form,
});

if (!response.ok) {
  console.error(`Extraction request failed with HTTP ${response.status}`);
  process.exit(1);
}

console.log(`Extraction request completed with HTTP ${response.status}`);
