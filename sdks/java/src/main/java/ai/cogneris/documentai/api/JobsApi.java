/*
 * Cogneris Document AI API
 * The Cogneris Document AI API turns unstructured documents — PDFs, images, scans — into structured JSON.  This document describes the endpoints that are actually deployed. It is written from the running service (`cogneris-api-be`) rather than from a design, so what is listed here is what you can call.  ## Authentication  Every endpoint takes an API key in the `Authorization` header as `Bearer <key>`. Keys begin with `xtkt_live_` (production) or `xtkt_test_` (sandbox); either prefix is accepted before the key is looked up for validation. The key selects the application environment. A recognized prefix alone does not authenticate a request: the key must also be valid and active. Keys are tenant-scoped and cannot cross tenant boundaries. Mint them in the dashboard under **Settings → API keys**.  ## Uploads  The synchronous document endpoints take `multipart/form-data`. There is no fetch-by-URL variant — the file travels in the request body.  - Accepted extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`,   `.bmp`, `.doc`, `.docx` - Maximum size: 10 MB per file, except `/Document/split`, which accepts 500 MB  The asynchronous job endpoints do not take a file. Upload it first to `POST /api/v1/artifacts` — same extensions, same 10 MB limit — and submit the `artifact://` reference it returns.  ## Artifact references  A reference names one stored object. `POST /api/v1/artifacts` returns one, a job submit consumes one as `inputReference`, and a finished job returns one as `outputReference`. `GET /api/v1/artifacts/content` turns either back into bytes.  - References are scoped to the tenant that created them. One belonging to another   tenant is refused as an invalid reference — the answer does not distinguish a   reference that exists elsewhere from one that never existed. - An uploaded reference is **reusable**: one upload can back several jobs. - It expires **7 days** after upload, matching how long a job is retained. The   exact instant is returned as `expiresAt`. Reading it afterwards answers `410`,   which is not `404` — the reference was real, it aged out, and re-requesting it   will never succeed. Upload again. - A job's `outputReference` lives as long as the job does.  ### Two shapes, one of them historical  Everything this API produces today is `artifact://<key>`. Jobs that completed before 2026-09-22 carry a bucket-qualified path instead — `<bucket>/<tenant>/document-jobs/<jobId>/result.json`, sometimes with an `@<version>` suffix. `GET /api/v1/artifacts/content` accepts both, so a reference stored from an older job still resolves for the rest of its life. Treat a reference as opaque: pass back exactly what you were given.  ## Templates  Extraction and classification are driven by the document types and templates configured for your tenant. The platform selects the template from the document itself, so the synchronous `/Document/_*` calls take no template or schema parameter. An asynchronous Extraction job may instead name one explicitly with `templateId` on `POST /api/v1/document-jobs`.  ## Scopes  Keys carry scopes. The Portal endpoints check them and answer `403` when the required one is absent; the document endpoints accept any valid key for the tenant without consulting the list. `*` is a real scope meaning full access, and it is what a key receives when it is created without an explicit scope list.  ## Rate limits  One shared policy covers every surface in this document, Portal included: **50 requests per API key per fixed 1-minute window**. It is a fixed window rather than a token bucket, so the allowance resets on the minute instead of refilling gradually. Requests over the limit receive `429`.  ## Response envelope  Successful responses from the **document and job** endpoints share one wrapper: `data` for the payload, `meta` for the status and any messages, and `hasErrors` for a fast failure check.  The **Portal** endpoints do not use that wrapper. They return the payload directly, and their errors are RFC 9457 problem documents sent as `application/problem+json`, with a stable `code`, a `correlationId` that is also returned in the `x-correlation-id` header, and a `retryable` flag. Branch on `code`; treat `type` as an opaque identifier.  ## Errors  An error arrives in one of two shapes, and the `Content-Type` says which.  - `application/problem+json` — an RFC 9457 problem document, the same one the   Portal uses. Every route answers this way when the failure happens before your   request is processed: a missing or invalid key (`401`), the rate limit (`429`),   a request refused as malformed or unsafe (`400`), or an unexpected failure   (`500`). - `application/json` — the service envelope with `hasErrors: true` and the   reasons in `meta.errors`. The document, job and artifact routes answer this way   when processing itself fails. Each operation lists the statuses where it does.  Every operation lists `400`, `401`, `403`, `404`, `409`, `429` and `500`, because the API answers each of them in the same shape wherever it occurs. A status on an operation with nothing to miss or conflict with — a `409` on a read, say — is part of that uniform model and not something the operation returns in practice.
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

import ai.cogneris.documentai.model.DocumentJobCancellationEnvelope;
import ai.cogneris.documentai.model.DocumentJobEnvelope;
import ai.cogneris.documentai.model.DocumentJobListEnvelope;
import ai.cogneris.documentai.model.DocumentJobSubmissionEnvelope;
import ai.cogneris.documentai.model.ProblemDetails;
import ai.cogneris.documentai.model.ServiceErrorEnvelope;
import ai.cogneris.documentai.model.SubmitDocumentJobRequest;
import java.util.UUID;

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
public class JobsApi {
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

  public JobsApi() {
    this(Configuration.getDefaultApiClient());
  }

  public JobsApi(ApiClient apiClient) {
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
   * Cancel a document job
   *
   * @param jobId  (required)
   * @return DocumentJobCancellationEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobCancellationEnvelope cancelDocumentJob(@javax.annotation.Nonnull UUID jobId) throws ApiException {
    return cancelDocumentJob(jobId, null);
  }

  /**
   * Cancel a document job
   *
   * @param jobId  (required)
   * @param headers Optional headers to include in the request
   * @return DocumentJobCancellationEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobCancellationEnvelope cancelDocumentJob(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    ApiResponse<DocumentJobCancellationEnvelope> localVarResponse = cancelDocumentJobWithHttpInfo(jobId, headers);
    return localVarResponse.getData();
  }

  /**
   * Cancel a document job
   *
   * @param jobId  (required)
   * @return ApiResponse&lt;DocumentJobCancellationEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobCancellationEnvelope> cancelDocumentJobWithHttpInfo(@javax.annotation.Nonnull UUID jobId) throws ApiException {
    return cancelDocumentJobWithHttpInfo(jobId, null);
  }

  /**
   * Cancel a document job
   *
   * @param jobId  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;DocumentJobCancellationEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobCancellationEnvelope> cancelDocumentJobWithHttpInfo(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = cancelDocumentJobRequestBuilder(jobId, headers);
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
          throw getApiException("cancelDocumentJob", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<DocumentJobCancellationEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        DocumentJobCancellationEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<DocumentJobCancellationEnvelope>() {});


        return new ApiResponse<DocumentJobCancellationEnvelope>(
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

  private HttpRequest.Builder cancelDocumentJobRequestBuilder(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'jobId' is set
    if (jobId == null) {
      throw new ApiException(400, "Missing the required parameter 'jobId' when calling cancelDocumentJob");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/document-jobs/{jobId}/cancel"
        .replace("{jobId}", ApiClient.urlEncode(jobId.toString()));

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    localVarRequestBuilder.method("POST", HttpRequest.BodyPublishers.noBody());
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
   * Get a document job
   *
   * @param jobId  (required)
   * @return DocumentJobEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobEnvelope getDocumentJob(@javax.annotation.Nonnull UUID jobId) throws ApiException {
    return getDocumentJob(jobId, null);
  }

  /**
   * Get a document job
   *
   * @param jobId  (required)
   * @param headers Optional headers to include in the request
   * @return DocumentJobEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobEnvelope getDocumentJob(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    ApiResponse<DocumentJobEnvelope> localVarResponse = getDocumentJobWithHttpInfo(jobId, headers);
    return localVarResponse.getData();
  }

  /**
   * Get a document job
   *
   * @param jobId  (required)
   * @return ApiResponse&lt;DocumentJobEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobEnvelope> getDocumentJobWithHttpInfo(@javax.annotation.Nonnull UUID jobId) throws ApiException {
    return getDocumentJobWithHttpInfo(jobId, null);
  }

  /**
   * Get a document job
   *
   * @param jobId  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;DocumentJobEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobEnvelope> getDocumentJobWithHttpInfo(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = getDocumentJobRequestBuilder(jobId, headers);
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
          throw getApiException("getDocumentJob", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<DocumentJobEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        DocumentJobEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<DocumentJobEnvelope>() {});


        return new ApiResponse<DocumentJobEnvelope>(
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

  private HttpRequest.Builder getDocumentJobRequestBuilder(@javax.annotation.Nonnull UUID jobId, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'jobId' is set
    if (jobId == null) {
      throw new ApiException(400, "Missing the required parameter 'jobId' when calling getDocumentJob");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/document-jobs/{jobId}"
        .replace("{jobId}", ApiClient.urlEncode(jobId.toString()));

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
   * List document jobs
   *
   * @param limit  (optional, default to 100)
   * @return DocumentJobListEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobListEnvelope listDocumentJobs(@javax.annotation.Nullable Integer limit) throws ApiException {
    return listDocumentJobs(limit, null);
  }

  /**
   * List document jobs
   *
   * @param limit  (optional, default to 100)
   * @param headers Optional headers to include in the request
   * @return DocumentJobListEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobListEnvelope listDocumentJobs(@javax.annotation.Nullable Integer limit, Map<String, String> headers) throws ApiException {
    ApiResponse<DocumentJobListEnvelope> localVarResponse = listDocumentJobsWithHttpInfo(limit, headers);
    return localVarResponse.getData();
  }

  /**
   * List document jobs
   *
   * @param limit  (optional, default to 100)
   * @return ApiResponse&lt;DocumentJobListEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobListEnvelope> listDocumentJobsWithHttpInfo(@javax.annotation.Nullable Integer limit) throws ApiException {
    return listDocumentJobsWithHttpInfo(limit, null);
  }

  /**
   * List document jobs
   *
   * @param limit  (optional, default to 100)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;DocumentJobListEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobListEnvelope> listDocumentJobsWithHttpInfo(@javax.annotation.Nullable Integer limit, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = listDocumentJobsRequestBuilder(limit, headers);
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
          throw getApiException("listDocumentJobs", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<DocumentJobListEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        DocumentJobListEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<DocumentJobListEnvelope>() {});


        return new ApiResponse<DocumentJobListEnvelope>(
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

  private HttpRequest.Builder listDocumentJobsRequestBuilder(@javax.annotation.Nullable Integer limit, Map<String, String> headers) throws ApiException {

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/document-jobs";

    List<Pair> localVarQueryParams = new ArrayList<>();
    StringJoiner localVarQueryStringJoiner = new StringJoiner("&");
    String localVarQueryParameterBaseName;
    localVarQueryParameterBaseName = "limit";
    localVarQueryParams.addAll(ApiClient.parameterToPairs("limit", limit));

    if (!localVarQueryParams.isEmpty() || localVarQueryStringJoiner.length() != 0) {
      StringJoiner queryJoiner = new StringJoiner("&");
      localVarQueryParams.forEach(p -> queryJoiner.add(p.getName() + '=' + p.getValue()));
      if (localVarQueryStringJoiner.length() != 0) {
        queryJoiner.add(localVarQueryStringJoiner.toString());
      }
      localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath + '?' + queryJoiner.toString()));
    } else {
      localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));
    }

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
   * Submit an asynchronous document job
   * Queues a long-running operation. Answers &#x60;202&#x60; with a &#x60;Location&#x60; header pointing at the job and a &#x60;Retry-After&#x60; hint. Poll that URL, or subscribe to webhooks and let the completion event come to you.
   * @param submitDocumentJobRequest  (required)
   * @return DocumentJobSubmissionEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobSubmissionEnvelope submitDocumentJob(@javax.annotation.Nonnull SubmitDocumentJobRequest submitDocumentJobRequest) throws ApiException {
    return submitDocumentJob(submitDocumentJobRequest, null);
  }

  /**
   * Submit an asynchronous document job
   * Queues a long-running operation. Answers &#x60;202&#x60; with a &#x60;Location&#x60; header pointing at the job and a &#x60;Retry-After&#x60; hint. Poll that URL, or subscribe to webhooks and let the completion event come to you.
   * @param submitDocumentJobRequest  (required)
   * @param headers Optional headers to include in the request
   * @return DocumentJobSubmissionEnvelope
   * @throws ApiException if fails to make API call
   */
  public DocumentJobSubmissionEnvelope submitDocumentJob(@javax.annotation.Nonnull SubmitDocumentJobRequest submitDocumentJobRequest, Map<String, String> headers) throws ApiException {
    ApiResponse<DocumentJobSubmissionEnvelope> localVarResponse = submitDocumentJobWithHttpInfo(submitDocumentJobRequest, headers);
    return localVarResponse.getData();
  }

  /**
   * Submit an asynchronous document job
   * Queues a long-running operation. Answers &#x60;202&#x60; with a &#x60;Location&#x60; header pointing at the job and a &#x60;Retry-After&#x60; hint. Poll that URL, or subscribe to webhooks and let the completion event come to you.
   * @param submitDocumentJobRequest  (required)
   * @return ApiResponse&lt;DocumentJobSubmissionEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobSubmissionEnvelope> submitDocumentJobWithHttpInfo(@javax.annotation.Nonnull SubmitDocumentJobRequest submitDocumentJobRequest) throws ApiException {
    return submitDocumentJobWithHttpInfo(submitDocumentJobRequest, null);
  }

  /**
   * Submit an asynchronous document job
   * Queues a long-running operation. Answers &#x60;202&#x60; with a &#x60;Location&#x60; header pointing at the job and a &#x60;Retry-After&#x60; hint. Poll that URL, or subscribe to webhooks and let the completion event come to you.
   * @param submitDocumentJobRequest  (required)
   * @param headers Optional headers to include in the request
   * @return ApiResponse&lt;DocumentJobSubmissionEnvelope&gt;
   * @throws ApiException if fails to make API call
   */
  public ApiResponse<DocumentJobSubmissionEnvelope> submitDocumentJobWithHttpInfo(@javax.annotation.Nonnull SubmitDocumentJobRequest submitDocumentJobRequest, Map<String, String> headers) throws ApiException {
    HttpRequest.Builder localVarRequestBuilder = submitDocumentJobRequestBuilder(submitDocumentJobRequest, headers);
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
          throw getApiException("submitDocumentJob", localVarResponse);
        }
        localVarResponseBody = ApiClient.getResponseBody(localVarResponse);
        if (localVarResponseBody == null) {
          return new ApiResponse<DocumentJobSubmissionEnvelope>(
              localVarResponse.statusCode(),
              localVarResponse.headers().map(),
              null
          );
        }



        String responseBody = new String(localVarResponseBody.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        DocumentJobSubmissionEnvelope responseValue = responseBody.isBlank()? null: memberVarObjectMapper.readValue(responseBody, new TypeReference<DocumentJobSubmissionEnvelope>() {});


        return new ApiResponse<DocumentJobSubmissionEnvelope>(
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

  private HttpRequest.Builder submitDocumentJobRequestBuilder(@javax.annotation.Nonnull SubmitDocumentJobRequest submitDocumentJobRequest, Map<String, String> headers) throws ApiException {
    // verify the required parameter 'submitDocumentJobRequest' is set
    if (submitDocumentJobRequest == null) {
      throw new ApiException(400, "Missing the required parameter 'submitDocumentJobRequest' when calling submitDocumentJob");
    }

    HttpRequest.Builder localVarRequestBuilder = HttpRequest.newBuilder();

    String localVarPath = "/api/v1/document-jobs";

    localVarRequestBuilder.uri(URI.create(memberVarBaseUri + localVarPath));

    localVarRequestBuilder.header("Content-Type", "application/json");
    localVarRequestBuilder.header("Accept", "application/json, application/problem+json");

    try {
      byte[] localVarPostBody = memberVarObjectMapper.writeValueAsBytes(submitDocumentJobRequest);
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

}
