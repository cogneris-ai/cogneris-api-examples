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
 * CropDocument
 */
@JsonPropertyOrder({
  CropDocument.JSON_PROPERTY_BOX2_D,
  CropDocument.JSON_PROPERTY_MASK,
  CropDocument.JSON_PROPERTY_SIDE,
  CropDocument.JSON_PROPERTY_TYPE,
  CropDocument.JSON_PROPERTY_CONFIDENCE,
  CropDocument.JSON_PROPERTY_IMAGE_URL
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class CropDocument {
  public static final String JSON_PROPERTY_BOX2_D = "box2D";
  @javax.annotation.Nullable
  private List<Integer> box2D = new ArrayList<>();

  public static final String JSON_PROPERTY_MASK = "mask";
  @javax.annotation.Nullable
  private List<List<Integer>> mask = new ArrayList<>();

  public static final String JSON_PROPERTY_SIDE = "side";
  @javax.annotation.Nullable
  private String side;

  public static final String JSON_PROPERTY_TYPE = "type";
  @javax.annotation.Nullable
  private String type;

  public static final String JSON_PROPERTY_CONFIDENCE = "confidence";
  private JsonNullable<BigDecimal> confidence = JsonNullable.<BigDecimal>undefined();

  public static final String JSON_PROPERTY_IMAGE_URL = "imageUrl";
  @javax.annotation.Nullable
  private String imageUrl;

  public CropDocument() {
  }

  public CropDocument box2D(@javax.annotation.Nullable List<Integer> box2D) {
    this.box2D = box2D;
    return this;
  }

  public CropDocument addBox2DItem(Integer box2DItem) {
    if (this.box2D == null) {
      this.box2D = new ArrayList<>();
    }
    this.box2D.add(box2DItem);
    return this;
  }

  /**
   * Where the document sits on the source image.
   * @return box2D
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_BOX2_D, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<Integer> getBox2D() {
    return box2D;
  }


  @JsonProperty(value = JSON_PROPERTY_BOX2_D, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setBox2D(@javax.annotation.Nullable List<Integer> box2D) {
    this.box2D = box2D;
  }


  public CropDocument mask(@javax.annotation.Nullable List<List<Integer>> mask) {
    this.mask = mask;
    return this;
  }

  public CropDocument addMaskItem(List<Integer> maskItem) {
    if (this.mask == null) {
      this.mask = new ArrayList<>();
    }
    this.mask.add(maskItem);
    return this;
  }

  /**
   * The document&#39;s outline on the source image, as a list of points.
   * @return mask
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_MASK, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public List<List<Integer>> getMask() {
    return mask;
  }


  @JsonProperty(value = JSON_PROPERTY_MASK, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setMask(@javax.annotation.Nullable List<List<Integer>> mask) {
    this.mask = mask;
  }


  public CropDocument side(@javax.annotation.Nullable String side) {
    this.side = side;
    return this;
  }

  /**
   * Get side
   * @return side
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_SIDE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getSide() {
    return side;
  }


  @JsonProperty(value = JSON_PROPERTY_SIDE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setSide(@javax.annotation.Nullable String side) {
    this.side = side;
  }


  public CropDocument type(@javax.annotation.Nullable String type) {
    this.type = type;
    return this;
  }

  /**
   * The detected document type.
   * @return type
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_TYPE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getType() {
    return type;
  }


  @JsonProperty(value = JSON_PROPERTY_TYPE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setType(@javax.annotation.Nullable String type) {
    this.type = type;
  }


  public CropDocument confidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = JsonNullable.<BigDecimal>of(confidence);
    return this;
  }

  /**
   * Get confidence
   * @return confidence
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public BigDecimal getConfidence() {
        return confidence.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_CONFIDENCE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<BigDecimal> getConfidence_JsonNullable() {
    return confidence;
  }

  @JsonProperty(JSON_PROPERTY_CONFIDENCE)
  public void setConfidence_JsonNullable(JsonNullable<BigDecimal> confidence) {
    this.confidence = confidence;
  }

  public void setConfidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = JsonNullable.<BigDecimal>of(confidence);
  }


  public CropDocument imageUrl(@javax.annotation.Nullable String imageUrl) {
    this.imageUrl = imageUrl;
    return this;
  }

  /**
   * Signed URL of this document&#39;s crop.
   * @return imageUrl
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_IMAGE_URL, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getImageUrl() {
    return imageUrl;
  }


  @JsonProperty(value = JSON_PROPERTY_IMAGE_URL, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setImageUrl(@javax.annotation.Nullable String imageUrl) {
    this.imageUrl = imageUrl;
  }


  /**
   * Return true if this CropDocument object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    CropDocument cropDocument = (CropDocument) o;
    return Objects.equals(this.box2D, cropDocument.box2D) &&
        Objects.equals(this.mask, cropDocument.mask) &&
        Objects.equals(this.side, cropDocument.side) &&
        Objects.equals(this.type, cropDocument.type) &&
        equalsNullable(this.confidence, cropDocument.confidence) &&
        Objects.equals(this.imageUrl, cropDocument.imageUrl);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(box2D, mask, side, type, hashCodeNullable(confidence), imageUrl);
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
    sb.append("class CropDocument {\n");
    sb.append("    box2D: ").append(toIndentedString(box2D)).append("\n");
    sb.append("    mask: ").append(toIndentedString(mask)).append("\n");
    sb.append("    side: ").append(toIndentedString(side)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    confidence: ").append(toIndentedString(confidence)).append("\n");
    sb.append("    imageUrl: ").append(toIndentedString(imageUrl)).append("\n");
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

    // add `box2D` to the URL query string
    if (getBox2D() != null) {
      for (int i = 0; i < getBox2D().size(); i++) {
        joiner.add(String.format(java.util.Locale.ROOT, "%sbox2D%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
            ApiClient.urlEncode(ApiClient.valueToString(getBox2D().get(i)))));
      }
    }

    // add `mask` to the URL query string
    if (getMask() != null) {
      for (int i = 0; i < getMask().size(); i++) {
        joiner.add(String.format(java.util.Locale.ROOT, "%smask%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
            ApiClient.urlEncode(ApiClient.valueToString(getMask().get(i)))));
      }
    }

    // add `side` to the URL query string
    if (getSide() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sside%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getSide()))));
    }

    // add `type` to the URL query string
    if (getType() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%stype%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getType()))));
    }

    // add `confidence` to the URL query string
    if (getConfidence() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sconfidence%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getConfidence()))));
    }

    // add `imageUrl` to the URL query string
    if (getImageUrl() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%simageUrl%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getImageUrl()))));
    }

    return joiner.toString();
  }
}
