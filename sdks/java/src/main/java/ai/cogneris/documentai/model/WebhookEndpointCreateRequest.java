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
import ai.cogneris.documentai.model.WebhookEvent;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.openapitools.jackson.nullable.JsonNullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.openapitools.jackson.nullable.JsonNullable;
import java.util.NoSuchElementException;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * WebhookEndpointCreateRequest
 */
@JsonPropertyOrder({
  WebhookEndpointCreateRequest.JSON_PROPERTY_NAME,
  WebhookEndpointCreateRequest.JSON_PROPERTY_URL,
  WebhookEndpointCreateRequest.JSON_PROPERTY_EVENTS,
  WebhookEndpointCreateRequest.JSON_PROPERTY_HEADERS,
  WebhookEndpointCreateRequest.JSON_PROPERTY_BODY
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class WebhookEndpointCreateRequest {
  public static final String JSON_PROPERTY_NAME = "name";
  @javax.annotation.Nonnull
  private String name;

  public static final String JSON_PROPERTY_URL = "url";
  @javax.annotation.Nonnull
  private URI url;

  public static final String JSON_PROPERTY_EVENTS = "events";
  @javax.annotation.Nonnull
  private List<WebhookEvent> events = new ArrayList<>();

  public static final String JSON_PROPERTY_HEADERS = "headers";
  private JsonNullable<Map<String, String>> headers = JsonNullable.<Map<String, String>>undefined();

  public static final String JSON_PROPERTY_BODY = "body";
  private JsonNullable<String> body = JsonNullable.<String>undefined();

  public WebhookEndpointCreateRequest() {
  }

  public WebhookEndpointCreateRequest name(@javax.annotation.Nonnull String name) {
    this.name = name;
    return this;
  }

  /**
   * Get name
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


  public WebhookEndpointCreateRequest url(@javax.annotation.Nonnull URI url) {
    this.url = url;
    return this;
  }

  /**
   * Absolute HTTPS on a public address. Private, loopback and link-local targets are refused.
   * @return url
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_URL, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public URI getUrl() {
    return url;
  }


  @JsonProperty(value = JSON_PROPERTY_URL, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setUrl(@javax.annotation.Nonnull URI url) {
    this.url = url;
  }


  public WebhookEndpointCreateRequest events(@javax.annotation.Nonnull List<WebhookEvent> events) {
    this.events = events;
    return this;
  }

  public WebhookEndpointCreateRequest addEventsItem(WebhookEvent eventsItem) {
    if (this.events == null) {
      this.events = new ArrayList<>();
    }
    this.events.add(eventsItem);
    return this;
  }

  /**
   * Get events
   * @return events
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_EVENTS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public List<WebhookEvent> getEvents() {
    return events;
  }


  @JsonProperty(value = JSON_PROPERTY_EVENTS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setEvents(@javax.annotation.Nonnull List<WebhookEvent> events) {
    this.events = events;
  }


  public WebhookEndpointCreateRequest headers(@javax.annotation.Nullable Map<String, String> headers) {
    this.headers = JsonNullable.<Map<String, String>>of(headers);
    return this;
  }

  public WebhookEndpointCreateRequest putHeadersItem(String key, String headersItem) {
    if (this.headers == null || !this.headers.isPresent() || this.headers.get() == null) {
      this.headers = JsonNullable.<Map<String, String>>of(new HashMap<>());
    }
    try {
      this.headers.get().put(key, headersItem);
    } catch (java.util.NoSuchElementException e) {
      // this can never happen, as we make sure above that the value is present
    }
    return this;
  }

  /**
   * Sent on every delivery, for example your receiver&#39;s own credential. Stored encrypted.
   * @return headers
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public Map<String, String> getHeaders() {
        return headers.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_HEADERS, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<Map<String, String>> getHeaders_JsonNullable() {
    return headers;
  }

  @JsonProperty(JSON_PROPERTY_HEADERS)
  public void setHeaders_JsonNullable(JsonNullable<Map<String, String>> headers) {
    this.headers = headers;
  }

  public void setHeaders(@javax.annotation.Nullable Map<String, String> headers) {
    this.headers = JsonNullable.<Map<String, String>>of(headers);
  }


  public WebhookEndpointCreateRequest body(@javax.annotation.Nullable String body) {
    this.body = JsonNullable.<String>of(body);
    return this;
  }

  /**
   * Sent **instead of** the event payload when set. Leave it unset to receive the job fields.
   * @return body
   */
  @javax.annotation.Nullable
  @JsonIgnore
  public String getBody() {
        return body.orElse(null);
  }

  @JsonProperty(value = JSON_PROPERTY_BODY, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)

  public JsonNullable<String> getBody_JsonNullable() {
    return body;
  }

  @JsonProperty(JSON_PROPERTY_BODY)
  public void setBody_JsonNullable(JsonNullable<String> body) {
    this.body = body;
  }

  public void setBody(@javax.annotation.Nullable String body) {
    this.body = JsonNullable.<String>of(body);
  }


  /**
   * Return true if this WebhookEndpointCreateRequest object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    WebhookEndpointCreateRequest webhookEndpointCreateRequest = (WebhookEndpointCreateRequest) o;
    return Objects.equals(this.name, webhookEndpointCreateRequest.name) &&
        Objects.equals(this.url, webhookEndpointCreateRequest.url) &&
        Objects.equals(this.events, webhookEndpointCreateRequest.events) &&
        equalsNullable(this.headers, webhookEndpointCreateRequest.headers) &&
        equalsNullable(this.body, webhookEndpointCreateRequest.body);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, url, events, hashCodeNullable(headers), hashCodeNullable(body));
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
    sb.append("class WebhookEndpointCreateRequest {\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
    sb.append("    events: ").append(toIndentedString(events)).append("\n");
    sb.append("    headers: ").append(toIndentedString(headers)).append("\n");
    sb.append("    body: ").append(toIndentedString(body)).append("\n");
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

    // add `name` to the URL query string
    if (getName() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sname%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getName()))));
    }

    // add `url` to the URL query string
    if (getUrl() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%surl%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getUrl()))));
    }

    // add `events` to the URL query string
    if (getEvents() != null) {
      for (int i = 0; i < getEvents().size(); i++) {
        if (getEvents().get(i) != null) {
          joiner.add(String.format(java.util.Locale.ROOT, "%sevents%s%s=%s", prefix, suffix,
              "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
              ApiClient.urlEncode(ApiClient.valueToString(getEvents().get(i)))));
        }
      }
    }

    // add `headers` to the URL query string
    if (getHeaders() != null) {
      for (String _key : getHeaders().keySet()) {
        joiner.add(String.format(java.util.Locale.ROOT, "%sheaders%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, _key, containerSuffix),
            getHeaders().get(_key), ApiClient.urlEncode(ApiClient.valueToString(getHeaders().get(_key)))));
      }
    }

    // add `body` to the URL query string
    if (getBody() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sbody%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getBody()))));
    }

    return joiner.toString();
  }
}
