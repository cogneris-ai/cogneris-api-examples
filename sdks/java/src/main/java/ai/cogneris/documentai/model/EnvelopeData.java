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


package ai.cogneris.documentai.model;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.StringJoiner;
import java.util.Objects;
import java.util.Map;
import java.util.HashMap;
import ai.cogneris.documentai.model.ClassificationResult;
import ai.cogneris.documentai.model.CropDocument;
import ai.cogneris.documentai.model.FaceExtraction;
import ai.cogneris.documentai.model.FaceMatch;
import ai.cogneris.documentai.model.QualityAssessment;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * EnvelopeData
 */
@JsonPropertyOrder({
  EnvelopeData.JSON_PROPERTY_ID,
  EnvelopeData.JSON_PROPERTY_METADATA,
  EnvelopeData.JSON_PROPERTY_CREATED_DATE,
  EnvelopeData.JSON_PROPERTY_RESULTS,
  EnvelopeData.JSON_PROPERTY_DOCUMENT_TYPE,
  EnvelopeData.JSON_PROPERTY_CONFIDENCE,
  EnvelopeData.JSON_PROPERTY_FRAUD_BLOCKED,
  EnvelopeData.JSON_PROPERTY_FRAUD_REQUEST_ID,
  EnvelopeData.JSON_PROPERTY_QUALITY,
  EnvelopeData.JSON_PROPERTY_IMAGE_URLS,
  EnvelopeData.JSON_PROPERTY_DOCUMENTS,
  EnvelopeData.JSON_PROPERTY_COMPOSITE_IMAGE_URL,
  EnvelopeData.JSON_PROPERTY_REQUEST_ID,
  EnvelopeData.JSON_PROPERTY_EXTRACTIONS,
  EnvelopeData.JSON_PROPERTY_MATCHES
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class EnvelopeData {
  public static final String JSON_PROPERTY_ID = "id";
  @javax.annotation.Nullable
  private UUID id;

  public static final String JSON_PROPERTY_METADATA = "metadata";
  @javax.annotation.Nullable
  private Map<String, Object> metadata = new HashMap<>();

  public static final String JSON_PROPERTY_CREATED_DATE = "createdDate";
  @javax.annotation.Nullable
  private OffsetDateTime createdDate;

  public static final String JSON_PROPERTY_RESULTS = "results";
  @javax.annotation.Nullable
  private List<ClassificationResult> results = new ArrayList<>();

  public static final String JSON_PROPERTY_DOCUMENT_TYPE = "documentType";
  @javax.annotation.Nullable
  private String documentType;

  public static final String JSON_PROPERTY_CONFIDENCE = "confidence";
  @javax.annotation.Nullable
  private BigDecimal confidence;

  public static final String JSON_PROPERTY_FRAUD_BLOCKED = "fraudBlocked";
  @javax.annotation.Nullable
  private Boolean fraudBlocked;

  public static final String JSON_PROPERTY_FRAUD_REQUEST_ID = "fraudRequestId";
  private JsonNullable<UUID> fraudRequestId = JsonNullable.<UUID>undefined();

  public static final String JSON_PROPERTY_QUALITY = "quality";
  private JsonNullable<QualityAssessment> quality = JsonNullable.<QualityAssessment>undefined();

  public static final String JSON_PROPERTY_IMAGE_URLS = "imageUrls";
  private JsonNullable<List<String>> imageUrls = JsonNullable.<List<String>>undefined();

  public static final String JSON_PROPERTY_DOCUMENTS = "documents";
  @javax.annotation.Nullable
  private List<CropDocument> documents = new ArrayList<>();

  public static final String JSON_PROPERTY_COMPOSITE_IMAGE_URL = "compositeImageUrl";
  private JsonNullable<String> compositeImageUrl = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_REQUEST_ID = "requestId";
  @javax.annotation.Nullable
  private UUID requestId;

  public static final String JSON_PROPERTY_EXTRACTIONS = "extractions";
  @javax.annotation.Nullable
  private List<FaceExtraction> extractions = new ArrayList<>();

  public static final String JSON_PROPERTY_MATCHES = "matches";
  @javax.annotation.Nullable
  private List<FaceMatch> matches = new ArrayList<>();

  public EnvelopeData() {
  }

  public EnvelopeData id(@javax.annotation.Nullable UUID id) {
    this.id = id;
    return this;
  }

  /**
   * Get id
   * @return id
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public UUID getId() {
    return id;
  }


  @JsonProperty(value = JSON_PROPERTY_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setId(@javax.annotation.Nullable UUID id) {
    this.id = id;
  }


  public EnvelopeData metadata(@javax.annotation.Nullable Map<String, Object> metadata) {
    this.metadata = metadata;
    return this;
  }

  public EnvelopeData putMetadataItem(String key, Object metadataItem) {
    if (this.metadata == null) {
      this.metadata = new HashMap<>();
    }
    this.metadata.put(key, metadataItem);
    return this;
  }

  /**
   * Operation-specific payload, shaped by the template or operation that ran. The keys are your template&#39;s, so the object itself is left open here.  Extraction and zero-shot fill it with one entry per extracted field, and each entry is an &#x60;ExtractedField&#x60;: the value, how certain the model is of it, and — when the value was visually located on the page — where it was read from. A table-shaped field carries an &#x60;items&#x60; array instead, whose rows hold &#x60;ExtractedField&#x60; cells under the same keys.  Source coordinates follow one convention, the same on every engine:  - &#x60;page&#x60; is 1-indexed, and never past the document&#39;s last page. - &#x60;bbox&#x60; is &#x60;[x0, y0, x1, y1]&#x60; as fractions of the page size with the   origin at the top-left, so &#x60;x0,y0&#x60; is the top-left corner and &#x60;x1,y1&#x60;   the bottom-right. Values are clamped into &#x60;0&#x60;–&#x60;1&#x60; and the corners are   ordered, so &#x60;x0 &lt;&#x3D; x1&#x60; and &#x60;y0 &lt;&#x3D; y1&#x60; always hold. - &#x60;page&#x60;, &#x60;bbox&#x60; and &#x60;bbox_confidence&#x60; are omitted **together** for any   value the model could not locate on the page — a computed total, for   instance. Their absence is not an error, and a field object carrying   none of the three is ordinary.  Every confidence this API returns is a number from &#x60;0&#x60; to &#x60;100&#x60;, &#x60;bbox_confidence&#x60; included. There is no second scale to convert from.  A document job&#39;s stored &#x60;result.json&#x60; holds the same field entries, sanitized the same way, so the asynchronous answer agrees with the synchronous one for the same document. It wraps them differently — see &#x60;outputReference&#x60;.
   * @return metadata
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_METADATA, required = false)
  @JsonInclude(content = JsonInclude.Include.ALWAYS, value = JsonInclude.Include.USE_DEFAULTS)
  public Map<String, Object> getMetadata() {
    return metadata;
  }


  @JsonProperty(value = JSON_PROPERTY_METADATA, required = false)
  @JsonInclude(content = JsonInclude.Include.ALWAYS, value = JsonInclude.Include.USE_DEFAULTS)
  public void setMetadata(@javax.annotation.Nullable Map<String, Object> metadata) {
    this.metadata = metadata;
  }


  public EnvelopeData createdDate(@javax.annotation.Nullable OffsetDateTime createdDate) {
    this.createdDate = createdDate;
    return this;
  }

  /**
   * Get createdDate
   * @return createdDate
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_CREATED_DATE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public OffsetDateTime getCreatedDate() {
    return createdDate;
  }


  @JsonProperty(value = JSON_PROPERTY_CREATED_DATE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setCreatedDate(@javax.annotation.Nullable OffsetDateTime createdDate) {
    this.createdDate = createdDate;
  }


  public EnvelopeData results(@javax.annotation.Nullable List<ClassificationResult> results) {
    this.results = results;
    return this;
  }

  public EnvelopeData addResultsItem(ClassificationResult resultsItem) {
    if (this.results == null) {
      this.results = new ArrayList<>();
    }
    this.results.add(resultsItem);
    return this;
  }

  /**
   * &#x60;/Document/classifier&#x60; only: one entry per uploaded file.
   * @return results
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_RESULTS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<ClassificationResult> getResults() {
    return results;
  }


  @JsonProperty(value = JSON_PROPERTY_RESULTS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setResults(@javax.annotation.Nullable List<ClassificationResult> results) {
    this.results = results;
  }


  public EnvelopeData documentType(@javax.annotation.Nullable String documentType) {
    this.documentType = documentType;
    return this;
  }

  /**
   * &#x60;/Document/zero-shot&#x60; only: the document type the model recognized.
   * @return documentType
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_DOCUMENT_TYPE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getDocumentType() {
    return documentType;
  }


  @JsonProperty(value = JSON_PROPERTY_DOCUMENT_TYPE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setDocumentType(@javax.annotation.Nullable String documentType) {
    this.documentType = documentType;
  }


  public EnvelopeData confidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = confidence;
    return this;
  }

  /**
   * &#x60;/Document/zero-shot&#x60; only: certainty in &#x60;documentType&#x60;.
   * @return confidence
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_CONFIDENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public BigDecimal getConfidence() {
    return confidence;
  }


  @JsonProperty(value = JSON_PROPERTY_CONFIDENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setConfidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = confidence;
  }


  public EnvelopeData fraudBlocked(@javax.annotation.Nullable Boolean fraudBlocked) {
    this.fraudBlocked = fraudBlocked;
    return this;
  }

  /**
   * &#x60;/Document/extraction&#x60; only. Always &#x60;false&#x60;: fraud screening is advisory and never withholds the extraction. Kept for clients that already read it.
   * @return fraudBlocked
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_FRAUD_BLOCKED, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Boolean getFraudBlocked() {
    return fraudBlocked;
  }


  @JsonProperty(value = JSON_PROPERTY_FRAUD_BLOCKED, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setFraudBlocked(@javax.annotation.Nullable Boolean fraudBlocked) {
    this.fraudBlocked = fraudBlocked;
  }


  public EnvelopeData fraudRequestId(@javax.annotation.Nullable UUID fraudRequestId) {
    this.fraudRequestId = JsonNullable.<UUID>of(fraudRequestId);
    return this;
  }

  /**
   * &#x60;/Document/extraction&#x60; only: the fraud screening that ran on this document. Null when screening was disabled, not enabled for the tenant, or failed.
   * @return fraudRequestId
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public UUID getFraudRequestId() {
        return fraudRequestId.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_FRAUD_REQUEST_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<UUID> getFraudRequestId_JsonNullable() {
    return fraudRequestId;
  }

  @JsonProperty(JSON_PROPERTY_FRAUD_REQUEST_ID)
  public void setFraudRequestId_JsonNullable(JsonNullable<UUID> fraudRequestId) {
    this.fraudRequestId = fraudRequestId;
  }

  public void setFraudRequestId(@javax.annotation.Nullable UUID fraudRequestId) {
    this.fraudRequestId = JsonNullable.<UUID>of(fraudRequestId);
  }


  public EnvelopeData quality(@javax.annotation.Nullable QualityAssessment quality) {
    this.quality = JsonNullable.<QualityAssessment>of(quality);
    return this;
  }

  /**
   * &#x60;/Document/extraction&#x60; only: the input-quality pre-flight. Null when it did not run. On a &#x60;2&#x60; (block) verdict the extraction did not run and &#x60;metadata&#x60; is null; on a &#x60;1&#x60; (warn) it ran and this carries the findings.
   * @return quality
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public QualityAssessment getQuality() {
        return quality.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_QUALITY, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<QualityAssessment> getQuality_JsonNullable() {
    return quality;
  }

  @JsonProperty(JSON_PROPERTY_QUALITY)
  public void setQuality_JsonNullable(JsonNullable<QualityAssessment> quality) {
    this.quality = quality;
  }

  public void setQuality(@javax.annotation.Nullable QualityAssessment quality) {
    this.quality = JsonNullable.<QualityAssessment>of(quality);
  }


  public EnvelopeData imageUrls(@javax.annotation.Nullable List<String> imageUrls) {
    this.imageUrls = JsonNullable.<List<String>>of(imageUrls);
    return this;
  }

  public EnvelopeData addImageUrlsItem(String imageUrlsItem) {
    if (this.imageUrls == null || !this.imageUrls.isPresent() || this.imageUrls.get() == null) {
      this.imageUrls = JsonNullable.<List<String>>of(new ArrayList<>());
    }
    try {
      this.imageUrls.get().add(imageUrlsItem);
    } catch (java.util.NoSuchElementException e) {
      // this can never happen, as we make sure above that the value is present
    }
    return this;
  }

  /**
   * &#x60;/Document/crop&#x60; only: signed URLs of the cropped images.
   * @return imageUrls
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public List<String> getImageUrls() {
        return imageUrls.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_IMAGE_URLS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<List<String>> getImageUrls_JsonNullable() {
    return imageUrls;
  }

  @JsonProperty(JSON_PROPERTY_IMAGE_URLS)
  public void setImageUrls_JsonNullable(JsonNullable<List<String>> imageUrls) {
    this.imageUrls = imageUrls;
  }

  public void setImageUrls(@javax.annotation.Nullable List<String> imageUrls) {
    this.imageUrls = JsonNullable.<List<String>>of(imageUrls);
  }


  public EnvelopeData documents(@javax.annotation.Nullable List<CropDocument> documents) {
    this.documents = documents;
    return this;
  }

  public EnvelopeData addDocumentsItem(CropDocument documentsItem) {
    if (this.documents == null) {
      this.documents = new ArrayList<>();
    }
    this.documents.add(documentsItem);
    return this;
  }

  /**
   * &#x60;/Document/crop&#x60; only: each document found on the page, with where it sits.
   * @return documents
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_DOCUMENTS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<CropDocument> getDocuments() {
    return documents;
  }


  @JsonProperty(value = JSON_PROPERTY_DOCUMENTS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setDocuments(@javax.annotation.Nullable List<CropDocument> documents) {
    this.documents = documents;
  }


  public EnvelopeData compositeImageUrl(@javax.annotation.Nullable String compositeImageUrl) {
    this.compositeImageUrl = JsonNullable.<String>of(compositeImageUrl);
    return this;
  }

  /**
   * &#x60;/Document/crop&#x60; only: signed URL of the composite image, when one was produced.
   * @return compositeImageUrl
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getCompositeImageUrl() {
        return compositeImageUrl.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_COMPOSITE_IMAGE_URL, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getCompositeImageUrl_JsonNullable() {
    return compositeImageUrl;
  }

  @JsonProperty(JSON_PROPERTY_COMPOSITE_IMAGE_URL)
  public void setCompositeImageUrl_JsonNullable(JsonNullable<String> compositeImageUrl) {
    this.compositeImageUrl = compositeImageUrl;
  }

  public void setCompositeImageUrl(@javax.annotation.Nullable String compositeImageUrl) {
    this.compositeImageUrl = JsonNullable.<String>of(compositeImageUrl);
  }


  public EnvelopeData requestId(@javax.annotation.Nullable UUID requestId) {
    this.requestId = requestId;
    return this;
  }

  /**
   * &#x60;/Document/facematch&#x60; only: identifies this comparison. Facematch carries no &#x60;id&#x60;.
   * @return requestId
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_REQUEST_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public UUID getRequestId() {
    return requestId;
  }


  @JsonProperty(value = JSON_PROPERTY_REQUEST_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setRequestId(@javax.annotation.Nullable UUID requestId) {
    this.requestId = requestId;
  }


  public EnvelopeData extractions(@javax.annotation.Nullable List<FaceExtraction> extractions) {
    this.extractions = extractions;
    return this;
  }

  public EnvelopeData addExtractionsItem(FaceExtraction extractionsItem) {
    if (this.extractions == null) {
      this.extractions = new ArrayList<>();
    }
    this.extractions.add(extractionsItem);
    return this;
  }

  /**
   * &#x60;/Document/facematch&#x60; only: the face found, or not, in each uploaded document.
   * @return extractions
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_EXTRACTIONS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<FaceExtraction> getExtractions() {
    return extractions;
  }


  @JsonProperty(value = JSON_PROPERTY_EXTRACTIONS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setExtractions(@javax.annotation.Nullable List<FaceExtraction> extractions) {
    this.extractions = extractions;
  }


  public EnvelopeData matches(@javax.annotation.Nullable List<FaceMatch> matches) {
    this.matches = matches;
    return this;
  }

  public EnvelopeData addMatchesItem(FaceMatch matchesItem) {
    if (this.matches == null) {
      this.matches = new ArrayList<>();
    }
    this.matches.add(matchesItem);
    return this;
  }

  /**
   * &#x60;/Document/facematch&#x60; only: the selfie compared against each document face.
   * @return matches
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_MATCHES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<FaceMatch> getMatches() {
    return matches;
  }


  @JsonProperty(value = JSON_PROPERTY_MATCHES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setMatches(@javax.annotation.Nullable List<FaceMatch> matches) {
    this.matches = matches;
  }


  /**
   * Return true if this Envelope_data object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    EnvelopeData envelopeData = (EnvelopeData) o;
    return Objects.equals(this.id, envelopeData.id) &&
        Objects.equals(this.metadata, envelopeData.metadata) &&
        Objects.equals(this.createdDate, envelopeData.createdDate) &&
        Objects.equals(this.results, envelopeData.results) &&
        Objects.equals(this.documentType, envelopeData.documentType) &&
        Objects.equals(this.confidence, envelopeData.confidence) &&
        Objects.equals(this.fraudBlocked, envelopeData.fraudBlocked) &&
        equalsNullable(this.fraudRequestId, envelopeData.fraudRequestId) &&
        equalsNullable(this.quality, envelopeData.quality) &&
        equalsNullable(this.imageUrls, envelopeData.imageUrls) &&
        Objects.equals(this.documents, envelopeData.documents) &&
        equalsNullable(this.compositeImageUrl, envelopeData.compositeImageUrl) &&
        Objects.equals(this.requestId, envelopeData.requestId) &&
        Objects.equals(this.extractions, envelopeData.extractions) &&
        Objects.equals(this.matches, envelopeData.matches);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, metadata, createdDate, results, documentType, confidence, fraudBlocked, hashCodeNullable(fraudRequestId), hashCodeNullable(quality), hashCodeNullable(imageUrls), documents, hashCodeNullable(compositeImageUrl), requestId, extractions, matches);
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
    sb.append("class EnvelopeData {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    metadata: ").append(toIndentedString(metadata)).append("\n");
    sb.append("    createdDate: ").append(toIndentedString(createdDate)).append("\n");
    sb.append("    results: ").append(toIndentedString(results)).append("\n");
    sb.append("    documentType: ").append(toIndentedString(documentType)).append("\n");
    sb.append("    confidence: ").append(toIndentedString(confidence)).append("\n");
    sb.append("    fraudBlocked: ").append(toIndentedString(fraudBlocked)).append("\n");
    sb.append("    fraudRequestId: ").append(toIndentedString(fraudRequestId)).append("\n");
    sb.append("    quality: ").append(toIndentedString(quality)).append("\n");
    sb.append("    imageUrls: ").append(toIndentedString(imageUrls)).append("\n");
    sb.append("    documents: ").append(toIndentedString(documents)).append("\n");
    sb.append("    compositeImageUrl: ").append(toIndentedString(compositeImageUrl)).append("\n");
    sb.append("    requestId: ").append(toIndentedString(requestId)).append("\n");
    sb.append("    extractions: ").append(toIndentedString(extractions)).append("\n");
    sb.append("    matches: ").append(toIndentedString(matches)).append("\n");
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

    // add `id` to the URL query string
    if (getId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sid%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getId()))));
    }

    // add `metadata` to the URL query string
    if (getMetadata() != null) {
      for (String _key : getMetadata().keySet()) {
        joiner.add(String.format(java.util.Locale.ROOT, "%smetadata%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, _key, containerSuffix),
            getMetadata().get(_key), ApiClient.urlEncode(ApiClient.valueToString(getMetadata().get(_key)))));
      }
    }

    // add `createdDate` to the URL query string
    if (getCreatedDate() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%screatedDate%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getCreatedDate()))));
    }

    // add `results` to the URL query string
    if (getResults() != null) {
      for (int i = 0; i < getResults().size(); i++) {
        if (getResults().get(i) != null) {
          joiner.add(getResults().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%sresults%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    // add `documentType` to the URL query string
    if (getDocumentType() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sdocumentType%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getDocumentType()))));
    }

    // add `confidence` to the URL query string
    if (getConfidence() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sconfidence%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getConfidence()))));
    }

    // add `fraudBlocked` to the URL query string
    if (getFraudBlocked() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sfraudBlocked%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFraudBlocked()))));
    }

    // add `fraudRequestId` to the URL query string
    if (getFraudRequestId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sfraudRequestId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFraudRequestId()))));
    }

    // add `quality` to the URL query string
    if (getQuality() != null) {
      joiner.add(getQuality().toUrlQueryString(prefix + "quality" + suffix));
    }

    // add `imageUrls` to the URL query string
    if (getImageUrls() != null) {
      for (int i = 0; i < getImageUrls().size(); i++) {
        joiner.add(String.format(java.util.Locale.ROOT, "%simageUrls%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
            ApiClient.urlEncode(ApiClient.valueToString(getImageUrls().get(i)))));
      }
    }

    // add `documents` to the URL query string
    if (getDocuments() != null) {
      for (int i = 0; i < getDocuments().size(); i++) {
        if (getDocuments().get(i) != null) {
          joiner.add(getDocuments().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%sdocuments%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    // add `compositeImageUrl` to the URL query string
    if (getCompositeImageUrl() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%scompositeImageUrl%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getCompositeImageUrl()))));
    }

    // add `requestId` to the URL query string
    if (getRequestId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%srequestId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getRequestId()))));
    }

    // add `extractions` to the URL query string
    if (getExtractions() != null) {
      for (int i = 0; i < getExtractions().size(); i++) {
        if (getExtractions().get(i) != null) {
          joiner.add(getExtractions().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%sextractions%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    // add `matches` to the URL query string
    if (getMatches() != null) {
      for (int i = 0; i < getMatches().size(); i++) {
        if (getMatches().get(i) != null) {
          joiner.add(getMatches().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%smatches%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    return joiner.toString();
  }
}
