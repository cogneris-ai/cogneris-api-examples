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
import ai.cogneris.documentai.model.PortalMagicLinkOptIn;
import ai.cogneris.documentai.model.PortalSendChannel;
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
 * PortalMagicLinkRequest
 */
@JsonPropertyOrder({
  PortalMagicLinkRequest.JSON_PROPERTY_FORM_ID,
  PortalMagicLinkRequest.JSON_PROPERTY_NAME,
  PortalMagicLinkRequest.JSON_PROPERTY_SEND_CHANNEL,
  PortalMagicLinkRequest.JSON_PROPERTY_EMAIL,
  PortalMagicLinkRequest.JSON_PROPERTY_PHONE,
  PortalMagicLinkRequest.JSON_PROPERTY_TAX_ID,
  PortalMagicLinkRequest.JSON_PROPERTY_DUE_DAYS,
  PortalMagicLinkRequest.JSON_PROPERTY_MAX_ACCESSES,
  PortalMagicLinkRequest.JSON_PROPERTY_NOTES,
  PortalMagicLinkRequest.JSON_PROPERTY_OPT_IN
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class PortalMagicLinkRequest {
  public static final String JSON_PROPERTY_FORM_ID = "formId";
  @javax.annotation.Nonnull
  private Long formId;

  public static final String JSON_PROPERTY_NAME = "name";
  @javax.annotation.Nonnull
  private String name;

  public static final String JSON_PROPERTY_SEND_CHANNEL = "sendChannel";
  private JsonNullable<PortalSendChannel> sendChannel = JsonNullable.<PortalSendChannel>undefined();

  public static final String JSON_PROPERTY_EMAIL = "email";
  private JsonNullable<String> email = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_PHONE = "phone";
  private JsonNullable<String> phone = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_TAX_ID = "taxId";
  private JsonNullable<String> taxId = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_DUE_DAYS = "dueDays";
  @javax.annotation.Nullable
  private Integer dueDays = 30;

  public static final String JSON_PROPERTY_MAX_ACCESSES = "maxAccesses";
  private JsonNullable<Integer> maxAccesses = JsonNullable.<Integer>undefined();

  public static final String JSON_PROPERTY_NOTES = "notes";
  private JsonNullable<String> notes = JsonNullable.<String>undefined();

  public static final String JSON_PROPERTY_OPT_IN = "optIn";
  private JsonNullable<PortalMagicLinkOptIn> optIn = JsonNullable.<PortalMagicLinkOptIn>undefined();

  public PortalMagicLinkRequest() {
  }

  public PortalMagicLinkRequest formId(@javax.annotation.Nonnull Long formId) {
    this.formId = formId;
    return this;
  }

  /**
   * Target form, from &#x60;GET /api/v1/portal/forms&#x60;. Must be greater than zero.
   * @return formId
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_FORM_ID, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public Long getFormId() {
    return formId;
  }


  @JsonProperty(value = JSON_PROPERTY_FORM_ID, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setFormId(@javax.annotation.Nonnull Long formId) {
    this.formId = formId;
  }


  public PortalMagicLinkRequest name(@javax.annotation.Nonnull String name) {
    this.name = name;
    return this;
  }

  /**
   * Recipient display name.
   * @return name
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_NAME, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public String getName() {
    return name;
  }


  @JsonProperty(value = JSON_PROPERTY_NAME, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setName(@javax.annotation.Nonnull String name) {
    this.name = name;
  }


  public PortalMagicLinkRequest sendChannel(@javax.annotation.Nullable PortalSendChannel sendChannel) {
    this.sendChannel = JsonNullable.<PortalSendChannel>of(sendChannel);
    return this;
  }

  /**
   * Channel to deliver the link on. Omit it to create the link without sending anything.
   * @return sendChannel
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public PortalSendChannel getSendChannel() {
        return sendChannel.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_SEND_CHANNEL, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<PortalSendChannel> getSendChannel_JsonNullable() {
    return sendChannel;
  }

  @JsonProperty(JSON_PROPERTY_SEND_CHANNEL)
  public void setSendChannel_JsonNullable(JsonNullable<PortalSendChannel> sendChannel) {
    this.sendChannel = sendChannel;
  }

  public void setSendChannel(@javax.annotation.Nullable PortalSendChannel sendChannel) {
    this.sendChannel = JsonNullable.<PortalSendChannel>of(sendChannel);
  }


  public PortalMagicLinkRequest email(@javax.annotation.Nullable String email) {
    this.email = JsonNullable.<String>of(email);
    return this;
  }

  /**
   * Required when &#x60;sendChannel&#x60; is &#x60;email&#x60;.
   * @return email
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getEmail() {
        return email.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_EMAIL, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getEmail_JsonNullable() {
    return email;
  }

  @JsonProperty(JSON_PROPERTY_EMAIL)
  public void setEmail_JsonNullable(JsonNullable<String> email) {
    this.email = email;
  }

  public void setEmail(@javax.annotation.Nullable String email) {
    this.email = JsonNullable.<String>of(email);
  }


  public PortalMagicLinkRequest phone(@javax.annotation.Nullable String phone) {
    this.phone = JsonNullable.<String>of(phone);
    return this;
  }

  /**
   * Required when &#x60;sendChannel&#x60; is &#x60;sms&#x60; or &#x60;whatsapp&#x60;.
   * @return phone
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getPhone() {
        return phone.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_PHONE, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getPhone_JsonNullable() {
    return phone;
  }

  @JsonProperty(JSON_PROPERTY_PHONE)
  public void setPhone_JsonNullable(JsonNullable<String> phone) {
    this.phone = phone;
  }

  public void setPhone(@javax.annotation.Nullable String phone) {
    this.phone = JsonNullable.<String>of(phone);
  }


  public PortalMagicLinkRequest taxId(@javax.annotation.Nullable String taxId) {
    this.taxId = JsonNullable.<String>of(taxId);
    return this;
  }

  /**
   * Recipient tax id.
   * @return taxId
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getTaxId() {
        return taxId.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_TAX_ID, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getTaxId_JsonNullable() {
    return taxId;
  }

  @JsonProperty(JSON_PROPERTY_TAX_ID)
  public void setTaxId_JsonNullable(JsonNullable<String> taxId) {
    this.taxId = taxId;
  }

  public void setTaxId(@javax.annotation.Nullable String taxId) {
    this.taxId = JsonNullable.<String>of(taxId);
  }


  public PortalMagicLinkRequest dueDays(@javax.annotation.Nullable Integer dueDays) {
    this.dueDays = dueDays;
    return this;
  }

  /**
   * Days until the link expires. A value of zero or less is treated as 30.
   * @return dueDays
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_DUE_DAYS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public Integer getDueDays() {
    return dueDays;
  }


  @JsonProperty(value = JSON_PROPERTY_DUE_DAYS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setDueDays(@javax.annotation.Nullable Integer dueDays) {
    this.dueDays = dueDays;
  }


  public PortalMagicLinkRequest maxAccesses(@javax.annotation.Nullable Integer maxAccesses) {
    this.maxAccesses = JsonNullable.<Integer>of(maxAccesses);
    return this;
  }

  /**
   * How many times the link may be opened. Null means unlimited; 1 makes it single-use.
   * @return maxAccesses
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public Integer getMaxAccesses() {
        return maxAccesses.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_MAX_ACCESSES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<Integer> getMaxAccesses_JsonNullable() {
    return maxAccesses;
  }

  @JsonProperty(JSON_PROPERTY_MAX_ACCESSES)
  public void setMaxAccesses_JsonNullable(JsonNullable<Integer> maxAccesses) {
    this.maxAccesses = maxAccesses;
  }

  public void setMaxAccesses(@javax.annotation.Nullable Integer maxAccesses) {
    this.maxAccesses = JsonNullable.<Integer>of(maxAccesses);
  }


  public PortalMagicLinkRequest notes(@javax.annotation.Nullable String notes) {
    this.notes = JsonNullable.<String>of(notes);
    return this;
  }

  /**
   * Internal note kept against the link, never shown to the recipient.
   * @return notes
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getNotes() {
        return notes.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_NOTES, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getNotes_JsonNullable() {
    return notes;
  }

  @JsonProperty(JSON_PROPERTY_NOTES)
  public void setNotes_JsonNullable(JsonNullable<String> notes) {
    this.notes = notes;
  }

  public void setNotes(@javax.annotation.Nullable String notes) {
    this.notes = JsonNullable.<String>of(notes);
  }


  public PortalMagicLinkRequest optIn(@javax.annotation.Nullable PortalMagicLinkOptIn optIn) {
    this.optIn = JsonNullable.<PortalMagicLinkOptIn>of(optIn);
    return this;
  }

  /**
   * WhatsApp consent for this recipient, recorded alongside creation. Supply it when consent is not already on file. Omit it when consent is already held. Only WhatsApp records this consent; email and SMS use their own consent rules. When supplied, source and non-blank evidenceText are required for every channel.
   * @return optIn
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public PortalMagicLinkOptIn getOptIn() {
        return optIn.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_OPT_IN, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<PortalMagicLinkOptIn> getOptIn_JsonNullable() {
    return optIn;
  }

  @JsonProperty(JSON_PROPERTY_OPT_IN)
  public void setOptIn_JsonNullable(JsonNullable<PortalMagicLinkOptIn> optIn) {
    this.optIn = optIn;
  }

  public void setOptIn(@javax.annotation.Nullable PortalMagicLinkOptIn optIn) {
    this.optIn = JsonNullable.<PortalMagicLinkOptIn>of(optIn);
  }


  /**
   * Return true if this PortalMagicLinkRequest object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PortalMagicLinkRequest portalMagicLinkRequest = (PortalMagicLinkRequest) o;
    return Objects.equals(this.formId, portalMagicLinkRequest.formId) &&
        Objects.equals(this.name, portalMagicLinkRequest.name) &&
        equalsNullable(this.sendChannel, portalMagicLinkRequest.sendChannel) &&
        equalsNullable(this.email, portalMagicLinkRequest.email) &&
        equalsNullable(this.phone, portalMagicLinkRequest.phone) &&
        equalsNullable(this.taxId, portalMagicLinkRequest.taxId) &&
        Objects.equals(this.dueDays, portalMagicLinkRequest.dueDays) &&
        equalsNullable(this.maxAccesses, portalMagicLinkRequest.maxAccesses) &&
        equalsNullable(this.notes, portalMagicLinkRequest.notes) &&
        equalsNullable(this.optIn, portalMagicLinkRequest.optIn);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(formId, name, hashCodeNullable(sendChannel), hashCodeNullable(email), hashCodeNullable(phone), hashCodeNullable(taxId), dueDays, hashCodeNullable(maxAccesses), hashCodeNullable(notes), hashCodeNullable(optIn));
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
    sb.append("class PortalMagicLinkRequest {\n");
    sb.append("    formId: ").append(toIndentedString(formId)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    sendChannel: ").append(toIndentedString(sendChannel)).append("\n");
    sb.append("    email: ").append(toIndentedString(email)).append("\n");
    sb.append("    phone: ").append(toIndentedString(phone)).append("\n");
    sb.append("    taxId: ").append(toIndentedString(taxId)).append("\n");
    sb.append("    dueDays: ").append(toIndentedString(dueDays)).append("\n");
    sb.append("    maxAccesses: ").append(toIndentedString(maxAccesses)).append("\n");
    sb.append("    notes: ").append(toIndentedString(notes)).append("\n");
    sb.append("    optIn: ").append(toIndentedString(optIn)).append("\n");
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

    // add `name` to the URL query string
    if (getName() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sname%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getName()))));
    }

    // add `sendChannel` to the URL query string
    if (getSendChannel() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%ssendChannel%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getSendChannel()))));
    }

    // add `email` to the URL query string
    if (getEmail() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%semail%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getEmail()))));
    }

    // add `phone` to the URL query string
    if (getPhone() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sphone%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getPhone()))));
    }

    // add `taxId` to the URL query string
    if (getTaxId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%staxId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getTaxId()))));
    }

    // add `dueDays` to the URL query string
    if (getDueDays() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sdueDays%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getDueDays()))));
    }

    // add `maxAccesses` to the URL query string
    if (getMaxAccesses() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%smaxAccesses%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getMaxAccesses()))));
    }

    // add `notes` to the URL query string
    if (getNotes() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%snotes%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getNotes()))));
    }

    // add `optIn` to the URL query string
    if (getOptIn() != null) {
      joiner.add(getOptIn().toUrlQueryString(prefix + "optIn" + suffix));
    }

    return joiner.toString();
  }
}
