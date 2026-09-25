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
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * One extracted field: the value, how certain the model is of it, and where on the document it was read from. These are the objects that fill &#x60;data.metadata&#x60;, and the cells inside a table-shaped field&#39;s &#x60;items&#x60; rows.  The three location keys are present or absent together — see &#x60;data.metadata&#x60; for the coordinate convention they follow.
 */
@JsonPropertyOrder({
  ExtractedField.JSON_PROPERTY_VALUE,
  ExtractedField.JSON_PROPERTY_CONFIDENCE,
  ExtractedField.JSON_PROPERTY_PAGE,
  ExtractedField.JSON_PROPERTY_BBOX,
  ExtractedField.JSON_PROPERTY_BBOX_CONFIDENCE
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class ExtractedField {
  public static final String JSON_PROPERTY_VALUE = "value";
  private JsonNullable<String> value = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_CONFIDENCE = "confidence";
  @javax.annotation.Nullable
  private BigDecimal confidence;

  public static final String JSON_PROPERTY_PAGE = "page";
  @javax.annotation.Nullable
  private Integer page;

  public static final String JSON_PROPERTY_BBOX = "bbox";
  @javax.annotation.Nullable
  private List<BigDecimal> bbox = new ArrayList<>();

  public static final String JSON_PROPERTY_BBOX_CONFIDENCE = "bbox_confidence";
  @javax.annotation.Nullable
  private BigDecimal bboxConfidence;

  public ExtractedField() {
  }

  public ExtractedField value(@javax.annotation.Nullable String value) {
    this.value = JsonNullable.<String>of(value);
    return this;
  }

  /**
   * The extracted value, or &#x60;null&#x60; when the field was not found.
   * @return value
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getValue() {
        return value.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_VALUE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getValue_JsonNullable() {
    return value;
  }

  @JsonProperty(JSON_PROPERTY_VALUE)
  public void setValue_JsonNullable(JsonNullable<String> value) {
    this.value = value;
  }

  public void setValue(@javax.annotation.Nullable String value) {
    this.value = JsonNullable.<String>of(value);
  }


  public ExtractedField confidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = confidence;
    return this;
  }

  /**
   * Certainty in the value, from &#x60;0&#x60; to &#x60;100&#x60;. This is the one confidence scale the API uses; &#x60;bbox_confidence&#x60; is on the same one.
   * minimum: 0
   * maximum: 100
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


  public ExtractedField page(@javax.annotation.Nullable Integer page) {
    this.page = page;
    return this;
  }

  /**
   * 1-indexed page the value was read from. Absent when the value could not be located on the page.
   * minimum: 1
   * @return page
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_PAGE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Integer getPage() {
    return page;
  }


  @JsonProperty(value = JSON_PROPERTY_PAGE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setPage(@javax.annotation.Nullable Integer page) {
    this.page = page;
  }


  public ExtractedField bbox(@javax.annotation.Nullable List<BigDecimal> bbox) {
    this.bbox = bbox;
    return this;
  }

  public ExtractedField addBboxItem(BigDecimal bboxItem) {
    if (this.bbox == null) {
      this.bbox = new ArrayList<>();
    }
    this.bbox.add(bboxItem);
    return this;
  }

  /**
   * Where a value sits on its page, as &#x60;[x0, y0, x1, y1]&#x60; fractions of the page size with the origin at the top-left: &#x60;x0,y0&#x60; is the top-left corner and &#x60;x1,y1&#x60; the bottom-right. Fractions rather than pixels, so the box survives any rendering scale — multiply by the width and height you draw the page at.
   * @return bbox
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_BBOX, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<BigDecimal> getBbox() {
    return bbox;
  }


  @JsonProperty(value = JSON_PROPERTY_BBOX, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setBbox(@javax.annotation.Nullable List<BigDecimal> bbox) {
    this.bbox = bbox;
  }


  public ExtractedField bboxConfidence(@javax.annotation.Nullable BigDecimal bboxConfidence) {
    this.bboxConfidence = bboxConfidence;
    return this;
  }

  /**
   * Certainty in the location, from &#x60;0&#x60; to &#x60;100&#x60; — the same scale as &#x60;confidence&#x60;, not a &#x60;0&#x60;–&#x60;1&#x60; fraction. Absent whenever &#x60;bbox&#x60; is.
   * minimum: 0
   * maximum: 100
   * @return bboxConfidence
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_BBOX_CONFIDENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public BigDecimal getBboxConfidence() {
    return bboxConfidence;
  }


  @JsonProperty(value = JSON_PROPERTY_BBOX_CONFIDENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setBboxConfidence(@javax.annotation.Nullable BigDecimal bboxConfidence) {
    this.bboxConfidence = bboxConfidence;
  }


  /**
   * Return true if this ExtractedField object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    ExtractedField extractedField = (ExtractedField) o;
    return equalsNullable(this.value, extractedField.value) &&
        Objects.equals(this.confidence, extractedField.confidence) &&
        Objects.equals(this.page, extractedField.page) &&
        Objects.equals(this.bbox, extractedField.bbox) &&
        Objects.equals(this.bboxConfidence, extractedField.bboxConfidence);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(hashCodeNullable(value), confidence, page, bbox, bboxConfidence);
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
    sb.append("class ExtractedField {\n");
    sb.append("    value: ").append(toIndentedString(value)).append("\n");
    sb.append("    confidence: ").append(toIndentedString(confidence)).append("\n");
    sb.append("    page: ").append(toIndentedString(page)).append("\n");
    sb.append("    bbox: ").append(toIndentedString(bbox)).append("\n");
    sb.append("    bboxConfidence: ").append(toIndentedString(bboxConfidence)).append("\n");
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

    // add `value` to the URL query string
    if (getValue() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%svalue%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getValue()))));
    }

    // add `confidence` to the URL query string
    if (getConfidence() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sconfidence%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getConfidence()))));
    }

    // add `page` to the URL query string
    if (getPage() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%spage%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getPage()))));
    }

    // add `bbox` to the URL query string
    if (getBbox() != null) {
      for (int i = 0; i < getBbox().size(); i++) {
        if (getBbox().get(i) != null) {
          joiner.add(String.format(java.util.Locale.ROOT, "%sbbox%s%s=%s", prefix, suffix,
              "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
              ApiClient.urlEncode(ApiClient.valueToString(getBbox().get(i)))));
        }
      }
    }

    // add `bbox_confidence` to the URL query string
    if (getBboxConfidence() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sbbox_confidence%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getBboxConfidence()))));
    }

    return joiner.toString();
  }
}
