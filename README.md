# Cogneris API examples

Runnable examples for the [Cogneris Document AI API](https://cogneris.ai/docs.html).
The Postman collection is generated from the published OpenAPI contract, with no
API keys or customer data committed to this repository.

## Import the Postman collection

1. Download [`Cogneris-API.postman_collection.json`](postman/Cogneris-API.postman_collection.json).
2. In Postman, select **Import**, then choose the downloaded file.
3. Open the collection variables and set `bearerToken` to a valid key beginning
   with `xtkt_live_`. The committed value is intentionally empty.
4. Open **Documents → extraction → Extract structured fields from a document**,
   choose a local file in the `file` form-data field, and send the request.

The collection defaults to `https://api-us.cogneris.ai`. Change `baseUrl` to
`https://api-eu.cogneris.ai` when your tenant is hosted in Europe.

## Run the live extraction smoke test

Use the same collection request from the command line with a valid live key and
a non-sensitive local document. The key is read from the environment and is not
written to the collection or printed in the output.

```bash
COGNERIS_KEY=xtkt_live_... npm run smoke:live -- --file /path/to/document.pdf
```

For an EU-hosted tenant, add `--base-url https://api-eu.cogneris.ai`.

## Regenerate from OpenAPI

The source contract is [`openapi/cogneris-openapi.yaml`](openapi/cogneris-openapi.yaml),
copied from `cogneris-site/src/openapi.yaml`. To regenerate it:

```bash
npm ci
npm run generate
npm test
```

The generator removes unstable converter IDs and adds an empty, secret-typed
`bearerToken` collection variable. Its converter process uses a fixed random
seed so the same OpenAPI input produces the same committed collection. It does
not add or persist credentials.
