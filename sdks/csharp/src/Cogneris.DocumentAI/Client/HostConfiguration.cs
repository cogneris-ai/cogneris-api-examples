/*
 * Cogneris Document AI API
 *
 * The Cogneris Document AI API turns unstructured documents — PDFs, images, scans — into structured JSON.  This document describes the endpoints that are actually deployed. It is written from the running service (`cogneris-api-be`) rather than from a design, so what is listed here is what you can call.  ## Authentication  Every endpoint takes an API key in the `Authorization` header as `Bearer <key>`. Keys begin with `xtkt_live_` (production) or `xtkt_test_` (sandbox); either prefix is accepted before the key is looked up for validation. The key selects the application environment. A recognized prefix alone does not authenticate a request: the key must also be valid and active. Keys are tenant-scoped and cannot cross tenant boundaries. Mint them in the dashboard under **Settings → API keys**.  ## Uploads  The synchronous document endpoints take `multipart/form-data`. There is no fetch-by-URL variant — the file travels in the request body.  - Accepted extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`,   `.bmp`, `.doc`, `.docx` - Maximum size: 10 MB per file, except `/Document/split`, which accepts 500 MB  The asynchronous job endpoints do not take a file. Upload it first to `POST /api/v1/artifacts` — same extensions, same 10 MB limit — and submit the `artifact://` reference it returns.  ## Artifact references  A reference names one stored object. `POST /api/v1/artifacts` returns one, a job submit consumes one as `inputReference`, and a finished job returns one as `outputReference`. `GET /api/v1/artifacts/content` turns either back into bytes.  - References are scoped to the tenant that created them. One belonging to another   tenant is refused as an invalid reference — the answer does not distinguish a   reference that exists elsewhere from one that never existed. - An uploaded reference is **reusable**: one upload can back several jobs. - It expires **7 days** after upload, matching how long a job is retained. The   exact instant is returned as `expiresAt`. Reading it afterwards answers `410`,   which is not `404` — the reference was real, it aged out, and re-requesting it   will never succeed. Upload again. - A job's `outputReference` lives as long as the job does.  ### Two shapes, one of them historical  Everything this API produces today is `artifact://<key>`. Jobs that completed before 2026-09-22 carry a bucket-qualified path instead — `<bucket>/<tenant>/document-jobs/<jobId>/result.json`, sometimes with an `@<version>` suffix. `GET /api/v1/artifacts/content` accepts both, so a reference stored from an older job still resolves for the rest of its life. Treat a reference as opaque: pass back exactly what you were given.  ## Templates  Extraction and classification are driven by the document types and templates configured for your tenant. The platform selects the template from the document itself, so the synchronous `/Document/_*` calls take no template or schema parameter. Use `GET /api/v1/templates` to list the finished templates available to your key before naming one explicitly with `templateId` on `POST /api/v1/document-jobs`. The list is cursor-paginated; pass its `nextCursor` as `cursor` to read the next page.  ## Scopes  Keys carry scopes. The Portal and webhook-endpoint routes check them and answer `403` when the required one is absent; the document endpoints accept any valid key for the tenant without consulting the list. `*` is a real scope meaning full access, and it is what a key receives when it is created without an explicit scope list.  ## Webhooks  A finished asynchronous job can announce itself, so you do not have to poll it. Register an HTTPS endpoint with `POST /api/v1/webhook-endpoints` and it receives a signed `POST` when a job you subscribed to succeeds, fails or is cancelled. The webhook **announces** the result and does not carry it: read the bytes with `GET /api/v1/artifacts/content?reference=<OutputReference>`.  Endpoints are managed with a **production** key holding `webhooks.manage` (or `*`). An endpoint receives your whole account's production events for the events it subscribes to, and events from sandbox jobs are never delivered, so a sandbox key is refused.  Each delivery carries three headers:  - `X-Xtrakt-Event` — the event name, such as `extract.processed`. - `X-Xtrakt-Delivery` — a fresh id per send. It is not a deduplication key. - `X-Xtrakt-Signature` — `t=<unix seconds>,v1=<hex>`, where `v1` is the   HMAC-SHA256 of `<t>.<raw body>` keyed with the endpoint's `whsec_` secret.   Recompute it over the raw bytes, compare in constant time, and reject a `t`   outside your tolerance.  For a job, the body is the job's terminal state. **Its property names are PascalCase**, unlike the rest of this API:  ```json {\"JobId\":\"7c9e6679-7425-40de-944b-e07fc1f90ae7\",\"Operation\":\"Extraction\",  \"Status\":\"succeeded\",\"OutputReference\":\"artifact://document-jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7/result.json\",  \"Stage\":null,\"ProcessedPages\":null,\"TotalPages\":null,\"FailureCode\":null,  \"AttemptCount\":1,\"CompletedAt\":\"2026-09-23T14:02:11.482Z\"} ```  `Status` is `succeeded`, `failed` or `cancelled`, and a cancelled job sends the `.failed` event. `OutputReference` is null unless the job succeeded, and always null for `Redaction`. The synchronous `/Document/_*` calls fire the same event names with their own response as the body; a delivery about a job is the one that has `JobId`. An endpoint with a `body` sends that fixed text **instead of** the payload.  Delivery semantics:  - **A job's outcome never depends on its webhook.** A job that succeeded stays   succeeded when the delivery fails; `GET /api/v1/document-jobs/{jobId}` is the   source of truth. - **One attempt per endpoint, no retry.** A timeout or a non-2xx answer is   recorded and not sent again. Answer `2xx` fast and do the work afterwards, and   reconcile periodically with `GET /api/v1/document-jobs`. - **Duplicates are rare but possible.** Deduplicate on `JobId` plus the event. - Every delivery attempt is metered as webhook usage, successful or not.  ## Rate limits  One shared policy covers every surface in this document, Portal included: **50 requests per API key per fixed 1-minute window**. It is a fixed window rather than a token bucket, so the allowance resets on the minute instead of refilling gradually. Requests over the limit receive `429`.  ## Response envelope  Successful responses from the **document, job and webhook-endpoint** routes share one wrapper: `data` for the payload, `meta` for the status and any messages, and `hasErrors` for a fast failure check. The webhook-endpoint routes send their **errors** as problem documents, described next.  The **Portal** endpoints do not use that wrapper. They return the payload directly, and their errors are RFC 9457 problem documents sent as `application/problem+json`, with a stable `code`, a `correlationId` that is also returned in the `x-correlation-id` header, and a `retryable` flag. Branch on `code`; treat `type` as an opaque identifier.  ## Errors  An error arrives in one of two shapes, and the `Content-Type` says which.  - `application/problem+json` — an RFC 9457 problem document, the same one the   Portal uses. Every route answers this way when the failure happens before your   request is processed: a missing or invalid key (`401`), the rate limit (`429`),   a request refused as malformed or unsafe (`400`), or an unexpected failure   (`500`). - `application/json` — the service envelope with `hasErrors: true` and the   reasons in `meta.errors`. The document, job and artifact routes answer this way   when processing itself fails. Each operation lists the statuses where it does.  Every operation lists `400`, `401`, `403`, `404`, `409`, `429` and `500`, because the API answers each of them in the same shape wherever it occurs. A status on an operation with nothing to miss or conflict with — a `409` on a read, say — is part of that uniform model and not something the operation returns in practice.
 *
 * The version of the OpenAPI document: 2026-09-24
 * Generated by: https://github.com/openapitools/openapi-generator.git
 */

#nullable enable

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Cogneris.DocumentAI.Api;
using Cogneris.DocumentAI.Model;

namespace Cogneris.DocumentAI.Client
{
    /// <summary>
    /// Provides hosting configuration for Cogneris.DocumentAI
    /// </summary>
    public partial class HostConfiguration
    {
        private readonly IServiceCollection _services;
        private readonly JsonSerializerOptions _jsonOptions = new JsonSerializerOptions();

        internal bool HttpClientsAdded { get; private set; }

        /// <summary>
        /// Instantiates the class
        /// </summary>
        /// <param name="services"></param>
        public HostConfiguration(IServiceCollection services)
        {
            _services = services;
            _jsonOptions.Converters.Add(new JsonStringEnumConverter());
            _jsonOptions.Converters.Add(new DateTimeJsonConverter());
            _jsonOptions.Converters.Add(new DateTimeNullableJsonConverter());
            _jsonOptions.Converters.Add(new DateOnlyJsonConverter());
            _jsonOptions.Converters.Add(new DateOnlyNullableJsonConverter());
            _jsonOptions.Converters.Add(new ApiErrorJsonConverter());
            _jsonOptions.Converters.Add(new ArtifactJsonConverter());
            _jsonOptions.Converters.Add(new ArtifactUploadEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new ClassificationResultJsonConverter());
            _jsonOptions.Converters.Add(new CropDocumentJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobCancellationJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobCancellationEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobListJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobListEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobOperationJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobOperationNullableJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobStatusJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobStatusNullableJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmissionJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmissionEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmitOperationJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmitOperationNullableJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmitStatusJsonConverter());
            _jsonOptions.Converters.Add(new DocumentJobSubmitStatusNullableJsonConverter());
            _jsonOptions.Converters.Add(new EnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new EnvelopeDataJsonConverter());
            _jsonOptions.Converters.Add(new ExtractedFieldJsonConverter());
            _jsonOptions.Converters.Add(new FaceExtractionJsonConverter());
            _jsonOptions.Converters.Add(new FaceMatchJsonConverter());
            _jsonOptions.Converters.Add(new PortalChannelsJsonConverter());
            _jsonOptions.Converters.Add(new PortalFormJsonConverter());
            _jsonOptions.Converters.Add(new PortalMagicLinkJsonConverter());
            _jsonOptions.Converters.Add(new PortalMagicLinkOptInJsonConverter());
            _jsonOptions.Converters.Add(new PortalMagicLinkRequestJsonConverter());
            _jsonOptions.Converters.Add(new PortalSendChannelJsonConverter());
            _jsonOptions.Converters.Add(new PortalSendChannelNullableJsonConverter());
            _jsonOptions.Converters.Add(new ProblemDetailsJsonConverter());
            _jsonOptions.Converters.Add(new ProblemDetailsErrorsInnerJsonConverter());
            _jsonOptions.Converters.Add(new QualityAssessmentJsonConverter());
            _jsonOptions.Converters.Add(new QualityFindingJsonConverter());
            _jsonOptions.Converters.Add(new QualityVerdictJsonConverter());
            _jsonOptions.Converters.Add(new QualityVerdictNullableJsonConverter());
            _jsonOptions.Converters.Add(new ServiceErrorEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new ServiceResponseMetaJsonConverter());
            _jsonOptions.Converters.Add(new SubmitDocumentJobRequestJsonConverter());
            _jsonOptions.Converters.Add(new TemplateJsonConverter());
            _jsonOptions.Converters.Add(new TemplateListJsonConverter());
            _jsonOptions.Converters.Add(new TemplateListEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointCreateRequestJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointCreatedJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointCreatedEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointDeletionJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointDeletionEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointListJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointListEnvelopeJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEndpointUpdateRequestJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEventJsonConverter());
            _jsonOptions.Converters.Add(new WebhookEventNullableJsonConverter());
            JsonSerializerOptionsProvider jsonSerializerOptionsProvider = new(_jsonOptions);
            _services.AddSingleton(jsonSerializerOptionsProvider);
            _services.AddSingleton<IApiFactory, ApiFactory>();
            _services.AddSingleton<ArtifactsApiEvents>();
            _services.AddSingleton<DocumentsApiEvents>();
            _services.AddSingleton<JobsApiEvents>();
            _services.AddSingleton<PortalApiEvents>();
            _services.AddSingleton<TemplatesApiEvents>();
            _services.AddSingleton<WebhooksApiEvents>();
            OnHostConfigurationCreated();
        }

        /// <summary>
        /// Configures the HttpClients.
        /// </summary>
        /// <param name="builder"></param>
        /// <returns></returns>
        public HostConfiguration AddApiHttpClients(Action<IHttpClientBuilder>? builder = null)
        {
            return AddApiHttpClients((Action<IServiceProvider, HttpClient>?)null, builder);
        }

        /// <summary>
        /// Configures the HttpClients.
        /// </summary>
        /// <param name="client"></param>
        /// <param name="builder"></param>
        /// <returns></returns>
        public HostConfiguration AddApiHttpClients(
            Action<HttpClient>? client,
            Action<IHttpClientBuilder>? builder = null)
        {
            var wrapped = client != null ? new Action<IServiceProvider, HttpClient>((_, httpClient) =>
            {
                client(httpClient);
            }) : null;
            return AddApiHttpClients(wrapped, builder);
        }

        /// <summary>
        /// Configures the HttpClients.
        /// </summary>
        /// <param name="client"></param>
        /// <param name="builder"></param>
        /// <returns></returns>
        public HostConfiguration AddApiHttpClients(
            Action<IServiceProvider, HttpClient>? client,
            Action<IHttpClientBuilder>? builder = null)
        {
            if (client == null)
                client = (_, c) => c.BaseAddress = new Uri(ClientUtils.BASE_ADDRESS);

            List<IHttpClientBuilder> builders = new List<IHttpClientBuilder>();

            builders.Add(_services.AddHttpClient<IArtifactsApi, ArtifactsApi>("Cogneris.DocumentAI.Api.IArtifactsApi", client));
            builders.Add(_services.AddHttpClient<IDocumentsApi, DocumentsApi>("Cogneris.DocumentAI.Api.IDocumentsApi", client));
            builders.Add(_services.AddHttpClient<IJobsApi, JobsApi>("Cogneris.DocumentAI.Api.IJobsApi", client));
            builders.Add(_services.AddHttpClient<IPortalApi, PortalApi>("Cogneris.DocumentAI.Api.IPortalApi", client));
            builders.Add(_services.AddHttpClient<ITemplatesApi, TemplatesApi>("Cogneris.DocumentAI.Api.ITemplatesApi", client));
            builders.Add(_services.AddHttpClient<IWebhooksApi, WebhooksApi>("Cogneris.DocumentAI.Api.IWebhooksApi", client));

            foreach (IHttpClientBuilder instance in builders)
            {
                bool suppressDefault = false;
                OnAddApiHttpClientBuilder(instance, builder, ref suppressDefault);
                if (!suppressDefault)
                    builder?.Invoke(instance);
            }

            HttpClientsAdded = true;

            return this;
        }

        /// <summary>
        /// Applies configuration to each HttpClient.
        /// Implement this partial method to prepend configuration, invoke <paramref name="userBuilder"/> at the
        /// desired position, and append further configuration. Set <paramref name="suppressDefault"/> to
        /// <c>true</c> when you invoke <paramref name="userBuilder"/> yourself to prevent a second invocation,
        /// or to ignore the user's builder entirely.
        /// If this method is not implemented, <paramref name="userBuilder"/> is invoked automatically.
        /// </summary>
        /// <param name="builder">The <see cref="IHttpClientBuilder"/> to configure.</param>
        /// <param name="userBuilder">The caller-supplied builder action, or <c>null</c> if none was provided.</param>
        /// <param name="suppressDefault">Set to <c>true</c> to prevent the default invocation of <paramref name="userBuilder"/>.</param>
        partial void OnAddApiHttpClientBuilder(IHttpClientBuilder builder, Action<IHttpClientBuilder>? userBuilder, ref bool suppressDefault);

        /// <summary>
        /// Called at the end of the constructor after all JSON converters and services are registered.
        /// Implement this partial method to further configure <c>_jsonOptions</c> or register additional singletons via <c>_services</c>.
        /// </summary>
        partial void OnHostConfigurationCreated();

        /// <summary>
        /// Called after all services have been registered.
        /// Implement this partial method to register additional services.
        /// </summary>
        /// <param name="services"></param>
        partial void OnServicesAdded(IServiceCollection services);

        internal void NotifyServicesAdded(IServiceCollection services) => OnServicesAdded(services);

        /// <summary>
        /// Configures the JsonSerializerSettings
        /// </summary>
        /// <param name="options"></param>
        /// <returns></returns>
        public HostConfiguration ConfigureJsonOptions(Action<JsonSerializerOptions> options)
        {
            options(_jsonOptions);

            return this;
        }

        /// <summary>
        /// Adds tokens to your IServiceCollection
        /// </summary>
        /// <typeparam name="TTokenBase"></typeparam>
        /// <param name="token"></param>
        /// <returns></returns>
        public HostConfiguration AddTokens<TTokenBase>(TTokenBase token) where TTokenBase : TokenBase
        {
            return AddTokens(new TTokenBase[]{ token });
        }

        /// <summary>
        /// Adds tokens to your IServiceCollection
        /// </summary>
        /// <typeparam name="TTokenBase"></typeparam>
        /// <param name="tokens"></param>
        /// <returns></returns>
        public HostConfiguration AddTokens<TTokenBase>(IEnumerable<TTokenBase> tokens) where TTokenBase : TokenBase
        {
            TokenContainer<TTokenBase> container = new TokenContainer<TTokenBase>(tokens);
            _services.AddSingleton(services => container);

            return this;
        }

        /// <summary>
        /// Adds a token provider to your IServiceCollection
        /// </summary>
        /// <typeparam name="TTokenProvider"></typeparam>
        /// <typeparam name="TTokenBase"></typeparam>
        /// <returns></returns>
        public HostConfiguration UseProvider<TTokenProvider, TTokenBase>()
            where TTokenProvider : TokenProvider<TTokenBase>
            where TTokenBase : TokenBase
        {
            _services.AddSingleton<TTokenProvider>();
            _services.AddSingleton<TokenProvider<TTokenBase>>(services => services.GetRequiredService<TTokenProvider>());

            return this;
        }
    }
}
