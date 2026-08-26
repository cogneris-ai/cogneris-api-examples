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

## Regenerate from OpenAPI

The source contract is [`openapi/cogneris-openapi.yaml`](openapi/cogneris-openapi.yaml),
copied from `cogneris-site/src/openapi.yaml`. To regenerate it:

```bash
npm ci
npm run generate
npm test
```

The generator removes unstable converter IDs and adds an empty, secret-typed
`bearerToken` collection variable. It does not add or persist credentials.
