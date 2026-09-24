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
import ai.cogneris.documentai.model.QualityVerdict;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.util.Arrays;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * QualityFinding
 */
@JsonPropertyOrder({
  QualityFinding.JSON_PROPERTY_PROBE,
  QualityFinding.JSON_PROPERTY_LEVEL,
  QualityFinding.JSON_PROPERTY_MEASURED,
  QualityFinding.JSON_PROPERTY_THRESHOLD,
  QualityFinding.JSON_PROPERTY_MESSAGE
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class QualityFinding {
  public static final String JSON_PROPERTY_PROBE = "probe";
  @javax.annotation.Nonnull
  private String probe;

  public static final String JSON_PROPERTY_LEVEL = "level";
  @javax.annotation.Nonnull
  private QualityVerdict level;

  public static final String JSON_PROPERTY_MEASURED = "measured";
  @javax.annotation.Nonnull
  private BigDecimal measured;

  public static final String JSON_PROPERTY_THRESHOLD = "threshold";
  @javax.annotation.Nonnull
  private BigDecimal threshold;

  public static final String JSON_PROPERTY_MESSAGE = "message";
  @javax.annotation.Nonnull
  private String message;

  public QualityFinding() {
  }

  public QualityFinding probe(@javax.annotation.Nonnull String probe) {
    this.probe = probe;
    return this;
  }

  /**
   * The check that crossed its threshold, such as &#x60;blur&#x60; or &#x60;resolution&#x60;.
   * @return probe
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_PROBE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public String getProbe() {
    return probe;
  }


  @JsonProperty(value = JSON_PROPERTY_PROBE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setProbe(@javax.annotation.Nonnull String probe) {
    this.probe = probe;
  }


  public QualityFinding level(@javax.annotation.Nonnull QualityVerdict level) {
    this.level = level;
    return this;
  }

  /**
   * Get level
   * @return level
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_LEVEL, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public QualityVerdict getLevel() {
    return level;
  }


  @JsonProperty(value = JSON_PROPERTY_LEVEL, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setLevel(@javax.annotation.Nonnull QualityVerdict level) {
    this.level = level;
  }


  public QualityFinding measured(@javax.annotation.Nonnull BigDecimal measured) {
    this.measured = measured;
    return this;
  }

  /**
   * Get measured
   * @return measured
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_MEASURED, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public BigDecimal getMeasured() {
    return measured;
  }


  @JsonProperty(value = JSON_PROPERTY_MEASURED, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setMeasured(@javax.annotation.Nonnull BigDecimal measured) {
    this.measured = measured;
  }


  public QualityFinding threshold(@javax.annotation.Nonnull BigDecimal threshold) {
    this.threshold = threshold;
    return this;
  }

  /**
   * Get threshold
   * @return threshold
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_THRESHOLD, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public BigDecimal getThreshold() {
    return threshold;
  }


  @JsonProperty(value = JSON_PROPERTY_THRESHOLD, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setThreshold(@javax.annotation.Nonnull BigDecimal threshold) {
    this.threshold = threshold;
  }


  public QualityFinding message(@javax.annotation.Nonnull String message) {
    this.message = message;
    return this;
  }

  /**
   * Get message
   * @return message
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_MESSAGE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public String getMessage() {
    return message;
  }


  @JsonProperty(value = JSON_PROPERTY_MESSAGE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setMessage(@javax.annotation.Nonnull String message) {
    this.message = message;
  }


  /**
   * Return true if this QualityFinding object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    QualityFinding qualityFinding = (QualityFinding) o;
    return Objects.equals(this.probe, qualityFinding.probe) &&
        Objects.equals(this.level, qualityFinding.level) &&
        Objects.equals(this.measured, qualityFinding.measured) &&
        Objects.equals(this.threshold, qualityFinding.threshold) &&
        Objects.equals(this.message, qualityFinding.message);
  }

  @Override
  public int hashCode() {
    return Objects.hash(probe, level, measured, threshold, message);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class QualityFinding {\n");
    sb.append("    probe: ").append(toIndentedString(probe)).append("\n");
    sb.append("    level: ").append(toIndentedString(level)).append("\n");
    sb.append("    measured: ").append(toIndentedString(measured)).append("\n");
    sb.append("    threshold: ").append(toIndentedString(threshold)).append("\n");
    sb.append("    message: ").append(toIndentedString(message)).append("\n");
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

    // add `probe` to the URL query string
    if (getProbe() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sprobe%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getProbe()))));
    }

    // add `level` to the URL query string
    if (getLevel() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%slevel%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getLevel()))));
    }

    // add `measured` to the URL query string
    if (getMeasured() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%smeasured%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getMeasured()))));
    }

    // add `threshold` to the URL query string
    if (getThreshold() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sthreshold%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getThreshold()))));
    }

    // add `message` to the URL query string
    if (getMessage() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%smessage%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getMessage()))));
    }

    return joiner.toString();
  }
}
