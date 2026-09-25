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

import ai.cogneris.documentai.model.Envelope;
import java.io.File;
import ai.cogneris.documentai.model.ProblemDetails;
import ai.cogneris.documentai.model.ServiceErrorEnvelope;

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
public class DocumentsApi {
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

  public DocumentsApi() {
    this(Configuration.getDefaultApiClient());
  }

  public DocumentsApi(ApiClient apiClient) {
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
      body = responseBody == null ? null : new String(responseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
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
   * Classify one or more documents
   * Detects the document type against the classes configured for your tenant. Repeat the &#x60;files&#x60; field to classify several documents in one call.
   * @param files One or more files to classify. (required)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope classifyDocuments(@javax.annotation.Nonnull List<File> files) throws ApiException {
    return classifyDocuments(files, null);
  }

  /**
   * Classify one or more documents
   * Detects the document type against the classes configured for your tenant. Repeat the &#x60;files&#x60; field to classify several documents in one call.
   * @param files One or more files to classify. (required)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope classifyDocuments(@javax.annotation.Nonnull List<File> files, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = classifyDocumentsWithHttpInfo(files, headers);
    return localVarResponse.getData();
  }

  /**
   * Classify one or more documents
   * Detects the document type against the classes configured for your tenant. Repeat the &#x60;files&#x60; field to classify several documents in one call.
   * @param files One or more files to classify. (required)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> classifyDocumentsWithHttpInfo(@javax.annotation.Nonnull List<File> files) throws ApiException {
    return classifyDocumentsWithHttpInfo(files, null);
  }

  /**
   * Classify one or more documents
   * Detects the document type against the classes configured for your tenant. Repeat the &#x60;files&#x60; field to classify several documents in one call.
   * @param files One or more files to classify. (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> classifyDocumentsWithHttpInfo(@javax.annotation.Nonnull List<File> files, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = classifyDocumentsRequestBuilder(files, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("classifyDocuments", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder classifyDocumentsRequestBuilder(@javax.annotation.Nonnull List<File> files, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'files' is set
    if (files == null) {
      throw new ApiException(400, "Missing the required parameter 'files' when calling classifyDocuments");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/classifier";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    for (int i=0; i < files.size(); i++) {
        multiPartBuilder.addBinaryBody("files", files.get(i));
        hasFiles = true;
    }
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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
   * Crop pages to the document
   * Trims pages down to the document itself — useful when the source is a photo or a scan with a border, a desk or a second page in frame.
   * @param _file  (required)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope cropDocument(@javax.annotation.Nonnull File _file) throws ApiException {
    return cropDocument(_file, null);
  }

  /**
   * Crop pages to the document
   * Trims pages down to the document itself — useful when the source is a photo or a scan with a border, a desk or a second page in frame.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope cropDocument(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = cropDocumentWithHttpInfo(_file, headers);
    return localVarResponse.getData();
  }

  /**
   * Crop pages to the document
   * Trims pages down to the document itself — useful when the source is a photo or a scan with a border, a desk or a second page in frame.
   * @param _file  (required)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> cropDocumentWithHttpInfo(@javax.annotation.Nonnull File _file) throws ApiException {
    return cropDocumentWithHttpInfo(_file, null);
  }

  /**
   * Crop pages to the document
   * Trims pages down to the document itself — useful when the source is a photo or a scan with a border, a desk or a second page in frame.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> cropDocumentWithHttpInfo(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = cropDocumentRequestBuilder(_file, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("cropDocument", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder cropDocumentRequestBuilder(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    // verify the required parameter '_file' is set
    if (_file == null) {
      throw new ApiException(400, "Missing the required parameter '_file' when calling cropDocument");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/crop";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    multiPartBuilder.addBinaryBody("file", _file);
    hasFiles = true;
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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
   * Extract structured fields from a document
   * Extracts structured fields from a single document using the templates configured for your tenant. The platform selects the best template for the uploaded document.
   * @param _file The document to extract from. (required)
   * @param complementaryPrompt Free-text instruction appended to the model prompt. Use it to ask for extra fields, enforce formatting, or narrow the scope.  (optional)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope extractDocument(@javax.annotation.Nonnull File _file, @javax.annotation.Nullable String complementaryPrompt) throws ApiException {
    return extractDocument(_file, complementaryPrompt, null);
  }

  /**
   * Extract structured fields from a document
   * Extracts structured fields from a single document using the templates configured for your tenant. The platform selects the best template for the uploaded document.
   * @param _file The document to extract from. (required)
   * @param complementaryPrompt Free-text instruction appended to the model prompt. Use it to ask for extra fields, enforce formatting, or narrow the scope.  (optional)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope extractDocument(@javax.annotation.Nonnull File _file, @javax.annotation.Nullable String complementaryPrompt, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = extractDocumentWithHttpInfo(_file, complementaryPrompt, headers);
    return localVarResponse.getData();
  }

  /**
   * Extract structured fields from a document
   * Extracts structured fields from a single document using the templates configured for your tenant. The platform selects the best template for the uploaded document.
   * @param _file The document to extract from. (required)
   * @param complementaryPrompt Free-text instruction appended to the model prompt. Use it to ask for extra fields, enforce formatting, or narrow the scope.  (optional)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> extractDocumentWithHttpInfo(@javax.annotation.Nonnull File _file, @javax.annotation.Nullable String complementaryPrompt) throws ApiException {
    return extractDocumentWithHttpInfo(_file, complementaryPrompt, null);
  }

  /**
   * Extract structured fields from a document
   * Extracts structured fields from a single document using the templates configured for your tenant. The platform selects the best template for the uploaded document.
   * @param _file The document to extract from. (required)
   * @param complementaryPrompt Free-text instruction appended to the model prompt. Use it to ask for extra fields, enforce formatting, or narrow the scope.  (optional)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> extractDocumentWithHttpInfo(@javax.annotation.Nonnull File _file, @javax.annotation.Nullable String complementaryPrompt, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = extractDocumentRequestBuilder(_file, complementaryPrompt, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("extractDocument", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder extractDocumentRequestBuilder(@javax.annotation.Nonnull File _file, @javax.annotation.Nullable String complementaryPrompt, Map<String, String> headers) throws ApiException {
    // verify the required parameter '_file' is set
    if (_file == null) {
      throw new ApiException(400, "Missing the required parameter '_file' when calling extractDocument");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/extraction";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    multiPartBuilder.addBinaryBody("file", _file);
    hasFiles = true;
    if (complementaryPrompt != null) {
        multiPartBuilder.addTextBody("ComplementaryPrompt", complementaryPrompt.toString(), org.apache.http.entity.ContentType.TEXT_PLAIN.withCharset(java.nio.charset.StandardCharsets.UTF_8));
    }
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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
   * Match a selfie against identity documents
   *
   * @param selfie The selfie to compare. (required)
   * @param documents One or more identity documents to compare against. (required)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope faceMatchDocument(@javax.annotation.Nonnull File selfie, @javax.annotation.Nonnull List<File> documents) throws ApiException {
    return faceMatchDocument(selfie, documents, null);
  }

  /**
   * Match a selfie against identity documents
   *
   * @param selfie The selfie to compare. (required)
   * @param documents One or more identity documents to compare against. (required)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope faceMatchDocument(@javax.annotation.Nonnull File selfie, @javax.annotation.Nonnull List<File> documents, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = faceMatchDocumentWithHttpInfo(selfie, documents, headers);
    return localVarResponse.getData();
  }

  /**
   * Match a selfie against identity documents
   *
   * @param selfie The selfie to compare. (required)
   * @param documents One or more identity documents to compare against. (required)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> faceMatchDocumentWithHttpInfo(@javax.annotation.Nonnull File selfie, @javax.annotation.Nonnull List<File> documents) throws ApiException {
    return faceMatchDocumentWithHttpInfo(selfie, documents, null);
  }

  /**
   * Match a selfie against identity documents
   *
   * @param selfie The selfie to compare. (required)
   * @param documents One or more identity documents to compare against. (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> faceMatchDocumentWithHttpInfo(@javax.annotation.Nonnull File selfie, @javax.annotation.Nonnull List<File> documents, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = faceMatchDocumentRequestBuilder(selfie, documents, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("faceMatchDocument", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder faceMatchDocumentRequestBuilder(@javax.annotation.Nonnull File selfie, @javax.annotation.Nonnull List<File> documents, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'selfie' is set
    if (selfie == null) {
      throw new ApiException(400, "Missing the required parameter 'selfie' when calling faceMatchDocument");
    }
    // verify the required parameter 'documents' is set
    if (documents == null) {
      throw new ApiException(400, "Missing the required parameter 'documents' when calling faceMatchDocument");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/facematch";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    multiPartBuilder.addBinaryBody("selfie", selfie);
    hasFiles = true;
    for (int i=0; i < documents.size(); i++) {
        multiPartBuilder.addBinaryBody("documents", documents.get(i));
        hasFiles = true;
    }
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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
   * Split a bundle into its documents
   * Breaks one file into the documents it contains, returning a detected type and page range per segment. Accepts files up to 500 MB — well above the 10 MB limit that applies to the other document endpoints. PDFs work best; other supported formats are accepted but usually return a single segment.
   * @param _file  (required)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope splitDocument(@javax.annotation.Nonnull File _file) throws ApiException {
    return splitDocument(_file, null);
  }

  /**
   * Split a bundle into its documents
   * Breaks one file into the documents it contains, returning a detected type and page range per segment. Accepts files up to 500 MB — well above the 10 MB limit that applies to the other document endpoints. PDFs work best; other supported formats are accepted but usually return a single segment.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope splitDocument(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = splitDocumentWithHttpInfo(_file, headers);
    return localVarResponse.getData();
  }

  /**
   * Split a bundle into its documents
   * Breaks one file into the documents it contains, returning a detected type and page range per segment. Accepts files up to 500 MB — well above the 10 MB limit that applies to the other document endpoints. PDFs work best; other supported formats are accepted but usually return a single segment.
   * @param _file  (required)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> splitDocumentWithHttpInfo(@javax.annotation.Nonnull File _file) throws ApiException {
    return splitDocumentWithHttpInfo(_file, null);
  }

  /**
   * Split a bundle into its documents
   * Breaks one file into the documents it contains, returning a detected type and page range per segment. Accepts files up to 500 MB — well above the 10 MB limit that applies to the other document endpoints. PDFs work best; other supported formats are accepted but usually return a single segment.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> splitDocumentWithHttpInfo(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = splitDocumentRequestBuilder(_file, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("splitDocument", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder splitDocumentRequestBuilder(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    // verify the required parameter '_file' is set
    if (_file == null) {
      throw new ApiException(400, "Missing the required parameter '_file' when calling splitDocument");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/split";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    multiPartBuilder.addBinaryBody("file", _file);
    hasFiles = true;
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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
   * Discover fields without a template
   * Reports the fields the model can find in a document you have no template for, each with a confidence score from &#x60;0&#x60; to &#x60;100&#x60;.
   * @param _file  (required)
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope zeroShotDocument(@javax.annotation.Nonnull File _file) throws ApiException {
    return zeroShotDocument(_file, null);
  }

  /**
   * Discover fields without a template
   * Reports the fields the model can find in a document you have no template for, each with a confidence score from &#x60;0&#x60; to &#x60;100&#x60;.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return Envelope
   * @throws ApiException if fails to make API call
   */
  public Envelope zeroShotDocument(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    ApiResponse<Envelope> localVarResponse = zeroShotDocumentWithHttpInfo(_file, headers);
    return localVarResponse.getData();
  }

  /**
   * Discover fields without a template
   * Reports the fields the model can find in a document you have no template for, each with a confidence score from &#x60;0&#x60; to &#x60;100&#x60;.
   * @param _file  (required)
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> zeroShotDocumentWithHttpInfo(@javax.annotation.Nonnull File _file) throws ApiException {
    return zeroShotDocumentWithHttpInfo(_file, null);
  }

  /**
   * Discover fields without a template
   * Reports the fields the model can find in a document you have no template for, each with a confidence score from &#x60;0&#x60; to &#x60;100&#x60;.
   * @param _file  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;Envelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<Envelope> zeroShotDocumentWithHttpInfo(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = zeroShotDocumentRequestBuilder(_file, headers);
    HttpRequest localVarRequest = localVarRequestBuilder.build();
    try {
      HttpResponse<InputStream> localVarResponse = memberVarHttpClient.send(
          localVarRequest,
          HttpResponse.BodyHandlers.ofInputStream());
      if (memberVarResponseInterceptor != null) {
        memberVarResponseInterceptor.accept(localVarResponse);
      }
      InputStream localVarResponseBody = null;
      try {
        if (localVarResponse.statusCode()/ 100 != 2) {
          throw getApiException("zeroShotDocument", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<Envelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        Envelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<Envelope>() {});


        return new ApiResponse<Envelope>(
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
    } finally {
      localVarRequest.bodyPublisher().ifPresent(publisher -> {
        if (publisher instanceof MultipartBodyPublisher multipart) multipart.close();
      });
    }
  }

  private HttpRequest.Builder zeroShotDocumentRequestBuilder(@javax.annotation.Nonnull File _file, Map<String, String> headers) throws ApiException {
    // verify the required parameter '_file' is set
    if (_file == null) {
      throw new ApiException(400, "Missing the required parameter '_file' when calling zeroShotDocument");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/Document/zero-shot";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    MultipartEntityBuilder multiPartBuilder = MultipartEntityBuilder.create();
    boolean hasFiles = false;
    multiPartBuilder.addBinaryBody("file", _file);
    hasFiles = true;
    HttpEntity entity = multiPartBuilder.build();
    HttpRequest.BodyPublisher formDataPublisher;
    if (hasFiles) {
        formDataPublisher = new MultipartBodyPublisher(entity);
    } else {
        ByteArrayOutputStream formOutputStream = new ByteArrayOutputStream();
        try {
            entity.writeTo(formOutputStream);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        byte[] formBytes = formOutputStream.toByteArray();
        formDataPublisher = HttpRequest.BodyPublishers
            .ofInputStream(() -> new ByteArrayInputStream(formBytes));
    }
    localVarRequestBuilder
        .header("Content-Type", entity.getContentType().getValue())
        .method("POST", formDataPublisher);
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

  /** Owns the generated Apache multipart serializer's producer and both pipe ends. */
  private static final class MultipartBodyPublisher implements HttpRequest.BodyPublisher, AutoCloseable {
    private final HttpEntity entity;
    private final java.util.Set<Upload> active = new java.util.HashSet<>();
    private final HttpRequest.BodyPublisher delegate = HttpRequest.BodyPublishers.ofInputStream(this::open);
    private boolean closed;

    MultipartBodyPublisher(HttpEntity entity) {
      this.entity = entity;
    }

    @Override public long contentLength() { return delegate.contentLength(); }

    @Override public void subscribe(java.util.concurrent.Flow.Subscriber<? super java.nio.ByteBuffer> subscriber) {
      delegate.subscribe(subscriber);
    }

    private synchronized InputStream open() {
      if (closed) throw new IllegalStateException("Multipart upload is closed.");
      try {
        Upload upload = new Upload(Pipe.open());
        active.add(upload);
        upload.producer.start();
        return upload;
      } catch (IOException error) {
        throw new java.io.UncheckedIOException(new IOException("Multipart upload could not start."));
      }
    }

    @Override public void close() {
      java.util.List<Upload> uploads;
      synchronized (this) {
        if (closed) return;
        closed = true;
        uploads = new java.util.ArrayList<>(active);
        active.clear();
      }
      for (Upload upload : uploads) upload.close();
    }

    private final class Upload extends InputStream {
      private final Pipe pipe;
      private final InputStream source;
      private final Thread producer;
      private volatile IOException failure;
      private boolean stopped;

      Upload(Pipe pipe) {
        this.pipe = pipe;
        source = Channels.newInputStream(pipe.source());
        producer = new Thread(() -> {
          try {
            entity.writeTo(Channels.newOutputStream(pipe.sink()));
          } catch (IOException | RuntimeException error) {
            // No document path, bytes, or raw exception may escape through stderr.
            // Record failure before closing the sink makes EOF visible to the reader.
            failure = new IOException("Multipart upload could not be produced.");
          } finally {
            closeChannel(pipe.sink());
          }
        }, "cogneris-sdk-upload");
        producer.setDaemon(true);
      }

      @Override public int read() throws IOException {
        int result = source.read();
        if (result < 0 && failure != null) throw failure;
        return result;
      }

      @Override public int read(byte[] bytes, int offset, int length) throws IOException {
        int result = source.read(bytes, offset, length);
        if (result < 0 && failure != null) throw failure;
        return result;
      }

      @Override public void close() {
        synchronized (this) {
          if (stopped) return;
          stopped = true;
        }
        // Close channels directly: a blocked Channels input stream can hold its read monitor.
        closeChannel(pipe.source());
        closeChannel(pipe.sink());
        producer.interrupt();
        boolean interrupted = Thread.interrupted();
        try {
          long start = System.nanoTime();
          while (producer.isAlive() && producer != Thread.currentThread()) {
            long left = 1_000_000_000L - (System.nanoTime() - start);
            if (left <= 0) break;
            try { producer.join(left / 1_000_000, (int) (left % 1_000_000)); }
            catch (InterruptedException error) { interrupted = true; }
          }
        } finally {
          if (interrupted) Thread.currentThread().interrupt();
          synchronized (MultipartBodyPublisher.this) { active.remove(this); }
        }
      }
    }

    private static void closeChannel(java.nio.channels.Channel channel) {
      try { channel.close(); } catch (IOException ignored) { }
    }
  }

}
