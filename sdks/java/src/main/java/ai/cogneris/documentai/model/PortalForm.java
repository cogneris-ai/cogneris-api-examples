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
import java.util.Arrays;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * PortalForm
 */
@JsonPropertyOrder({
  PortalForm.JSON_PROPERTY_FORM_ID,
  PortalForm.JSON_PROPERTY_FORM_NAME,
  PortalForm.JSON_PROPERTY_FORM_DESCRIPTION
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class PortalForm {
  public static final String JSON_PROPERTY_FORM_ID = "formId";
  @javax.annotation.Nullable
  private Long formId;

  public static final String JSON_PROPERTY_FORM_NAME = "formName";
  @javax.annotation.Nullable
  private String formName;

  public static final String JSON_PROPERTY_FORM_DESCRIPTION = "formDescription";
  private JsonNullable<String> formDescription = JsonNullable.<String>undefined();

  public PortalForm() {
  }

  public PortalForm formId(@javax.annotation.Nullable Long formId) {
    this.formId = formId;
    return this;
  }

  /**
   * Get formId
   * @return formId
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_FORM_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Long getFormId() {
    return formId;
  }


  @JsonProperty(value = JSON_PROPERTY_FORM_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setFormId(@javax.annotation.Nullable Long formId) {
    this.formId = formId;
  }


  public PortalForm formName(@javax.annotation.Nullable String formName) {
    this.formName = formName;
    return this;
  }

  /**
   * Get formName
   * @return formName
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_FORM_NAME, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getFormName() {
    return formName;
  }


  @JsonProperty(value = JSON_PROPERTY_FORM_NAME, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setFormName(@javax.annotation.Nullable String formName) {
    this.formName = formName;
  }


  public PortalForm formDescription(@javax.annotation.Nullable String formDescription) {
    this.formDescription = JsonNullable.<String>of(formDescription);
    return this;
  }

  /**
   * Get formDescription
   * @return formDescription
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getFormDescription() {
        return formDescription.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_FORM_DESCRIPTION, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getFormDescription_JsonNullable() {
    return formDescription;
  }

  @JsonProperty(JSON_PROPERTY_FORM_DESCRIPTION)
  public void setFormDescription_JsonNullable(JsonNullable<String> formDescription) {
    this.formDescription = formDescription;
  }

  public void setFormDescription(@javax.annotation.Nullable String formDescription) {
    this.formDescription = JsonNullable.<String>of(formDescription);
  }


  /**
   * Return true if this PortalForm object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PortalForm portalForm = (PortalForm) o;
    return Objects.equals(this.formId, portalForm.formId) &&
        Objects.equals(this.formName, portalForm.formName) &&
        equalsNullable(this.formDescription, portalForm.formDescription);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(formId, formName, hashCodeNullable(formDescription));
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
    sb.append("class PortalForm {\n");
    sb.append("    formId: ").append(toIndentedString(formId)).append("\n");
    sb.append("    formName: ").append(toIndentedString(formName)).append("\n");
    sb.append("    formDescription: ").append(toIndentedString(formDescription)).append("\n");
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

    // add `formId` to the URL query string
    if (getFormId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sformId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFormId()))));
    }

    // add `formName` to the URL query string
    if (getFormName() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sformName%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFormName()))));
    }

    // add `formDescription` to the URL query string
    if (getFormDescription() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sformDescription%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getFormDescription()))));
    }

    return joiner.toString();
  }
}
