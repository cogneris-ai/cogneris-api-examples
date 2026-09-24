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


package ai.cogneris.documentai.model;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.StringJoiner;
import java.util.Objects;
import java.util.Map;
import java.util.HashMap;
import ai.cogneris.documentai.model.DocumentJobOperation;
import ai.cogneris.documentai.model.DocumentJobStatus;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Arrays;
import java.util.UUID;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * DocumentJob
 */
@JsonPropertyOrder({
  DocumentJob.JSON_PROPERTY_JOB_ID,
  DocumentJob.JSON_PROPERTY_OPERATION,
  DocumentJob.JSON_PROPERTY_STATUS,
  DocumentJob.JSON_PROPERTY_OUTPUT_REFERENCE,
  DocumentJob.JSON_PROPERTY_STAGE,
  DocumentJob.JSON_PROPERTY_PROCESSED_PAGES,
  DocumentJob.JSON_PROPERTY_TOTAL_PAGES,
  DocumentJob.JSON_PROPERTY_ATTEMPT_COUNT,
  DocumentJob.JSON_PROPERTY_FAILURE_CODE,
  DocumentJob.JSON_PROPERTY_RETRYABLE,
  DocumentJob.JSON_PROPERTY_STARTED_AT,
  DocumentJob.JSON_PROPERTY_COMPLETED_AT,
  DocumentJob.JSON_PROPERTY_CANCELLATION_REQUESTED_AT,
  DocumentJob.JSON_PROPERTY_EXPIRES_AT,
  DocumentJob.JSON_PROPERTY_CREDITS_CONSUMED
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class DocumentJob {
  public static final String JSON_PROPERTY_JOB_ID = "jobId";
  @javax.annotation.Nullable
  private UUID jobId;

  public static final String JSON_PROPERTY_OPERATION = "operation";
  @javax.annotation.Nullable
  private DocumentJobOperation operation;

  public static final String JSON_PROPERTY_STATUS = "status";
  @javax.annotation.Nullable
  private DocumentJobStatus status;

  public static final String JSON_PROPERTY_OUTPUT_REFERENCE = "outputReference";
  private JsonNullable<String> outputReference = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_STAGE = "stage";
  private JsonNullable<String> stage = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_PROCESSED_PAGES = "processedPages";
  private JsonNullable<Integer> processedPages = JsonNullable.<Integer>undefined();

  public static final String JSON_PROPERTY_TOTAL_PAGES = "totalPages";
  private JsonNullable<Integer> totalPages = JsonNullable.<Integer>undefined();

  public static final String JSON_PROPERTY_ATTEMPT_COUNT = "attemptCount";
  @javax.annotation.Nullable
  private Integer attemptCount;

  public static final String JSON_PROPERTY_FAILURE_CODE = "failureCode";
  private JsonNullable<String> failureCode = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_RETRYABLE = "retryable";
  @javax.annotation.Nullable
  private Boolean retryable;

  public static final String JSON_PROPERTY_STARTED_AT = "startedAt";
  private JsonNullable<OffsetDateTime> startedAt = JsonNullable.<OffsetDateTime>undefined();

  public static final String JSON_PROPERTY_COMPLETED_AT = "completedAt";
  private JsonNullable<OffsetDateTime> completedAt = JsonNullable.<OffsetDateTime>undefined();

  public static final String JSON_PROPERTY_CANCELLATION_REQUESTED_AT = "cancellationRequestedAt";
  private JsonNullable<OffsetDateTime> cancellationRequestedAt = JsonNullable.<OffsetDateTime>undefined();

  public static final String JSON_PROPERTY_EXPIRES_AT = "expiresAt";
  @javax.annotation.Nullable
  private OffsetDateTime expiresAt;

  public static final String JSON_PROPERTY_CREDITS_CONSUMED = "creditsConsumed";
  private JsonNullable<BigDecimal> creditsConsumed = JsonNullable.<BigDecimal>undefined();

  public DocumentJob() {
  }

  public DocumentJob jobId(@javax.annotation.Nullable UUID jobId) {
    this.jobId = jobId;
    return this;
  }

  /**
   * Get jobId
   * @return jobId
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_JOB_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public UUID getJobId() {
    return jobId;
  }


  @JsonProperty(value = JSON_PROPERTY_JOB_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setJobId(@javax.annotation.Nullable UUID jobId) {
    this.jobId = jobId;
  }


  public DocumentJob operation(@javax.annotation.Nullable DocumentJobOperation operation) {
    this.operation = operation;
    return this;
  }

  /**
   * Get operation
   * @return operation
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_OPERATION, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public DocumentJobOperation getOperation() {
    return operation;
  }


  @JsonProperty(value = JSON_PROPERTY_OPERATION, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setOperation(@javax.annotation.Nullable DocumentJobOperation operation) {
    this.operation = operation;
  }


  public DocumentJob status(@javax.annotation.Nullable DocumentJobStatus status) {
    this.status = status;
    return this;
  }

  /**
   * Get status
   * @return status
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_STATUS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public DocumentJobStatus getStatus() {
    return status;
  }


  @JsonProperty(value = JSON_PROPERTY_STATUS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setStatus(@javax.annotation.Nullable DocumentJobStatus status) {
    this.status = status;
  }


  public DocumentJob outputReference(@javax.annotation.Nullable String outputReference) {
    this.outputReference = JsonNullable.<String>of(outputReference);
    return this;
  }

  /**
   * Where the finished result is stored, as an &#x60;artifact://&#x60; reference. Read it with &#x60;GET /api/v1/artifacts/content&#x60;. Null until the job succeeds, and always null for &#x60;Redaction&#x60;, which has its own download route.  For &#x60;Extraction&#x60; and &#x60;ZeroShot&#x60; its field entries are the same &#x60;ExtractedField&#x60; objects a synchronous call returns for that document — same source-coordinate convention, same &#x60;0&#x60;-&#x60;100&#x60; confidence scale.  The stored &#x60;result.json&#x60; is not the response envelope and does not repeat its casing: it holds the extraction result directly, with &#x60;Metadata&#x60; where the synchronous body has &#x60;data.metadata&#x60;. The field names inside are your template&#39;s either way.  Jobs that completed before 2026-09-22 carry a bucket-qualified path rather than an &#x60;artifact://&#x60; reference; the download accepts both.
   * @return outputReference
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getOutputReference() {
        return outputReference.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_OUTPUT_REFERENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getOutputReference_JsonNullable() {
    return outputReference;
  }

  @JsonProperty(JSON_PROPERTY_OUTPUT_REFERENCE)
  public void setOutputReference_JsonNullable(JsonNullable<String> outputReference) {
    this.outputReference = outputReference;
  }

  public void setOutputReference(@javax.annotation.Nullable String outputReference) {
    this.outputReference = JsonNullable.<String>of(outputReference);
  }


  public DocumentJob stage(@javax.annotation.Nullable String stage) {
    this.stage = JsonNullable.<String>of(stage);
    return this;
  }

  /**
   * Get stage
   * @return stage
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getStage() {
        return stage.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_STAGE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getStage_JsonNullable() {
    return stage;
  }

  @JsonProperty(JSON_PROPERTY_STAGE)
  public void setStage_JsonNullable(JsonNullable<String> stage) {
    this.stage = stage;
  }

  public void setStage(@javax.annotation.Nullable String stage) {
    this.stage = JsonNullable.<String>of(stage);
  }


  public DocumentJob processedPages(@javax.annotation.Nullable Integer processedPages) {
    this.processedPages = JsonNullable.<Integer>of(processedPages);
    return this;
  }

  /**
   * Get processedPages
   * @return processedPages
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public Integer getProcessedPages() {
        return processedPages.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_PROCESSED_PAGES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<Integer> getProcessedPages_JsonNullable() {
    return processedPages;
  }

  @JsonProperty(JSON_PROPERTY_PROCESSED_PAGES)
  public void setProcessedPages_JsonNullable(JsonNullable<Integer> processedPages) {
    this.processedPages = processedPages;
  }

  public void setProcessedPages(@javax.annotation.Nullable Integer processedPages) {
    this.processedPages = JsonNullable.<Integer>of(processedPages);
  }


  public DocumentJob totalPages(@javax.annotation.Nullable Integer totalPages) {
    this.totalPages = JsonNullable.<Integer>of(totalPages);
    return this;
  }

  /**
   * Get totalPages
   * @return totalPages
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public Integer getTotalPages() {
        return totalPages.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_TOTAL_PAGES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<Integer> getTotalPages_JsonNullable() {
    return totalPages;
  }

  @JsonProperty(JSON_PROPERTY_TOTAL_PAGES)
  public void setTotalPages_JsonNullable(JsonNullable<Integer> totalPages) {
    this.totalPages = totalPages;
  }

  public void setTotalPages(@javax.annotation.Nullable Integer totalPages) {
    this.totalPages = JsonNullable.<Integer>of(totalPages);
  }


  public DocumentJob attemptCount(@javax.annotation.Nullable Integer attemptCount) {
    this.attemptCount = attemptCount;
    return this;
  }

  /**
   * Get attemptCount
   * @return attemptCount
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_ATTEMPT_COUNT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Integer getAttemptCount() {
    return attemptCount;
  }


  @JsonProperty(value = JSON_PROPERTY_ATTEMPT_COUNT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setAttemptCount(@javax.annotation.Nullable Integer attemptCount) {
    this.attemptCount = attemptCount;
  }


  public DocumentJob failureCode(@javax.annotation.Nullable String failureCode) {
    this.failureCode = JsonNullable.<String>of(failureCode);
    return this;
  }

  /**
   * Get failureCode
   * @return failureCode
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getFailureCode() {
        return failureCode.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_FAILURE_CODE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getFailureCode_JsonNullable() {
    return failureCode;
  }

  @JsonProperty(JSON_PROPERTY_FAILURE_CODE)
  public void setFailureCode_JsonNullable(JsonNullable<String> failureCode) {
    this.failureCode = failureCode;
  }

  public void setFailureCode(@javax.annotation.Nullable String failureCode) {
    this.failureCode = JsonNullable.<String>of(failureCode);
  }


  public DocumentJob retryable(@javax.annotation.Nullable Boolean retryable) {
    this.retryable = retryable;
    return this;
  }

  /**
   * Get retryable
   * @return retryable
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_RETRYABLE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Boolean getRetryable() {
    return retryable;
  }


  @JsonProperty(value = JSON_PROPERTY_RETRYABLE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setRetryable(@javax.annotation.Nullable Boolean retryable) {
    this.retryable = retryable;
  }


  public DocumentJob startedAt(@javax.annotation.Nullable OffsetDateTime startedAt) {
    this.startedAt = JsonNullable.<OffsetDateTime>of(startedAt);
    return this;
  }

  /**
   * Get startedAt
   * @return startedAt
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public OffsetDateTime getStartedAt() {
        return startedAt.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_STARTED_AT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<OffsetDateTime> getStartedAt_JsonNullable() {
    return startedAt;
  }

  @JsonProperty(JSON_PROPERTY_STARTED_AT)
  public void setStartedAt_JsonNullable(JsonNullable<OffsetDateTime> startedAt) {
    this.startedAt = startedAt;
  }

  public void setStartedAt(@javax.annotation.Nullable OffsetDateTime startedAt) {
    this.startedAt = JsonNullable.<OffsetDateTime>of(startedAt);
  }


  public DocumentJob completedAt(@javax.annotation.Nullable OffsetDateTime completedAt) {
    this.completedAt = JsonNullable.<OffsetDateTime>of(completedAt);
    return this;
  }

  /**
   * Get completedAt
   * @return completedAt
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public OffsetDateTime getCompletedAt() {
        return completedAt.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_COMPLETED_AT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<OffsetDateTime> getCompletedAt_JsonNullable() {
    return completedAt;
  }

  @JsonProperty(JSON_PROPERTY_COMPLETED_AT)
  public void setCompletedAt_JsonNullable(JsonNullable<OffsetDateTime> completedAt) {
    this.completedAt = completedAt;
  }

  public void setCompletedAt(@javax.annotation.Nullable OffsetDateTime completedAt) {
    this.completedAt = JsonNullable.<OffsetDateTime>of(completedAt);
  }


  public DocumentJob cancellationRequestedAt(@javax.annotation.Nullable OffsetDateTime cancellationRequestedAt) {
    this.cancellationRequestedAt = JsonNullable.<OffsetDateTime>of(cancellationRequestedAt);
    return this;
  }

  /**
   * Get cancellationRequestedAt
   * @return cancellationRequestedAt
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public OffsetDateTime getCancellationRequestedAt() {
        return cancellationRequestedAt.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_CANCELLATION_REQUESTED_AT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<OffsetDateTime> getCancellationRequestedAt_JsonNullable() {
    return cancellationRequestedAt;
  }

  @JsonProperty(JSON_PROPERTY_CANCELLATION_REQUESTED_AT)
  public void setCancellationRequestedAt_JsonNullable(JsonNullable<OffsetDateTime> cancellationRequestedAt) {
    this.cancellationRequestedAt = cancellationRequestedAt;
  }

  public void setCancellationRequestedAt(@javax.annotation.Nullable OffsetDateTime cancellationRequestedAt) {
    this.cancellationRequestedAt = JsonNullable.<OffsetDateTime>of(cancellationRequestedAt);
  }


  public DocumentJob expiresAt(@javax.annotation.Nullable OffsetDateTime expiresAt) {
    this.expiresAt = expiresAt;
    return this;
  }

  /**
   * Get expiresAt
   * @return expiresAt
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_EXPIRES_AT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public OffsetDateTime getExpiresAt() {
    return expiresAt;
  }


  @JsonProperty(value = JSON_PROPERTY_EXPIRES_AT, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setExpiresAt(@javax.annotation.Nullable OffsetDateTime expiresAt) {
    this.expiresAt = expiresAt;
  }


  public DocumentJob creditsConsumed(@javax.annotation.Nullable BigDecimal creditsConsumed) {
    this.creditsConsumed = JsonNullable.<BigDecimal>of(creditsConsumed);
    return this;
  }

  /**
   * What the job consumed, in credits. Absent — never &#x60;0&#x60; — while the cost is unknown: a job still queued or running, an operation that is not metered, or one billing could not price. &#x60;0&#x60; is a real value meaning the job was free. It is a property of the job, so polling a finished job twice reports the same figure; it is not a charge per read.
   * @return creditsConsumed
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public BigDecimal getCreditsConsumed() {
        return creditsConsumed.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_CREDITS_CONSUMED, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<BigDecimal> getCreditsConsumed_JsonNullable() {
    return creditsConsumed;
  }

  @JsonProperty(JSON_PROPERTY_CREDITS_CONSUMED)
  public void setCreditsConsumed_JsonNullable(JsonNullable<BigDecimal> creditsConsumed) {
    this.creditsConsumed = creditsConsumed;
  }

  public void setCreditsConsumed(@javax.annotation.Nullable BigDecimal creditsConsumed) {
    this.creditsConsumed = JsonNullable.<BigDecimal>of(creditsConsumed);
  }


  /**
   * Return true if this DocumentJob object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    DocumentJob documentJob = (DocumentJob) o;
    return Objects.equals(this.jobId, documentJob.jobId) &&
        Objects.equals(this.operation, documentJob.operation) &&
        Objects.equals(this.status, documentJob.status) &&
        equalsNullable(this.outputReference, documentJob.outputReference) &&
        equalsNullable(this.stage, documentJob.stage) &&
        equalsNullable(this.processedPages, documentJob.processedPages) &&
        equalsNullable(this.totalPages, documentJob.totalPages) &&
        Objects.equals(this.attemptCount, documentJob.attemptCount) &&
        equalsNullable(this.failureCode, documentJob.failureCode) &&
        Objects.equals(this.retryable, documentJob.retryable) &&
        equalsNullable(this.startedAt, documentJob.startedAt) &&
        equalsNullable(this.completedAt, documentJob.completedAt) &&
        equalsNullable(this.cancellationRequestedAt, documentJob.cancellationRequestedAt) &&
        Objects.equals(this.expiresAt, documentJob.expiresAt) &&
        equalsNullable(this.creditsConsumed, documentJob.creditsConsumed);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(jobId, operation, status, hashCodeNullable(outputReference), hashCodeNullable(stage), hashCodeNullable(processedPages), hashCodeNullable(totalPages), attemptCount, hashCodeNullable(failureCode), retryable, hashCodeNullable(startedAt), hashCodeNullable(completedAt), hashCodeNullable(cancellationRequestedAt), expiresAt, hashCodeNullable(creditsConsumed));
  }

  private static <T> int hashCodeNullable(JsonNullable<T> a) {
    if (a == null) {
      return 1;
    }
    return a.isPresent() ? Arrays.deepHashCode(new Object[]{a.get()}) : 31;
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class DocumentJob {\n");
    sb.append("    jobId: ").append(toIndentedString(jobId)).append("\n");
    sb.append("    operation: ").append(toIndentedString(operation)).append("\n");
    sb.append("    status: ").append(toIndentedString(status)).append("\n");
    sb.append("    outputReference: ").append(toIndentedString(outputReference)).append("\n");
    sb.append("    stage: ").append(toIndentedString(stage)).append("\n");
    sb.append("    processedPages: ").append(toIndentedString(processedPages)).append("\n");
    sb.append("    totalPages: ").append(toIndentedString(totalPages)).append("\n");
    sb.append("    attemptCount: ").append(toIndentedString(attemptCount)).append("\n");
    sb.append("    failureCode: ").append(toIndentedString(failureCode)).append("\n");
    sb.append("    retryable: ").append(toIndentedString(retryable)).append("\n");
    sb.append("    startedAt: ").append(toIndentedString(startedAt)).append("\n");
    sb.append("    completedAt: ").append(toIndentedString(completedAt)).append("\n");
    sb.append("    cancellationRequestedAt: ").append(toIndentedString(cancellationRequestedAt)).append("\n");
    sb.append("    expiresAt: ").append(toIndentedString(expiresAt)).append("\n");
    sb.append("    creditsConsumed: ").append(toIndentedString(creditsConsumed)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(Object o) {
    return o == null ? "null" : o.toString().replace("\n", "\n    ");
  }

  /**
   * Convert the instance into URL query string.
   *
   * @return URL query string
   */
  public String toUrlQueryString() {
    return toUrlQueryString(null);
  }

  /**
   * Convert the instance into URL query string.
   *
   * @param prefix prefix of the query string
   * @return URL query string
   */
  public String toUrlQueryString(String prefix) {
    String suffix = "";
    String containerSuffix = "";
    String containerPrefix = "";
    if (prefix == null) {
      // style=form, explode=true, e.g. /pet?name=cat&type=manx
      prefix = "";
    } else {
      // deepObject style e.g. /pet?id[name]=cat&id[type]=manx
      prefix = prefix + "[";
      suffix = "]";
      containerSuffix = "]";
      containerPrefix = "[";
    }

    StringJoiner joiner = new StringJoiner("&");

    // add `jobId` to the URL query string
    if (getJobId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sjobId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getJobId()))));
    }

    // add `operation` to the URL query string
    if (getOperation() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%soperation%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getOperation()))));
    }

    // add `status` to the URL query string
    if (getStatus() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sstatus%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getStatus()))));
    }

    // add `outputReference` to the URL query string
    if (getOutputReference() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%soutputReference%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getOutputReference()))));
    }

    // add `stage` to the URL query string
    if (getStage() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sstage%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getStage()))));
    }

    // add `processedPages` to the URL query string
    if (getProcessedPages() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sprocessedPages%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getProcessedPages()))));
    }

    // add `totalPages` to the URL query string
    if (getTotalPages() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%stotalPages%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getTotalPages()))));
    }

    // add `attemptCount` to the URL query string
    if (getAttemptCount() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sattemptCount%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getAttemptCount()))));
    }

    // add `failureCode` to the URL query string
    if (getFailureCode() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sfailureCode%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFailureCode()))));
    }

    // add `retryable` to the URL query string
    if (getRetryable() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sretryable%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getRetryable()))));
    }

    // add `startedAt` to the URL query string
    if (getStartedAt() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sstartedAt%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getStartedAt()))));
    }

    // add `completedAt` to the URL query string
    if (getCompletedAt() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%scompletedAt%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getCompletedAt()))));
    }

    // add `cancellationRequestedAt` to the URL query string
    if (getCancellationRequestedAt() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%scancellationRequestedAt%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getCancellationRequestedAt()))));
    }

    // add `expiresAt` to the URL query string
    if (getExpiresAt() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sexpiresAt%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getExpiresAt()))));
    }

    // add `creditsConsumed` to the URL query string
    if (getCreditsConsumed() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%screditsConsumed%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getCreditsConsumed()))));
    }

    return joiner.toString();
  }
}
