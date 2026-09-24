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
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.util.Arrays;
import java.util.UUID;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * ClassificationResult
 */
@JsonPropertyOrder({
  ClassificationResult.JSON_PROPERTY_FILE_NAME,
  ClassificationResult.JSON_PROPERTY_DOCUMENT_TYPE,
  ClassificationResult.JSON_PROPERTY_CONFIDENCE,
  ClassificationResult.JSON_PROPERTY_PAGES,
  ClassificationResult.JSON_PROPERTY_TEMPLATE_ID,
  ClassificationResult.JSON_PROPERTY_TEMPLATE_METADATA
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class ClassificationResult {
  public static final String JSON_PROPERTY_FILE_NAME = "fileName";
  @javax.annotation.Nullable
  private String fileName;

  public static final String JSON_PROPERTY_DOCUMENT_TYPE = "documentType";
  @javax.annotation.Nullable
  private String documentType;

  public static final String JSON_PROPERTY_CONFIDENCE = "confidence";
  @javax.annotation.Nullable
  private BigDecimal confidence;

  public static final String JSON_PROPERTY_PAGES = "pages";
  private JsonNullable<Integer> pages = JsonNullable.<Integer>undefined();

  public static final String JSON_PROPERTY_TEMPLATE_ID = "templateId";
  private JsonNullable<UUID> templateId = JsonNullable.<UUID>undefined();

  public static final String JSON_PROPERTY_TEMPLATE_METADATA = "templateMetadata";
  private JsonNullable<String> templateMetadata = JsonNullable.<String>undefined();

  public ClassificationResult() {
  }

  public ClassificationResult fileName(@javax.annotation.Nullable String fileName) {
    this.fileName = fileName;
    return this;
  }

  /**
   * The uploaded file this entry classifies.
   * @return fileName
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_FILE_NAME, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getFileName() {
    return fileName;
  }


  @JsonProperty(value = JSON_PROPERTY_FILE_NAME, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setFileName(@javax.annotation.Nullable String fileName) {
    this.fileName = fileName;
  }


  public ClassificationResult documentType(@javax.annotation.Nullable String documentType) {
    this.documentType = documentType;
    return this;
  }

  /**
   * Get documentType
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


  public ClassificationResult confidence(@javax.annotation.Nullable BigDecimal confidence) {
    this.confidence = confidence;
    return this;
  }

  /**
   * Certainty in &#x60;documentType&#x60;.
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


  public ClassificationResult pages(@javax.annotation.Nullable Integer pages) {
    this.pages = JsonNullable.<Integer>of(pages);
    return this;
  }

  /**
   * Get pages
   * @return pages
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public Integer getPages() {
        return pages.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_PAGES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<Integer> getPages_JsonNullable() {
    return pages;
  }

  @JsonProperty(JSON_PROPERTY_PAGES)
  public void setPages_JsonNullable(JsonNullable<Integer> pages) {
    this.pages = pages;
  }

  public void setPages(@javax.annotation.Nullable Integer pages) {
    this.pages = JsonNullable.<Integer>of(pages);
  }


  public ClassificationResult templateId(@javax.annotation.Nullable UUID templateId) {
    this.templateId = JsonNullable.<UUID>of(templateId);
    return this;
  }

  /**
   * The template the document type resolves to, when one is configured.
   * @return templateId
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public UUID getTemplateId() {
        return templateId.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_TEMPLATE_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<UUID> getTemplateId_JsonNullable() {
    return templateId;
  }

  @JsonProperty(JSON_PROPERTY_TEMPLATE_ID)
  public void setTemplateId_JsonNullable(JsonNullable<UUID> templateId) {
    this.templateId = templateId;
  }

  public void setTemplateId(@javax.annotation.Nullable UUID templateId) {
    this.templateId = JsonNullable.<UUID>of(templateId);
  }


  public ClassificationResult templateMetadata(@javax.annotation.Nullable String templateMetadata) {
    this.templateMetadata = JsonNullable.<String>of(templateMetadata);
    return this;
  }

  /**
   * The matched template&#39;s schema. Null when &#x60;templateId&#x60; is, or the template has no schema yet.
   * @return templateMetadata
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getTemplateMetadata() {
        return templateMetadata.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_TEMPLATE_METADATA, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getTemplateMetadata_JsonNullable() {
    return templateMetadata;
  }

  @JsonProperty(JSON_PROPERTY_TEMPLATE_METADATA)
  public void setTemplateMetadata_JsonNullable(JsonNullable<String> templateMetadata) {
    this.templateMetadata = templateMetadata;
  }

  public void setTemplateMetadata(@javax.annotation.Nullable String templateMetadata) {
    this.templateMetadata = JsonNullable.<String>of(templateMetadata);
  }


  /**
   * Return true if this ClassificationResult object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    ClassificationResult classificationResult = (ClassificationResult) o;
    return Objects.equals(this.fileName, classificationResult.fileName) &&
        Objects.equals(this.documentType, classificationResult.documentType) &&
        Objects.equals(this.confidence, classificationResult.confidence) &&
        equalsNullable(this.pages, classificationResult.pages) &&
        equalsNullable(this.templateId, classificationResult.templateId) &&
        equalsNullable(this.templateMetadata, classificationResult.templateMetadata);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(fileName, documentType, confidence, hashCodeNullable(pages), hashCodeNullable(templateId), hashCodeNullable(templateMetadata));
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
    sb.append("class ClassificationResult {\n");
    sb.append("    fileName: ").append(toIndentedString(fileName)).append("\n");
    sb.append("    documentType: ").append(toIndentedString(documentType)).append("\n");
    sb.append("    confidence: ").append(toIndentedString(confidence)).append("\n");
    sb.append("    pages: ").append(toIndentedString(pages)).append("\n");
    sb.append("    templateId: ").append(toIndentedString(templateId)).append("\n");
    sb.append("    templateMetadata: ").append(toIndentedString(templateMetadata)).append("\n");
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

    // add `fileName` to the URL query string
    if (getFileName() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sfileName%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFileName()))));
    }

    // add `documentType` to the URL query string
    if (getDocumentType() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sdocumentType%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getDocumentType()))));
    }

    // add `confidence` to the URL query string
    if (getConfidence() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sconfidence%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getConfidence()))));
    }

    // add `pages` to the URL query string
    if (getPages() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%spages%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getPages()))));
    }

    // add `templateId` to the URL query string
    if (getTemplateId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%stemplateId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getTemplateId()))));
    }

    // add `templateMetadata` to the URL query string
    if (getTemplateMetadata() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%stemplateMetadata%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getTemplateMetadata()))));
    }

    return joiner.toString();
  }
}
