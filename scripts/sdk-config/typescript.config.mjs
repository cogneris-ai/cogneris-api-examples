import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
);

export default {
  input:
    process.env.COGNERIS_SDK_OPENAPI_INPUT ??
    path.join(root, "openapi", "cogneris-openapi.yaml"),
  output: {
    clean: true,
    path:
      process.env.COGNERIS_TYPESCRIPT_SDK_OUTPUT ??
      path.join(root, "sdks", "typescript", "src"),
  },
  plugins: [
    "@hey-api/client-fetch",
    "@hey-api/typescript",
    "@hey-api/sdk",
  ],
  logs: {
    file: false,
    level: "silent",
  },
};
