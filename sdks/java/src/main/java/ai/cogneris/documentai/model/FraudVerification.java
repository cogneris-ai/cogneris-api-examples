/*
 * Cogneris Document AI API
 * The Cogneris Document AI API turns unstructured documents — PDFs, images, scans — into structured JSON.  This document describes the endpoints that are actually deployed. It is written from the running service (`cogneris-api-be`) rather than from a design, so what is listed here is what you can call.  ## Authentication  Every endpoint takes an API key in the `Authorization` header as `Bearer <key>`. Keys begin with `xtkt_live_` (production) or `xtkt_test_` (sandbox); either prefix is accepted before the key is looked up for validation. The key selects the application environment. A recognized prefix alone does not authenticate a request: the key must also be valid and active. Keys are tenant-scoped and cannot cross tenant boundaries. Mint them in the console under **Vision → Developers → API Keys**.  ## Sandbox  A `xtkt_test_` (sandbox) key is accepted for authentication, but sandbox covers only the asynchronous job flow. Everything else refuses it.  - **Available routes.** `POST /api/v1/artifacts`, `GET /api/v1/artifacts/content`,   `POST /api/v1/document-jobs`, `GET /api/v1/document-jobs`,   `GET /api/v1/document-jobs/{jobId}` and `POST /api/v1/document-jobs/{jobId}/cancel`. - **Every other route refuses a sandbox key** — the synchronous `/Document/_*`   endpoints, `/api/v1/templates`, `/api/v1/portal/_*` and   `/api/v1/webhook-endpoints*` — with `403`, `application/problem+json` and   `code` `environment.sandbox_route_unavailable`. - **Job submit is narrower.** On `POST /api/v1/document-jobs` a sandbox key may   run only `Extraction` without a `templateId`, `Classification`, `ZeroShot`,   `Crop` and `Split`. Any other operation (for example `Facematch`), or any   `templateId`, is refused with the same `403` and `code`. - **No credits.** A sandbox job does not debit credits or production quota, so   `creditsConsumed` is always `null` for a sandbox key.  ## Uploads  The synchronous document endpoints take `multipart/form-data`. There is no fetch-by-URL variant — the file travels in the request body.  - Accepted extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`,   `.bmp`, `.doc`, `.docx` - Maximum size: 10 MB per file, except `/Document/split`, which accepts 500 MB  The asynchronous job endpoints do not take a file. Upload it first to `POST /api/v1/artifacts` — same extensions, same 10 MB limit — and submit the `artifact://` reference it returns.  ## Artifact references  A reference names one stored object. `POST /api/v1/artifacts` returns one, a job submit consumes one as `inputReference`, and a finished job returns one as `outputReference`. `GET /api/v1/artifacts/content` turns either back into bytes.  - References are scoped to the tenant that created them. One belonging to another   tenant is refused as an invalid reference — the answer does not distinguish a   reference that exists elsewhere from one that never existed. - An uploaded reference is **reusable**: one upload can back several jobs. - It expires **7 days** after upload, matching how long a job is retained. The   exact instant is returned as `expiresAt`. Reading it afterwards answers `410`,   which is not `404` — the reference was real, it aged out, and re-requesting it   will never succeed. Upload again. - A job's `outputReference` lives as long as the job does.  ### Two shapes, one of them historical  Everything this API produces today is `artifact://<key>`. Jobs that completed before 2026-09-22 carry a bucket-qualified path instead — `<bucket>/<tenant>/document-jobs/<jobId>/result.json`, sometimes with an `@<version>` suffix. `GET /api/v1/artifacts/content` accepts both, so a reference stored from an older job still resolves for the rest of its life. Treat a reference as opaque: pass back exactly what you were given.  ## Templates  Extraction and classification are driven by the document types and templates configured for your tenant. The platform selects the template from the document itself, so the synchronous `/Document/_*` calls take no template or schema parameter. Use `GET /api/v1/templates` to list the finished templates available to your key before naming one explicitly with `templateId` on `POST /api/v1/document-jobs`. The list is cursor-paginated; pass its `nextCursor` as `cursor` to read the next page.  Templates keep a version history. Publishing or updating a template's definition records a new version, and a job submitted with `templateId` runs on the version that was current when the submit was accepted, reported back as `templateVersion`. You never send a version, and earlier versions cannot be selected for new work, so the same submit repeated after a new publish can return a different result.  ## Scopes  Keys carry scopes. The Portal and webhook-endpoint routes check them and answer `403` when the required one is absent; the document endpoints accept any valid key for the tenant without consulting the list. `*` is a real scope meaning full access, and it is what a key receives when it is created without an explicit scope list.  ## Webhooks  A finished asynchronous job can announce itself, so you do not have to poll it. Register an HTTPS endpoint with `POST /api/v1/webhook-endpoints` and it receives a signed `POST` when a job you subscribed to succeeds, fails or is cancelled. The webhook **announces** the result and does not carry it: read the bytes with `GET /api/v1/artifacts/content?reference=<OutputReference>`.  Endpoints are managed with a **production** key holding `webhooks.manage` (or `*`). An endpoint receives your whole account's production events for the events it subscribes to, and events from sandbox jobs are never delivered, so a sandbox key is refused.  Each delivery carries four headers:  - `X-Xtrakt-Event` — the event name, such as `extract.processed`. - `X-Xtrakt-Delivery` — one id shared by every attempt of the same event at the   same endpoint. Deduplicate on it. - `X-Xtrakt-Delivery-Attempt` — the attempt number, `1` on the first send. - `X-Xtrakt-Signature` — `t=<unix seconds>,v1=<hex>`, where `v1` is the   HMAC-SHA256 of `<t>.<raw body>` keyed with the endpoint's `whsec_` secret.   Recompute it over the raw bytes, compare in constant time, and reject a `t`   outside your tolerance.  For a job, the body is the job's terminal state. **Its property names are PascalCase**, unlike the rest of this API:  ```json {\"JobId\":\"7c9e6679-7425-40de-944b-e07fc1f90ae7\",\"Operation\":\"Extraction\",  \"Status\":\"succeeded\",\"OutputReference\":\"artifact://document-jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7/result.json\",  \"Stage\":null,\"ProcessedPages\":null,\"TotalPages\":null,\"FailureCode\":null,  \"AttemptCount\":1,\"CompletedAt\":\"2026-09-23T14:02:11.482Z\"} ```  `Status` is `succeeded`, `failed` or `cancelled`, and a cancelled job sends the `.failed` event. `OutputReference` is null unless the job succeeded, and always null for `Redaction`. The synchronous `/Document/_*` calls fire the same event names with their own response as the body; a delivery about a job is the one that has `JobId`. An endpoint with a `body` sends that fixed text **instead of** the payload.  Delivery semantics:  - **A job's outcome never depends on its webhook.** A job that succeeded stays   succeeded when the delivery fails; `GET /api/v1/document-jobs/{jobId}` is the   source of truth. - **Up to 5 attempts per endpoint, the first one included.** A timeout, a   transport failure, or a `5xx`, `408` or `429` answer is retried with exponential   backoff (10 s to 600 s between attempts); any other `4xx` is final. The attempt   that reaches the ceiling is recorded as `webhook_retries_exhausted`. Answer `2xx`   fast and do the work afterwards, and reconcile periodically with   `GET /api/v1/document-jobs`. - **Duplicates are possible.** Deduplicate on `X-Xtrakt-Delivery`, or on `JobId`   plus the event. - Every delivery attempt is metered as webhook usage, successful or not.  ## Rate limits  One shared policy covers every surface in this document, Portal included: **50 requests per API key per fixed 1-minute window**. It is a fixed window rather than a token bucket, so the allowance resets on the minute instead of refilling gradually. Requests over the limit receive `429`.  ## Response envelope  Successful responses from the **document, job and webhook-endpoint** routes share one wrapper: `data` for the payload, `meta` for the status and any messages, and `hasErrors` for a fast failure check. The webhook-endpoint routes send their **errors** as problem documents, described next.  The **Portal** endpoints do not use that wrapper. They return the payload directly, and their errors are RFC 9457 problem documents sent as `application/problem+json`, with a stable `code`, a `correlationId` that is also returned in the `x-correlation-id` header, and a `retryable` flag. Branch on `code`; treat `type` as an opaque identifier.  ## Errors  An error arrives in one of two shapes, and the `Content-Type` says which.  - `application/problem+json` — an RFC 9457 problem document, the same one the   Portal uses. Every route answers this way when the failure happens before your   request is processed: a missing or invalid key (`401`), the rate limit (`429`),   a request refused as malformed or unsafe (`400`), or an unexpected failure   (`500`). - `application/json` — the service envelope with `hasErrors: true` and the   reasons in `meta.errors`. The document, job and artifact routes answer this way   when processing itself fails. Each operation lists the statuses where it does.  Every operation lists `400`, `401`, `403`, `404`, `409`, `429` and `500`, because the API answers each of them in the same shape wherever it occurs. A status on an operation with nothing to miss or conflict with — a `409` on a read, say — is part of that uniform model and not something the operation returns in practice.
 *
 * The version of the OpenAPI document: 2026-10-30
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
import ai.cogneris.documentai.model.FraudCheck;
import ai.cogneris.documentai.model.FraudSignal;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


import ai.cogneris.documentai.ApiClient;
/**
 * FraudVerification
 */
@JsonPropertyOrder({
  FraudVerification.JSON_PROPERTY_REQUEST_ID,
  FraudVerification.JSON_PROPERTY_VERDICT,
  FraudVerification.JSON_PROPERTY_RISK_SCORE,
  FraudVerification.JSON_PROPERTY_AI_GENERATED_LIKELIHOOD,
  FraudVerification.JSON_PROPERTY_POLICY_ACTION,
  FraudVerification.JSON_PROPERTY_PIPELINE_VERSION,
  FraudVerification.JSON_PROPERTY_REUSED,
  FraudVerification.JSON_PROPERTY_SIGNALS,
  FraudVerification.JSON_PROPERTY_CHECKS,
  FraudVerification.JSON_PROPERTY_FAILED_COVERAGE
})
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class FraudVerification {
  public static final String JSON_PROPERTY_REQUEST_ID = "requestId";
  @javax.annotation.Nonnull
  private UUID requestId;

  /**
   * Gets or Sets verdict
   */
  public enum VerdictEnum {
    TRUSTED(String.valueOf("trusted")),

    REVIEW(String.valueOf("review")),

    SUSPECT(String.valueOf("suspect"));

    private String value;

    VerdictEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static VerdictEnum fromValue(String value) {
      for (VerdictEnum b : VerdictEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  public static final String JSON_PROPERTY_VERDICT = "verdict";
  @javax.annotation.Nonnull
  private VerdictEnum verdict;

  public static final String JSON_PROPERTY_RISK_SCORE = "riskScore";
  @javax.annotation.Nonnull
  private BigDecimal riskScore;

  public static final String JSON_PROPERTY_AI_GENERATED_LIKELIHOOD = "aiGeneratedLikelihood";
  @javax.annotation.Nullable
  private BigDecimal aiGeneratedLikelihood;

  /**
   * Your tenant&#39;s enforcement policy applied to the verdict. &#x60;block&#x60; means \&quot;do not proceed without a person\&quot;; it is a routing decision, not a rejection.
   */
  public enum PolicyActionEnum {
    ALLOW(String.valueOf("allow")),

    FLAG(String.valueOf("flag")),

    BLOCK(String.valueOf("block"));

    private String value;

    PolicyActionEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static PolicyActionEnum fromValue(String value) {
      for (PolicyActionEnum b : PolicyActionEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  public static final String JSON_PROPERTY_POLICY_ACTION = "policyAction";
  @javax.annotation.Nonnull
  private PolicyActionEnum policyAction;

  public static final String JSON_PROPERTY_PIPELINE_VERSION = "pipelineVersion";
  @javax.annotation.Nullable
  private String pipelineVersion;

  public static final String JSON_PROPERTY_REUSED = "reused";
  @javax.annotation.Nonnull
  private Boolean reused;

  public static final String JSON_PROPERTY_SIGNALS = "signals";
  @javax.annotation.Nonnull
  private List<FraudSignal> signals = new ArrayList<>();

  public static final String JSON_PROPERTY_CHECKS = "checks";
  @javax.annotation.Nonnull
  private List<FraudCheck> checks = new ArrayList<>();

  public static final String JSON_PROPERTY_FAILED_COVERAGE = "failedCoverage";
  @javax.annotation.Nonnull
  private List<String> failedCoverage = new ArrayList<>();

  public FraudVerification() {
  }

  public FraudVerification requestId(@javax.annotation.Nonnull UUID requestId) {
    this.requestId = requestId;
    return this;
  }

  /**
   * Id of the analysis. Read it back with &#x60;GET /api/v1/fraud-verify/{requestId}&#x60;.
   * @return requestId
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_REQUEST_ID, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public UUID getRequestId() {
    return requestId;
  }


  @JsonProperty(value = JSON_PROPERTY_REQUEST_ID, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setRequestId(@javax.annotation.Nonnull UUID requestId) {
    this.requestId = requestId;
  }


  public FraudVerification verdict(@javax.annotation.Nonnull VerdictEnum verdict) {
    this.verdict = verdict;
    return this;
  }

  /**
   * Get verdict
   * @return verdict
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_VERDICT, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public VerdictEnum getVerdict() {
    return verdict;
  }


  @JsonProperty(value = JSON_PROPERTY_VERDICT, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setVerdict(@javax.annotation.Nonnull VerdictEnum verdict) {
    this.verdict = verdict;
  }


  public FraudVerification riskScore(@javax.annotation.Nonnull BigDecimal riskScore) {
    this.riskScore = riskScore;
    return this;
  }

  /**
   * The aggregated risk the verdict was taken from.
   * minimum: 0
   * maximum: 1
   * @return riskScore
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_RISK_SCORE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public BigDecimal getRiskScore() {
    return riskScore;
  }


  @JsonProperty(value = JSON_PROPERTY_RISK_SCORE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setRiskScore(@javax.annotation.Nonnull BigDecimal riskScore) {
    this.riskScore = riskScore;
  }


  public FraudVerification aiGeneratedLikelihood(@javax.annotation.Nullable BigDecimal aiGeneratedLikelihood) {
    this.aiGeneratedLikelihood = aiGeneratedLikelihood;
    return this;
  }

  /**
   * How likely the text was machine-generated. Never decisive on its own.
   * minimum: 0
   * maximum: 1
   * @return aiGeneratedLikelihood
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_AI_GENERATED_LIKELIHOOD, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public BigDecimal getAiGeneratedLikelihood() {
    return aiGeneratedLikelihood;
  }


  @JsonProperty(value = JSON_PROPERTY_AI_GENERATED_LIKELIHOOD, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setAiGeneratedLikelihood(@javax.annotation.Nullable BigDecimal aiGeneratedLikelihood) {
    this.aiGeneratedLikelihood = aiGeneratedLikelihood;
  }


  public FraudVerification policyAction(@javax.annotation.Nonnull PolicyActionEnum policyAction) {
    this.policyAction = policyAction;
    return this;
  }

  /**
   * Your tenant&#39;s enforcement policy applied to the verdict. &#x60;block&#x60; means \&quot;do not proceed without a person\&quot;; it is a routing decision, not a rejection.
   * @return policyAction
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_POLICY_ACTION, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public PolicyActionEnum getPolicyAction() {
    return policyAction;
  }


  @JsonProperty(value = JSON_PROPERTY_POLICY_ACTION, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setPolicyAction(@javax.annotation.Nonnull PolicyActionEnum policyAction) {
    this.policyAction = policyAction;
  }


  public FraudVerification pipelineVersion(@javax.annotation.Nullable String pipelineVersion) {
    this.pipelineVersion = pipelineVersion;
    return this;
  }

  /**
   * Version of the checks that produced this analysis.
   * @return pipelineVersion
   */
  @javax.annotation.Nullable
  @JsonProperty(value = JSON_PROPERTY_PIPELINE_VERSION, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public String getPipelineVersion() {
    return pipelineVersion;
  }


  @JsonProperty(value = JSON_PROPERTY_PIPELINE_VERSION, required = false)
  @JsonInclude(value = JsonInclude.Include.USE_DEFAULTS)
  public void setPipelineVersion(@javax.annotation.Nullable String pipelineVersion) {
    this.pipelineVersion = pipelineVersion;
  }


  public FraudVerification reused(@javax.annotation.Nonnull Boolean reused) {
    this.reused = reused;
    return this;
  }

  /**
   * True when an earlier analysis of the same file was returned, free of charge.
   * @return reused
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_REUSED, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public Boolean getReused() {
    return reused;
  }


  @JsonProperty(value = JSON_PROPERTY_REUSED, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setReused(@javax.annotation.Nonnull Boolean reused) {
    this.reused = reused;
  }


  public FraudVerification signals(@javax.annotation.Nonnull List<FraudSignal> signals) {
    this.signals = signals;
    return this;
  }

  public FraudVerification addSignalsItem(FraudSignal signalsItem) {
    if (this.signals == null) {
      this.signals = new ArrayList<>();
    }
    this.signals.add(signalsItem);
    return this;
  }

  /**
   * Get signals
   * @return signals
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_SIGNALS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public List<FraudSignal> getSignals() {
    return signals;
  }


  @JsonProperty(value = JSON_PROPERTY_SIGNALS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setSignals(@javax.annotation.Nonnull List<FraudSignal> signals) {
    this.signals = signals;
  }


  public FraudVerification checks(@javax.annotation.Nonnull List<FraudCheck> checks) {
    this.checks = checks;
    return this;
  }

  public FraudVerification addChecksItem(FraudCheck checksItem) {
    if (this.checks == null) {
      this.checks = new ArrayList<>();
    }
    this.checks.add(checksItem);
    return this;
  }

  /**
   * Every check that ran, in order.
   * @return checks
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_CHECKS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public List<FraudCheck> getChecks() {
    return checks;
  }


  @JsonProperty(value = JSON_PROPERTY_CHECKS, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setChecks(@javax.annotation.Nonnull List<FraudCheck> checks) {
    this.checks = checks;
  }


  public FraudVerification failedCoverage(@javax.annotation.Nonnull List<String> failedCoverage) {
    this.failedCoverage = failedCoverage;
    return this;
  }

  public FraudVerification addFailedCoverageItem(String failedCoverageItem) {
    if (this.failedCoverage == null) {
      this.failedCoverage = new ArrayList<>();
    }
    this.failedCoverage.add(failedCoverageItem);
    return this;
  }

  /**
   * Checks that could not run on this document.
   * @return failedCoverage
   */
  @javax.annotation.Nonnull
  @JsonProperty(value = JSON_PROPERTY_FAILED_COVERAGE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public List<String> getFailedCoverage() {
    return failedCoverage;
  }


  @JsonProperty(value = JSON_PROPERTY_FAILED_COVERAGE, required = true)
  @JsonInclude(value = JsonInclude.Include.ALWAYS)
  public void setFailedCoverage(@javax.annotation.Nonnull List<String> failedCoverage) {
    this.failedCoverage = failedCoverage;
  }


  /**
   * Return true if this FraudVerification object is equal to o.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FraudVerification fraudVerification = (FraudVerification) o;
    return Objects.equals(this.requestId, fraudVerification.requestId) &&
        Objects.equals(this.verdict, fraudVerification.verdict) &&
        Objects.equals(this.riskScore, fraudVerification.riskScore) &&
        Objects.equals(this.aiGeneratedLikelihood, fraudVerification.aiGeneratedLikelihood) &&
        Objects.equals(this.policyAction, fraudVerification.policyAction) &&
        Objects.equals(this.pipelineVersion, fraudVerification.pipelineVersion) &&
        Objects.equals(this.reused, fraudVerification.reused) &&
        Objects.equals(this.signals, fraudVerification.signals) &&
        Objects.equals(this.checks, fraudVerification.checks) &&
        Objects.equals(this.failedCoverage, fraudVerification.failedCoverage);
  }

  @Override
  public int hashCode() {
    return Objects.hash(requestId, verdict, riskScore, aiGeneratedLikelihood, policyAction, pipelineVersion, reused, signals, checks, failedCoverage);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FraudVerification {\n");
    sb.append("    requestId: ").append(toIndentedString(requestId)).append("\n");
    sb.append("    verdict: ").append(toIndentedString(verdict)).append("\n");
    sb.append("    riskScore: ").append(toIndentedString(riskScore)).append("\n");
    sb.append("    aiGeneratedLikelihood: ").append(toIndentedString(aiGeneratedLikelihood)).append("\n");
    sb.append("    policyAction: ").append(toIndentedString(policyAction)).append("\n");
    sb.append("    pipelineVersion: ").append(toIndentedString(pipelineVersion)).append("\n");
    sb.append("    reused: ").append(toIndentedString(reused)).append("\n");
    sb.append("    signals: ").append(toIndentedString(signals)).append("\n");
    sb.append("    checks: ").append(toIndentedString(checks)).append("\n");
    sb.append("    failedCoverage: ").append(toIndentedString(failedCoverage)).append("\n");
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

    // add `requestId` to the URL query string
    if (getRequestId() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%srequestId%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getRequestId()))));
    }

    // add `verdict` to the URL query string
    if (getVerdict() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sverdict%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getVerdict()))));
    }

    // add `riskScore` to the URL query string
    if (getRiskScore() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sriskScore%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getRiskScore()))));
    }

    // add `aiGeneratedLikelihood` to the URL query string
    if (getAiGeneratedLikelihood() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%saiGeneratedLikelihood%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getAiGeneratedLikelihood()))));
    }

    // add `policyAction` to the URL query string
    if (getPolicyAction() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%spolicyAction%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getPolicyAction()))));
    }

    // add `pipelineVersion` to the URL query string
    if (getPipelineVersion() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%spipelineVersion%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getPipelineVersion()))));
    }

    // add `reused` to the URL query string
    if (getReused() != null) {
      joiner.add(String.format(java.util.Locale.ROOT, "%sreused%s=%s", prefix, suffix, ApiClient.urlEncode(ApiClient.valueToString(getReused()))));
    }

    // add `signals` to the URL query string
    if (getSignals() != null) {
      for (int i = 0; i < getSignals().size(); i++) {
        if (getSignals().get(i) != null) {
          joiner.add(getSignals().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%ssignals%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    // add `checks` to the URL query string
    if (getChecks() != null) {
      for (int i = 0; i < getChecks().size(); i++) {
        if (getChecks().get(i) != null) {
          joiner.add(getChecks().get(i).toUrlQueryString(String.format(java.util.Locale.ROOT, "%schecks%s%s", prefix, suffix,
          "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix))));
        }
      }
    }

    // add `failedCoverage` to the URL query string
    if (getFailedCoverage() != null) {
      for (int i = 0; i < getFailedCoverage().size(); i++) {
        joiner.add(String.format(java.util.Locale.ROOT, "%sfailedCoverage%s%s=%s", prefix, suffix,
            "".equals(suffix) ? "" : String.format(java.util.Locale.ROOT, "%s%d%s", containerPrefix, i, containerSuffix),
            ApiClient.urlEncode(ApiClient.valueToString(getFailedCoverage().get(i)))));
      }
    }

    return joiner.toString();
  }
}
