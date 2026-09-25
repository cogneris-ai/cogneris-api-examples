/*
 * Cogneris Document AI API
 * The Cogneris Document AI API turns unstructured documents — PDFs, images, scans — into structured JSON.  This document describes the endpoints that are actually deployed. It is written from the running service (`cogneris-api-be`) rather than from a design, so what is listed here is what you can call.  ## Authentication  Every endpoint takes an API key in the `Authorization` header as `Bearer <key>`. Keys begin with `xtkt_live_` (production) or `xtkt_test_` (sandbox); either prefix is accepted before the key is looked up for validation. The key selects the application environment. A recognized prefix alone does not authenticate a request: the key must also be valid and active. Keys are tenant-scoped and cannot cross tenant boundaries. Mint them in the dashboard under **Settings → API keys**.  ## Uploads  The synchronous document endpoints take `multipart/form-data`. There is no fetch-by-URL variant — the file travels in the request body.  - Accepted extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`,   `.bmp`, `.doc`, `.docx` - Maximum size: 10 MB per file, except `/Document/split`, which accepts 500 MB  The asynchronous job endpoints do not take a file. Upload it first to `POST /api/v1/artifacts` — same extensions, same 10 MB limit — and submit the `artifact://` reference it returns.  ## Artifact references  A reference names one stored object. `POST /api/v1/artifacts` returns one, a job submit consumes one as `inputReference`, and a finished job returns one as `outputReference`. `GET /api/v1/artifacts/content` turns either back into bytes.  - References are scoped to the tenant that created them. One belonging to another   tenant is refused as an invalid reference — the answer does not distinguish a   reference that exists elsewhere from one that never existed. - An uploaded reference is **reusable**: one upload can back several jobs. - It expires **7 days** after upload, matching how long a job is retained. The   exact instant is returned as `expiresAt`. Reading it afterwards answers `410`,   which is not `404` — the reference was real, it aged out, and re-requesting it   will never succeed. Upload again. - A job's `outputReference` lives as long as the job does.  ### Two shapes, one of them historical  Everything this API produces today is `artifact://<key>`. Jobs that completed before 2026-09-22 carry a bucket-qualified path instead — `<bucket>/<tenant>/document-jobs/<jobId>/result.json`, sometimes with an `@<version>` suffix. `GET /api/v1/artifacts/content` accepts both, so a reference stored from an older job still resolves for the rest of its life. Treat a reference as opaque: pass back exactly what you were given.  ## Templates  Extraction and classification are driven by the document types and templates configured for your tenant. The platform selects the template from the document itself, so the synchronous `/Document/_*` calls take no template or schema parameter. Use `GET /api/v1/templates` to list the finished templates available to your key before naming one explicitly with `templateId` on `POST /api/v1/document-jobs`. The list is cursor-paginated; pass its `nextCursor` as `cursor` to read the next page.  ## Scopes  Keys carry scopes. The Portal and webhook-endpoint routes check them and answer `403` when the required one is absent; the document endpoints accept any valid key for the tenant without consulting the list. `*` is a real scope meaning full access, and it is what a key receives when it is created without an explicit scope list.  ## Webhooks  A finished asynchronous job can announce itself, so you do not have to poll it. Register an HTTPS endpoint with `POST /api/v1/webhook-endpoints` and it receives a signed `POST` when a job you subscribed to succeeds, fails or is cancelled. The webhook **announces** the result and does not carry it: read the bytes with `GET /api/v1/artifacts/content?reference=<OutputReference>`.  Endpoints are managed with a **production** key holding `webhooks.manage` (or `*`). An endpoint receives your whole account's production events for the events it subscribes to, and events from sandbox jobs are never delivered, so a sandbox key is refused.  Each delivery carries three headers:  - `X-Xtrakt-Event` — the event name, such as `extract.processed`. - `X-Xtrakt-Delivery` — a fresh id per send. It is not a deduplication key. - `X-Xtrakt-Signature` — `t=<unix seconds>,v1=<hex>`, where `v1` is the   HMAC-SHA256 of `<t>.<raw body>` keyed with the endpoint's `whsec_` secret.   Recompute it over the raw bytes, compare in constant time, and reject a `t`   outside your tolerance.  For a job, the body is the job's terminal state. **Its property names are PascalCase**, unlike the rest of this API:  ```json {\"JobId\":\"7c9e6679-7425-40de-944b-e07fc1f90ae7\",\"Operation\":\"Extraction\",  \"Status\":\"succeeded\",\"OutputReference\":\"artifact://document-jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7/result.json\",  \"Stage\":null,\"ProcessedPages\":null,\"TotalPages\":null,\"FailureCode\":null,  \"AttemptCount\":1,\"CompletedAt\":\"2026-09-23T14:02:11.482Z\"} ```  `Status` is `succeeded`, `failed` or `cancelled`, and a cancelled job sends the `.failed` event. `OutputReference` is null unless the job succeeded, and always null for `Redaction`. The synchronous `/Document/_*` calls fire the same event names with their own response as the body; a delivery about a job is the one that has `JobId`. An endpoint with a `body` sends that fixed text **instead of** the payload.  Delivery semantics:  - **A job's outcome never depends on its webhook.** A job that succeeded stays   succeeded when the delivery fails; `GET /api/v1/document-jobs/{jobId}` is the   source of truth. - **One attempt per endpoint, no retry.** A timeout or a non-2xx answer is   recorded and not sent again. Answer `2xx` fast and do the work afterwards, and   reconcile periodically with `GET /api/v1/document-jobs`. - **Duplicates are rare but possible.** Deduplicate on `JobId` plus the event. - Every delivery attempt is metered as webhook usage, successful or not.  ## Rate limits  One shared policy covers every surface in this document, Portal included: **50 requests per API key per fixed 1-minute window**. It is a fixed window rather than a token bucket, so the allowance resets on the minute instead of refilling gradually. Requests over the limit receive `429`.  ## Response envelope  Successful responses from the **document, job and webhook-endpoint** routes share one wrapper: `data` for the payload, `meta` for the status and any messages, and `hasErrors` for a fast failure check. The webhook-endpoint routes send their **errors** as problem documents, described next.  The **Portal** endpoints do not use that wrapper. They return the payload directly, and their errors are RFC 9457 problem documents sent as `application/problem+json`, with a stable `code`, a `correlationId` that is also returned in the `x-correlation-id` header, and a `retryable` flag. Branch on `code`; treat `type` as an opaque identifier.  ## Errors  An error arrives in one of two shapes, and the `Content-Type` says which.  - `application/problem+json` — an RFC 9457 problem document, the same one the   Portal uses. Every route answers this way when the failure happens before your   request is processed: a missing or invalid key (`401`), the rate limit (`429`),   a request refused as malformed or unsafe (`400`), or an unexpected failure   (`500`). - `application/json` — the service envelope with `hasErrors: true` and the   reasons in `meta.errors`. The document, job and artifact routes answer this way   when processing itself fails. Each operation lists the statuses where it does.  Every operation lists `400`, `401`, `403`, `404`, `409`, `429` and `500`, because the API answers each of them in the same shape wherever it occurs. A status on an operation with nothing to miss or conflict with — a `409` on a read, say — is part of that uniform model and not something the operation returns in practice.
 *
 * The version of the OpenAPI document: 2026-09-24
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

package ai.cogneris.documentai.api;

import ai.cogneris.documentai.ApiClient;
import ai.cogneris.documentai.ApiException;
import ai.cogneris.documentai.ApiResponse;
import ai.cogneris.documentai.Configuration;
import ai.cogneris.documentai.Pair;

import ai.cogneris.documentai.model.ProblemDetails;
import java.util.UUID;
import ai.cogneris.documentai.model.WebhookEndpointCreateRequest;
import ai.cogneris.documentai.model.WebhookEndpointCreatedEnvelope;
import ai.cogneris.documentai.model.WebhookEndpointDeletionEnvelope;
import ai.cogneris.documentai.model.WebhookEndpointEnvelope;
import ai.cogneris.documentai.model.WebhookEndpointListEnvelope;
import ai.cogneris.documentai.model.WebhookEndpointUpdateRequest;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.apache.http.HttpEntity;
import org.apache.http.NameValuePair;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.client.entity.UrlEncodedFormEntity;

import java.io.InputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.net.http.HttpRequest;
import java.nio.channels.Channels;
import java.nio.channels.Pipe;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import java.util.ArrayList;
import java.util.StringJoiner;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class WebhooksApi {
  /**
   * Utility class for extending HttpRequest.Builder functionality.
   */
  private static class HttpRequestBuilderExtensions {
    /**
     * Adds additional headers to the provided HttpRequest.Builder. Useful for adding method/endpoint specific headers.
     *
     * @param builder the HttpRequest.Builder to which headers will be added
     * @param headers a map of header names and values to add; may be null
     * @return the same HttpRequest.Builder instance with the additional headers set
     */
    static HttpRequest.Builder withAdditionalHeaders(HttpRequest.Builder builder, Map<String, String> headers) {
        if (headers != null) {
            for (Map.Entry<String, String> entry : headers.entrySet()) {
                builder.header(entry.getKey(), entry.getValue());
            }
        }
        return builder;
    }
  }
  private final HttpClient memberVarHttpClient;
  private final ObjectMapper memberVarObjectMapper;
  private final String memberVarBaseUri;
  private final Consumer<HttpRequest.Builder> memberVarInterceptor;
  private final Duration memberVarReadTimeout;
  private final Consumer<HttpResponse<InputStream>> memberVarResponseInterceptor;
  private final Consumer<HttpResponse<InputStream>> memberVarAsyncResponseInterceptor;

  public WebhooksApi() {
    this(Configuration.getDefaultApiClient());
  }

  public WebhooksApi(ApiClient apiClient) {
    memberVarHttpClient = apiClient.getHttpClient();
    memberVarObjectMapper = apiClient.getObjectMapper();
    memberVarBaseUri = apiClient.getBaseUri();
    memberVarInterceptor = apiClient.getRequestInterceptor();
    memberVarReadTimeout = apiClient.getReadTimeout();
    memberVarResponseInterceptor = apiClient.getResponseInterceptor();
    memberVarAsyncResponseInterceptor = apiClient.getAsyncResponseInterceptor();
  }


  protected ApiException getApiException(String operationId, HttpResponse<InputStream> response) throws IOException {
    InputStream responseBody = ApiClient.getResponseBody(response);
    String body = null;
    try {
      body = responseBody == null ? null : new String(responseBody.readAllBytes());
    } finally {
      if (responseBody != null) {
        responseBody.close();
      }
    }
    String message = formatExceptionMessage(operationId, response.statusCode(), body);
    return new ApiException(response.statusCode(), message, response.headers(), body);
  }

  private String formatExceptionMessage(String operationId, int statusCode, String body) {
    if (body == null || body.isEmpty()) {
      body = "[no body]";
    }
    return operationId + " call failed with: " + statusCode + " - " + body;
  }

  /**
   * Download file from the given response.
   *
   * @param response Response
   * @return File
   * @throws ApiException If fail to read file content from response and write to disk
   */
  public File downloadFileFromResponse(HttpResponse<InputStream> response, InputStream responseBody) throws ApiException {
    if (responseBody == null) {
      throw new ApiException(new IOException("Response body is empty"));
    }
    try {
      File file = prepareDownloadFile(response);
      java.nio.file.Files.copy(responseBody, file.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
      return file;
    } catch (IOException e) {
      throw new ApiException(e);
    }
  }

  /**
   * <p>Prepare the file for download from the response.</p>
   *
   * @param response a {@link java.net.http.HttpResponse} object.
   * @return a {@link java.io.File} object.
   * @throws java.io.IOException if any.
   */
  private File prepareDownloadFile(HttpResponse<InputStream> response) throws IOException {
    String filename = null;
    java.util.Optional<String> contentDisposition = response.headers().firstValue("Content-Disposition");
    if (contentDisposition.isPresent() && !"".equals(contentDisposition.get())) {
      // Get filename from the Content-Disposition header.
      java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("filename=['\"]?([^'\"\\s]+)['\"]?");
      java.util.regex.Matcher matcher = pattern.matcher(contentDisposition.get());
      if (matcher.find())
        filename = matcher.group(1);
    }
    File file = null;
    if (filename != null) {
      java.nio.file.Path tempDir = java.nio.file.Files.createTempDirectory("swagger-gen-native");
      java.nio.file.Path filePath = java.nio.file.Files.createFile(tempDir.resolve(filename));
      file = filePath.toFile();
      tempDir.toFile().deleteOnExit();   // best effort cleanup
      file.deleteOnExit(); // best effort cleanup
    } else {
      file = java.nio.file.Files.createTempFile("download-", "").toFile();
      file.deleteOnExit(); // best effort cleanup
    }
    return file;
  }

  /**
   * Register a webhook endpoint
   * Registers an endpoint and returns its signing secret. **This is the only time the secret is shown** — store it before you close the response.  &#x60;Idempotency-Key&#x60; is required. Repeating the request with the same key and body returns the same endpoint and the same secret, with &#x60;Idempotency-Replayed: true&#x60;; the same key with a different body answers &#x60;409&#x60;.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param webhookEndpointCreateRequest  (required)
   * @return WebhookEndpointCreatedEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointCreatedEnvelope createWebhookEndpoint(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull WebhookEndpointCreateRequest webhookEndpointCreateRequest) throws ApiException {
    return createWebhookEndpoint(idempotencyKey, webhookEndpointCreateRequest, null);
  }

  /**
   * Register a webhook endpoint
   * Registers an endpoint and returns its signing secret. **This is the only time the secret is shown** — store it before you close the response.  &#x60;Idempotency-Key&#x60; is required. Repeating the request with the same key and body returns the same endpoint and the same secret, with &#x60;Idempotency-Replayed: true&#x60;; the same key with a different body answers &#x60;409&#x60;.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param webhookEndpointCreateRequest  (required)
   * @param headers Optional headers to include in the request
   * @return WebhookEndpointCreatedEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointCreatedEnvelope createWebhookEndpoint(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull WebhookEndpointCreateRequest webhookEndpointCreateRequest, Map<String, String> headers) throws ApiException {
    ApiResponse<WebhookEndpointCreatedEnvelope> localVarResponse = createWebhookEndpointWithHttpInfo(idempotencyKey, webhookEndpointCreateRequest, headers);
    return localVarResponse.getData();
  }

  /**
   * Register a webhook endpoint
   * Registers an endpoint and returns its signing secret. **This is the only time the secret is shown** — store it before you close the response.  &#x60;Idempotency-Key&#x60; is required. Repeating the request with the same key and body returns the same endpoint and the same secret, with &#x60;Idempotency-Replayed: true&#x60;; the same key with a different body answers &#x60;409&#x60;.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param webhookEndpointCreateRequest  (required)
   * @return ApiResponse&lt;WebhookEndpointCreatedEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointCreatedEnvelope> createWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull WebhookEndpointCreateRequest webhookEndpointCreateRequest) throws ApiException {
    return createWebhookEndpointWithHttpInfo(idempotencyKey, webhookEndpointCreateRequest, null);
  }

  /**
   * Register a webhook endpoint
   * Registers an endpoint and returns its signing secret. **This is the only time the secret is shown** — store it before you close the response.  &#x60;Idempotency-Key&#x60; is required. Repeating the request with the same key and body returns the same endpoint and the same secret, with &#x60;Idempotency-Replayed: true&#x60;; the same key with a different body answers &#x60;409&#x60;.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param webhookEndpointCreateRequest  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;WebhookEndpointCreatedEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointCreatedEnvelope> createWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull WebhookEndpointCreateRequest webhookEndpointCreateRequest, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = createWebhookEndpointRequestBuilder(idempotencyKey, webhookEndpointCreateRequest, headers);
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequestBuilder.build(),
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("createWebhookEndpoint", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<WebhookEndpointCreatedEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes());
        WebhookEndpointCreatedEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<WebhookEndpointCreatedEnvelope>() {});


        return new ApiResponse<WebhookEndpointCreatedEnvelope>(
            localVarResponse.statusCode(),
            localVarResponse.headers().map(),
            responseValue
        );
      } finally {
        if (localVarResponseBody != null) {
          localVarResponseBody.close();
        }
      }
    } catch (IOException e) {
      throw new ApiException(e);
    }
    catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ApiException(e);
    }
  }

  private HttpRequest.Builder createWebhookEndpointRequestBuilder(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull WebhookEndpointCreateRequest webhookEndpointCreateRequest, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'idempotencyKey' is set
    if (idempotencyKey == null) {
      throw new ApiException(400, "Missing the required parameter 'idempotencyKey' when calling createWebhookEndpoint");
    }
    // verify the required parameter 'webhookEndpointCreateRequest' is set
    if (webhookEndpointCreateRequest == null) {
      throw new ApiException(400, "Missing the required parameter 'webhookEndpointCreateRequest' when calling createWebhookEndpoint");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/webhook-endpoints";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    if (idempotencyKey != null) {
      localVarRequestBuilder.header("Idempotency-Key", idempotencyKey.toString());
    }
    localVarRequestBuilder.header("Content-Type", "application/json");
    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    try {
      byte[] localVarPostBody = memberVarObjectMapper.writeValueAsBytes(webhookEndpointCreateRequest);
      localVarRequestBuilder.method("POST", HttpRequest.BodyPublishers.ofByteArray(localVarPostBody));
    } catch (IOException e) {
      throw new ApiException(e);
    }
    if (memberVarReadTimeout != null) {
      localVarRequestBuilder.timeout(memberVarReadTimeout);
    }
    // Add custom headers if provided
    localVarRequestBuilder = HttpRequestBuilderExtensions.withAdditionalHeaders(localVarRequestBuilder, headers);
    if (memberVarInterceptor != null) {
      memberVarInterceptor.accept(localVarRequestBuilder);
    }
    return localVarRequestBuilder;
  }

  /**
   * Remove a webhook endpoint
   *
   * @param id  (required)
   * @return WebhookEndpointDeletionEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointDeletionEnvelope deleteWebhookEndpoint(@javax.annotation.Nonnull UUID id) throws ApiException {
    return deleteWebhookEndpoint(id, null);
  }

  /**
   * Remove a webhook endpoint
   *
   * @param id  (required)
   * @param headers Optional headers to include in the request
   * @return WebhookEndpointDeletionEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointDeletionEnvelope deleteWebhookEndpoint(@javax.annotation.Nonnull UUID id, Map<String, String> headers) throws ApiException {
    ApiResponse<WebhookEndpointDeletionEnvelope> localVarResponse = deleteWebhookEndpointWithHttpInfo(id, headers);
    return localVarResponse.getData();
  }

  /**
   * Remove a webhook endpoint
   *
   * @param id  (required)
   * @return ApiResponse&lt;WebhookEndpointDeletionEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointDeletionEnvelope> deleteWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull UUID id) throws ApiException {
    return deleteWebhookEndpointWithHttpInfo(id, null);
  }

  /**
   * Remove a webhook endpoint
   *
   * @param id  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;WebhookEndpointDeletionEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointDeletionEnvelope> deleteWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull UUID id, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = deleteWebhookEndpointRequestBuilder(id, headers);
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequestBuilder.build(),
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("deleteWebhookEndpoint", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<WebhookEndpointDeletionEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes());
        WebhookEndpointDeletionEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<WebhookEndpointDeletionEnvelope>() {});


        return new ApiResponse<WebhookEndpointDeletionEnvelope>(
            localVarResponse.statusCode(),
            localVarResponse.headers().map(),
            responseValue
        );
      } finally {
        if (localVarResponseBody != null) {
          localVarResponseBody.close();
        }
      }
    } catch (IOException e) {
      throw new ApiException(e);
    }
    catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ApiException(e);
    }
  }

  private HttpRequest.Builder deleteWebhookEndpointRequestBuilder(@javax.annotation.Nonnull UUID id, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'id' is set
    if (id == null) {
      throw new ApiException(400, "Missing the required parameter 'id' when calling deleteWebhookEndpoint");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/webhook-endpoints/{id}"
        .replace("{id}", ApiClient.urlEncode(id.toString()));

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    localVarRequestBuilder.method("DELETE", HttpRequest.BodyPublishers.noBody());
    if (memberVarReadTimeout != null) {
      localVarRequestBuilder.timeout(memberVarReadTimeout);
    }
    // Add custom headers if provided
    localVarRequestBuilder = HttpRequestBuilderExtensions.withAdditionalHeaders(localVarRequestBuilder, headers);
    if (memberVarInterceptor != null) {
      memberVarInterceptor.accept(localVarRequestBuilder);
    }
    return localVarRequestBuilder;
  }

  /**
   * List webhook endpoints
   * Every endpoint registered for the tenant. A signing secret is never returned here — only by the create, and by an update that changed the &#x60;url&#x60;. The custom &#x60;headers&#x60; are returned, which is why listing needs the same scope as writing.
   * @return WebhookEndpointListEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointListEnvelope listWebhookEndpoints() throws ApiException {
    return listWebhookEndpoints(null);
  }

  /**
   * List webhook endpoints
   * Every endpoint registered for the tenant. A signing secret is never returned here — only by the create, and by an update that changed the &#x60;url&#x60;. The custom &#x60;headers&#x60; are returned, which is why listing needs the same scope as writing.
   * @param headers Optional headers to include in the request
   * @return WebhookEndpointListEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointListEnvelope listWebhookEndpoints(Map<String, String> headers) throws ApiException {
    ApiResponse<WebhookEndpointListEnvelope> localVarResponse = listWebhookEndpointsWithHttpInfo(headers);
    return localVarResponse.getData();
  }

  /**
   * List webhook endpoints
   * Every endpoint registered for the tenant. A signing secret is never returned here — only by the create, and by an update that changed the &#x60;url&#x60;. The custom &#x60;headers&#x60; are returned, which is why listing needs the same scope as writing.
   * @return ApiResponse&lt;WebhookEndpointListEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointListEnvelope> listWebhookEndpointsWithHttpInfo() throws ApiException {
    return listWebhookEndpointsWithHttpInfo(null);
  }

  /**
   * List webhook endpoints
   * Every endpoint registered for the tenant. A signing secret is never returned here — only by the create, and by an update that changed the &#x60;url&#x60;. The custom &#x60;headers&#x60; are returned, which is why listing needs the same scope as writing.
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;WebhookEndpointListEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointListEnvelope> listWebhookEndpointsWithHttpInfo(Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = listWebhookEndpointsRequestBuilder(headers);
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequestBuilder.build(),
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("listWebhookEndpoints", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<WebhookEndpointListEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes());
        WebhookEndpointListEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<WebhookEndpointListEnvelope>() {});


        return new ApiResponse<WebhookEndpointListEnvelope>(
            localVarResponse.statusCode(),
            localVarResponse.headers().map(),
            responseValue
        );
      } finally {
        if (localVarResponseBody != null) {
          localVarResponseBody.close();
        }
      }
    } catch (IOException e) {
      throw new ApiException(e);
    }
    catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ApiException(e);
    }
  }

  private HttpRequest.Builder listWebhookEndpointsRequestBuilder(Map<String, String> headers) throws ApiException {

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/webhook-endpoints";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    localVarRequestBuilder.method("GET", HttpRequest.BodyPublishers.noBody());
    if (memberVarReadTimeout != null) {
      localVarRequestBuilder.timeout(memberVarReadTimeout);
    }
    // Add custom headers if provided
    localVarRequestBuilder = HttpRequestBuilderExtensions.withAdditionalHeaders(localVarRequestBuilder, headers);
    if (memberVarInterceptor != null) {
      memberVarInterceptor.accept(localVarRequestBuilder);
    }
    return localVarRequestBuilder;
  }

  /**
   * Replace a webhook endpoint
   * Replaces every field. **Changing &#x60;url&#x60; rotates the signing secret**, and the new one is returned as &#x60;data.secret&#x60; on this response only. Deliveries already in flight were signed with the old secret, so accept both until they drain. An update that keeps the &#x60;url&#x60; keeps the secret and returns &#x60;secret: null&#x60;.  &#x60;Idempotency-Key&#x60; is required, with the same replay rules as the create.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param id  (required)
   * @param webhookEndpointUpdateRequest  (required)
   * @return WebhookEndpointEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointEnvelope updateWebhookEndpoint(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull UUID id, @javax.annotation.Nonnull WebhookEndpointUpdateRequest webhookEndpointUpdateRequest) throws ApiException {
    return updateWebhookEndpoint(idempotencyKey, id, webhookEndpointUpdateRequest, null);
  }

  /**
   * Replace a webhook endpoint
   * Replaces every field. **Changing &#x60;url&#x60; rotates the signing secret**, and the new one is returned as &#x60;data.secret&#x60; on this response only. Deliveries already in flight were signed with the old secret, so accept both until they drain. An update that keeps the &#x60;url&#x60; keeps the secret and returns &#x60;secret: null&#x60;.  &#x60;Idempotency-Key&#x60; is required, with the same replay rules as the create.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param id  (required)
   * @param webhookEndpointUpdateRequest  (required)
   * @param headers Optional headers to include in the request
   * @return WebhookEndpointEnvelope
   * @throws ApiException if fails to make API call
   */
  public WebhookEndpointEnvelope updateWebhookEndpoint(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull UUID id, @javax.annotation.Nonnull WebhookEndpointUpdateRequest webhookEndpointUpdateRequest, Map<String, String> headers) throws ApiException {
    ApiResponse<WebhookEndpointEnvelope> localVarResponse = updateWebhookEndpointWithHttpInfo(idempotencyKey, id, webhookEndpointUpdateRequest, headers);
    return localVarResponse.getData();
  }

  /**
   * Replace a webhook endpoint
   * Replaces every field. **Changing &#x60;url&#x60; rotates the signing secret**, and the new one is returned as &#x60;data.secret&#x60; on this response only. Deliveries already in flight were signed with the old secret, so accept both until they drain. An update that keeps the &#x60;url&#x60; keeps the secret and returns &#x60;secret: null&#x60;.  &#x60;Idempotency-Key&#x60; is required, with the same replay rules as the create.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param id  (required)
   * @param webhookEndpointUpdateRequest  (required)
   * @return ApiResponse&lt;WebhookEndpointEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointEnvelope> updateWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull UUID id, @javax.annotation.Nonnull WebhookEndpointUpdateRequest webhookEndpointUpdateRequest) throws ApiException {
    return updateWebhookEndpointWithHttpInfo(idempotencyKey, id, webhookEndpointUpdateRequest, null);
  }

  /**
   * Replace a webhook endpoint
   * Replaces every field. **Changing &#x60;url&#x60; rotates the signing secret**, and the new one is returned as &#x60;data.secret&#x60; on this response only. Deliveries already in flight were signed with the old secret, so accept both until they drain. An update that keeps the &#x60;url&#x60; keeps the secret and returns &#x60;secret: null&#x60;.  &#x60;Idempotency-Key&#x60; is required, with the same replay rules as the create.
   * @param idempotencyKey Your identifier for this write, so a retry cannot register or change an endpoint twice. Reuse it only to repeat the identical request. Kept for 24 hours.  (required)
   * @param id  (required)
   * @param webhookEndpointUpdateRequest  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;WebhookEndpointEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<WebhookEndpointEnvelope> updateWebhookEndpointWithHttpInfo(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull UUID id, @javax.annotation.Nonnull WebhookEndpointUpdateRequest webhookEndpointUpdateRequest, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = updateWebhookEndpointRequestBuilder(idempotencyKey, id, webhookEndpointUpdateRequest, headers);
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequestBuilder.build(),
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("updateWebhookEndpoint", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<WebhookEndpointEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes());
        WebhookEndpointEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<WebhookEndpointEnvelope>() {});


        return new ApiResponse<WebhookEndpointEnvelope>(
            localVarResponse.statusCode(),
            localVarResponse.headers().map(),
            responseValue
        );
      } finally {
        if (localVarResponseBody != null) {
          localVarResponseBody.close();
        }
      }
    } catch (IOException e) {
      throw new ApiException(e);
    }
    catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new ApiException(e);
    }
  }

  private HttpRequest.Builder updateWebhookEndpointRequestBuilder(@javax.annotation.Nonnull String idempotencyKey, @javax.annotation.Nonnull UUID id, @javax.annotation.Nonnull WebhookEndpointUpdateRequest webhookEndpointUpdateRequest, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'idempotencyKey' is set
    if (idempotencyKey == null) {
      throw new ApiException(400, "Missing the required parameter 'idempotencyKey' when calling updateWebhookEndpoint");
    }
    // verify the required parameter 'id' is set
    if (id == null) {
      throw new ApiException(400, "Missing the required parameter 'id' when calling updateWebhookEndpoint");
    }
    // verify the required parameter 'webhookEndpointUpdateRequest' is set
    if (webhookEndpointUpdateRequest == null) {
      throw new ApiException(400, "Missing the required parameter 'webhookEndpointUpdateRequest' when calling updateWebhookEndpoint");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/webhook-endpoints/{id}"
        .replace("{id}", ApiClient.urlEncode(id.toString()));

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    if (idempotencyKey != null) {
      localVarRequestBuilder.header("Idempotency-Key", idempotencyKey.toString());
    }
    localVarRequestBuilder.header("Content-Type", "application/json");
    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    try {
      byte[] localVarPostBody = memberVarObjectMapper.writeValueAsBytes(webhookEndpointUpdateRequest);
      localVarRequestBuilder.method("PUT", HttpRequest.BodyPublishers.ofByteArray(localVarPostBody));
    } catch (IOException e) {
      throw new ApiException(e);
    }
    if (memberVarReadTimeout != null) {
      localVarRequestBuilder.timeout(memberVarReadTimeout);
    }
    // Add custom headers if provided
    localVarRequestBuilder = HttpRequestBuilderExtensions.withAdditionalHeaders(localVarRequestBuilder, headers);
    if (memberVarInterceptor != null) {
      memberVarInterceptor.accept(localVarRequestBuilder);
    }
    return localVarRequestBuilder;
  }

}
