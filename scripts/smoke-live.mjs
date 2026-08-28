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
const documentBytes = await fs.readFile(absoluteFile).catch(() => undefined);
if (!documentBytes) {
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
    form.append(field.key, new Blob([documentBytes]), path.basename(absoluteFile));
  } else if (!field.disabled) {
    form.append(field.key, field.value ?? "");
  }
}

const baseUrl = new URL(argument("--base-url") ?? "https://api-us.cogneris.ai");
const allowedHosts = new Set([
  "api-us.cogneris.ai",
  "api-eu.cogneris.ai",
  "127.0.0.1",
  "localhost",
]);
if (!allowedHosts.has(baseUrl.hostname)) {
  console.error(`unsupported API host: ${baseUrl.hostname}`);
  process.exit(2);
}
if (baseUrl.protocol !== "https:" && !["127.0.0.1", "localhost"].includes(baseUrl.hostname)) {
  console.error("Cogneris API hosts require HTTPS");
  process.exit(2);
}
const requestUrl = new URL("/Document/extraction", baseUrl);
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
