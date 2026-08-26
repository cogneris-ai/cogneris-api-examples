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
    { stdio: "inherit" },
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

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(collection, null, 2)}\n`);
} finally {
  await fs.rm(temporaryDirectory, { recursive: true, force: true });
}
