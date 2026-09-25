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
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Cogneris.DocumentAI.Model;
using System.Runtime.CompilerServices;
using System.Net.Http.Headers;

[assembly: InternalsVisibleTo("Cogneris.DocumentAI.Test")]

namespace Cogneris.DocumentAI.Client
{
    /// <summary>
    /// Utility functions providing some benefit to API client consumers.
    /// </summary>
    public static partial class ClientUtils
    {

        /// <summary>
        /// A delegate for events.
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        /// <returns></returns>
        public delegate void EventHandler<T>(object sender, T e) where T : EventArgs;

        /// <summary>
        /// Returns true when deserialization succeeds.
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="json"></param>
        /// <param name="options"></param>
        /// <param name="result"></param>
        /// <returns></returns>
        public static bool TryDeserialize<T>(string json, JsonSerializerOptions options, [global::System.Diagnostics.CodeAnalysis.NotNullWhen(true)] out T? result)
        {
            try
            {
                result = JsonSerializer.Deserialize<T>(json, options);
                return result != null;
            }
            catch (Exception)
            {
                result = default;
                return false;
            }
        }

        /// <summary>
        /// Returns true when deserialization succeeds.
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="reader"></param>
        /// <param name="options"></param>
        /// <param name="result"></param>
        /// <returns></returns>
        public static bool TryDeserialize<T>(ref Utf8JsonReader reader, JsonSerializerOptions options, [global::System.Diagnostics.CodeAnalysis.NotNullWhen(true)] out T? result)
        {
            try
            {
                result = JsonSerializer.Deserialize<T>(ref reader, options);
                return result != null;
            }
            catch (Exception)
            {
                result = default;
                return false;
            }
        }

        /// <summary>
        /// If parameter is DateTime, output in a formatted string (default ISO 8601), customizable with Configuration.DateTime.
        /// If parameter is a list, join the list with ",".
        /// Otherwise just return the string.
        /// </summary>
        /// <param name="obj">The parameter (header, path, query, form).</param>
        /// <param name="format">The DateTime serialization format.</param>
        /// <returns>Formatted string.</returns>
        public static string? ParameterToString(object? obj, string? format = ISO8601_DATETIME_FORMAT)
        {
            if (obj is DateTime dateTime)
                // Return a formatted date string - Can be customized with Configuration.DateTimeFormat
                // Defaults to an ISO 8601, using the known as a Round-trip date/time pattern ("o")
                // https://msdn.microsoft.com/en-us/library/az4se3k1(v=vs.110).aspx#Anchor_8
                // For example: 2009-06-15T13:45:30.0000000
                return dateTime.ToString(format);
            if (obj is DateTimeOffset dateTimeOffset)
                // Return a formatted date string - Can be customized with Configuration.DateTimeFormat
                // Defaults to an ISO 8601, using the known as a Round-trip date/time pattern ("o")
                // https://msdn.microsoft.com/en-us/library/az4se3k1(v=vs.110).aspx#Anchor_8
                // For example: 2009-06-15T13:45:30.0000000
                return dateTimeOffset.ToString(format);
            if (obj is DateOnly dateOnly)
                return dateOnly.ToString(format);
            if (obj is bool boolean)
                return boolean
                    ? "true"
                    : "false";
            if (obj is DocumentJobOperation documentJobOperation)
                return DocumentJobOperationValueConverter.ToJsonValue(documentJobOperation);
            if (obj is DocumentJobStatus documentJobStatus)
                return DocumentJobStatusValueConverter.ToJsonValue(documentJobStatus);
            if (obj is DocumentJobSubmitOperation documentJobSubmitOperation)
                return DocumentJobSubmitOperationValueConverter.ToJsonValue(documentJobSubmitOperation);
            if (obj is DocumentJobSubmitStatus documentJobSubmitStatus)
                return DocumentJobSubmitStatusValueConverter.ToJsonValue(documentJobSubmitStatus);
            if (obj is PortalMagicLinkOptIn.SourceEnum portalMagicLinkOptInSourceEnum)
                return PortalMagicLinkOptIn.SourceEnumToJsonValue(portalMagicLinkOptInSourceEnum);
            if (obj is PortalSendChannel portalSendChannel)
                return PortalSendChannelValueConverter.ToJsonValue(portalSendChannel);
            if (obj is QualityVerdict qualityVerdict)
                return QualityVerdictValueConverter.ToJsonValue(qualityVerdict).ToString();
            if (obj is Template.StatusEnum templateStatusEnum)
                return Template.StatusEnumToJsonValue(templateStatusEnum);
            if (obj is WebhookEndpoint.VarEnvironmentEnum webhookEndpointVarEnvironmentEnum)
                return WebhookEndpoint.VarEnvironmentEnumToJsonValue(webhookEndpointVarEnvironmentEnum);
            if (obj is WebhookEvent webhookEvent)
                return WebhookEventValueConverter.ToJsonValue(webhookEvent);
            if (obj is ICollection collection)
            {
                List<string?> entries = new();
                foreach (var entry in collection)
                    entries.Add(ParameterToString(entry));
                return string.Join(",", entries);
            }

            return Convert.ToString(obj, System.Globalization.CultureInfo.InvariantCulture);
        }

        /// <summary>
        /// URL encode a string
        /// Credit/Ref: https://github.com/restsharp/RestSharp/blob/master/RestSharp/Extensions/StringExtensions.cs#L50
        /// </summary>
        /// <param name="input">string to be URL encoded</param>
        /// <returns>Byte array</returns>
        public static string UrlEncode(string input)
        {
            const int maxLength = 32766;

            if (input == null)
            {
                throw new ArgumentNullException("input");
            }

            if (input.Length <= maxLength)
            {
                return Uri.EscapeDataString(input);
            }

            StringBuilder sb = new StringBuilder(input.Length * 2);
            int index = 0;

            while (index < input.Length)
            {
                int length = Math.Min(input.Length - index, maxLength);
                string subString = input.Substring(index, length);

                sb.Append(Uri.EscapeDataString(subString));
                index += subString.Length;
            }

            return sb.ToString();
        }

        /// <summary>
        /// Encode string in base64 format.
        /// </summary>
        /// <param name="text">string to be encoded.</param>
        /// <returns>Encoded string.</returns>
        public static string Base64Encode(string text)
        {
            return Convert.ToBase64String(global::System.Text.Encoding.UTF8.GetBytes(text));
        }

        /// <summary>
        /// Convert stream to byte array
        /// </summary>
        /// <param name="inputStream">Input stream to be converted</param>
        /// <returns>Byte array</returns>
        public static byte[] ReadAsBytes(Stream inputStream)
        {
            using (var ms = new MemoryStream())
            {
                inputStream.CopyTo(ms);
                return ms.ToArray();
            }
        }

        /// <summary>
        /// Select the Content-Type header's value from the given content-type array:
        /// if JSON type exists in the given array, use it;
        /// otherwise use the first one defined in 'consumes'
        /// </summary>
        /// <param name="contentTypes">The Content-Type array to select from.</param>
        /// <returns>The Content-Type header to use.</returns>
        public static string? SelectHeaderContentType(string[] contentTypes)
        {
            if (contentTypes.Length == 0)
                return null;

            foreach (var contentType in contentTypes)
            {
                if (IsJsonMime(contentType))
                    return contentType;
            }

            return contentTypes[0]; // use the first content type specified in 'consumes'
        }

        /// <summary>
        /// Select the Accept header's value from the given accepts array:
        /// if JSON exists in the given array, use it;
        /// otherwise use all of them (joining into a string)
        /// </summary>
        /// <param name="accepts">The accepts array to select from.</param>
        /// <returns>The Accept header to use.</returns>
        public static string? SelectHeaderAccept(string[] accepts)
        {
            if (accepts.Length == 0)
                return null;

            if (accepts.Contains("application/json", StringComparer.OrdinalIgnoreCase))
                return "application/json";

            return string.Join(",", accepts);
        }



        /// <summary>
        /// Select the Accept header's value from the given accepts array:
        /// if JSON exists in the given array, use it;
        /// otherwise use all of them.
        /// </summary>
        /// <param name="accepts">The accepts array to select from.</param>
        /// <returns>The Accept header values to use.</returns>
        public static IEnumerable<MediaTypeWithQualityHeaderValue> SelectHeaderAcceptArray(string[] accepts)
        {
            if (accepts.Length == 0)
                    return [];

            if (accepts.Contains("application/json", StringComparer.OrdinalIgnoreCase))
                    return [MediaTypeWithQualityHeaderValue.Parse("application/json")];

            return accepts.Select(MediaTypeWithQualityHeaderValue.Parse);
        }

        /// <summary>
        /// Provides a case-insensitive check that a provided content type is a known JSON-like content type.
        /// </summary>
        [GeneratedRegex("(?i)^(application/json|[^;/ \t]+/[^;/ \t]+[+]json)[ \t]*(;.*)?$")]
        private static partial Regex JsonRegex();

        /// <summary>
        /// Check if the given MIME is a JSON MIME.
        /// JSON MIME examples:
        ///    application/json
        ///    application/json; charset=UTF8
        ///    APPLICATION/JSON
        ///    application/vnd.company+json
        /// </summary>
        /// <param name="mime">MIME</param>
        /// <returns>Returns True if MIME type is json.</returns>
        public static bool IsJsonMime(string mime)
        {
            if (string.IsNullOrWhiteSpace(mime)) return false;

            return JsonRegex().IsMatch(mime) || mime.Equals("application/json-patch+json");
        }

        /// <summary>
        /// Get the discriminator
        /// </summary>
        /// <param name="utf8JsonReader"></param>
        /// <param name="discriminator"></param>
        /// <returns></returns>
        /// <exception cref="JsonException"></exception>
        public static string? GetDiscriminator(Utf8JsonReader utf8JsonReader, string discriminator)
        {
            int currentDepth = utf8JsonReader.CurrentDepth;

            if (utf8JsonReader.TokenType != JsonTokenType.StartObject && utf8JsonReader.TokenType != JsonTokenType.StartArray)
                throw new JsonException();

            JsonTokenType startingTokenType = utf8JsonReader.TokenType;

            while (utf8JsonReader.Read())
            {
                if (startingTokenType == JsonTokenType.StartObject && utf8JsonReader.TokenType == JsonTokenType.EndObject && currentDepth == utf8JsonReader.CurrentDepth)
                    break;

                if (startingTokenType == JsonTokenType.StartArray && utf8JsonReader.TokenType == JsonTokenType.EndArray && currentDepth == utf8JsonReader.CurrentDepth)
                    break;

                if (utf8JsonReader.TokenType == JsonTokenType.PropertyName && currentDepth == utf8JsonReader.CurrentDepth - 1)
                {
                    string? localVarJsonPropertyName = utf8JsonReader.GetString();
                    utf8JsonReader.Read();

                    if (localVarJsonPropertyName != null && localVarJsonPropertyName.Equals(discriminator))
                        return utf8JsonReader.GetString();
                }
            }

            throw new JsonException("The specified discriminator was not found.");
        }

        /// <summary>
        /// Determines if the provided header is a content header
        /// </summary>
        /// <param name="header">The header to check</param>
        /// <returns>True if a content header; False otherwise</returns>
        public static bool IsContentHeader(string header)
        {
            return ContentHeaders.Contains(header.ToLowerInvariant());
        }

        /// <summary>
        /// The collection of content headers as per
        /// https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpcontent.headers
        /// </summary>
        private static readonly string[] ContentHeaders = new String[]
        {
            "allow",
            "content-encoding",
            "content-disposition",
            "content-language",
            "content-length",
            "content-location",
            "content-md5",
            "content-range",
            "content-type",
            "expires",
            "last-modified"
        };

        /// <summary>
        /// The base path of the API
        /// </summary>
        public const string BASE_ADDRESS = "https://api-us.cogneris.ai";

        /// <summary>
        /// The scheme of the API
        /// </summary>
        public const string SCHEME = "https";

        /// <summary>
        /// The context path of the API
        /// </summary>
        public const string CONTEXT_PATH = "";

        /// <summary>
        /// The host of the API
        /// </summary>
        public const string HOST = "api-us.cogneris.ai";

        /// <summary>
        /// The format to use for DateTime serialization
        /// </summary>
        public const string ISO8601_DATETIME_FORMAT = "o";
    }
}
