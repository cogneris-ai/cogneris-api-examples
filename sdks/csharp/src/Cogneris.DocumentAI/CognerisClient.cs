using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Cogneris.DocumentAI.Api;
using Cogneris.DocumentAI.Client;
using Cogneris.DocumentAI.Extensions;
using Cogneris.DocumentAI.Model;
using Microsoft.Extensions.DependencyInjection;

namespace Cogneris.DocumentAI;

/// <summary>The supported public API regions.</summary>
public enum CognerisRegion
{
    /// <summary>United States.</summary>
    Us,
    /// <summary>European Union.</summary>
    Eu
}

/// <summary>Authentication, region, and an optional loopback-only test endpoint.</summary>
/// <param name="ApiKey">The tenant's API key.</param>
/// <param name="Region">The public API region.</param>
/// <param name="BaseUriForTesting">An HTTP(S) URI restricted to localhost, 127.0.0.1, or ::1.</param>
public sealed record CognerisClientOptions(
    string ApiKey,
    CognerisRegion Region = CognerisRegion.Us,
    Uri? BaseUriForTesting = null);

/// <summary>Document workflows implemented through the generated operations and models.</summary>
public sealed class CognerisClient : IAsyncDisposable
{
    private readonly ServiceProvider services;
    private readonly IDocumentsApi documents;
    private readonly IJobsApi jobs;
    private readonly List<HttpClient> httpClients = new();
    private readonly ConcurrentDictionary<Guid, TimeSpan> submitHints = new();

    /// <summary>Creates a client for the selected public API region.</summary>
    public CognerisClient(CognerisClientOptions options)
    {
        ArgumentNullException.ThrowIfNull(options);
        if (string.IsNullOrWhiteSpace(options.ApiKey))
            throw new ArgumentException("An API key is required.", nameof(options));
        var baseUri = options.Region switch
        {
            CognerisRegion.Us => new Uri("https://api-us.cogneris.ai"),
            CognerisRegion.Eu => new Uri("https://api-eu.cogneris.ai"),
            _ => throw new ArgumentOutOfRangeException(nameof(options), "Unsupported API region.")
        };
        if (options.BaseUriForTesting is { } testUri)
        {
            if (!testUri.IsAbsoluteUri ||
                (testUri.Scheme != Uri.UriSchemeHttp && testUri.Scheme != Uri.UriSchemeHttps) ||
                (testUri.IdnHost != "localhost" && testUri.IdnHost != "127.0.0.1" && testUri.IdnHost != "::1") ||
                testUri.UserInfo.Length != 0 || testUri.Query.Length != 0 || testUri.Fragment.Length != 0)
                throw new ArgumentException("The test endpoint must be a loopback HTTP(S) URI without credentials, query, or fragment.", nameof(options));
            baseUri = testUri;
        }

        var collection = new ServiceCollection();
        var token = new BearerToken(options.ApiKey);
        // The generated default token provider starts an undisposable periodic
        // timer. This provider leaves all polling delays to this facade.
        collection.AddSingleton<TokenProvider<BearerToken>>(new SingleTokenProvider(token));
        collection.AddApi(configuration => configuration.AddTokens(token).AddApiHttpClients(client =>
        {
            client.BaseAddress = baseUri;
            httpClients.Add(client);
        }, builder => builder.ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler { AllowAutoRedirect = false })));
        services = collection.BuildServiceProvider();
        documents = services.GetRequiredService<IDocumentsApi>();
        jobs = services.GetRequiredService<IJobsApi>();
    }

    /// <summary>Uploads a document for extraction. The generated operation disposes the supplied stream.</summary>
    public async Task<Envelope> ExtractAsync(
        Stream content, string fileName, string? contentType = null,
        string? complementaryPrompt = null, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(content);
        var response = await SendAsync(() => documents.ExtractDocumentAsync(
            new FileParameter(content, fileName, contentType ?? "application/octet-stream"),
            complementaryPrompt is null ? default : new Option<string>(complementaryPrompt), cancellationToken), cancellationToken).ConfigureAwait(false);
        if (!response.IsOk) throw new CognerisApiException(response.StatusCode);
        return Parse(() =>
        {
            var envelope = response.Ok();
            if (envelope is null || envelope.HasErrors == true || envelope.Data is null)
                throw new CognerisResponseException();
            return envelope;
        });
    }

    /// <summary>Submits a job referencing an already uploaded artifact.</summary>
    public async Task<DocumentJobSubmission> SubmitJobAsync(
        DocumentJobSubmitOperation operation, string inputReference,
        CancellationToken cancellationToken = default)
    {
        var response = await SendAsync(() => jobs.SubmitDocumentJobAsync(
            new SubmitDocumentJobRequest(operation, inputReference), cancellationToken), cancellationToken).ConfigureAwait(false);
        if (!response.IsAccepted) throw new CognerisApiException(response.StatusCode);
        var submission = Parse(() =>
        {
            var envelope = response.Accepted();
            if (envelope is null || envelope.HasErrors || envelope.Data is null)
                throw new CognerisResponseException();
            return envelope.Data;
        });
        var hint = RetryAfter(response) ?? (submission.RetryAfterSeconds >= 0
            ? TimeSpan.FromSeconds(submission.RetryAfterSeconds) : (TimeSpan?)null);
        if (hint is { } delay) submitHints[submission.JobId] = delay;
        return submission;
    }

    /// <summary>Retrieves a job's current state.</summary>
    public async Task<DocumentJob> GetJobAsync(Guid jobId, CancellationToken cancellationToken = default)
    {
        var (job, _) = await GetJobResponseAsync(jobId, cancellationToken).ConfigureAwait(false);
        return job;
    }

    /// <summary>Polls within an attempt bound, honoring integer Retry-After hints and cancellation.</summary>
    public async Task<DocumentJob> WaitForJobAsync(
        Guid jobId, int maxAttempts = 20, TimeSpan? pollInterval = null,
        CancellationToken cancellationToken = default)
    {
        if (maxAttempts < 1)
            throw new ArgumentOutOfRangeException(nameof(maxAttempts), "The attempt bound must be positive.");
        var interval = pollInterval ?? TimeSpan.FromSeconds(1);
        if (interval < TimeSpan.Zero)
            throw new ArgumentOutOfRangeException(nameof(pollInterval), "The polling interval must be non-negative.");
        cancellationToken.ThrowIfCancellationRequested();
        if (submitHints.TryRemove(jobId, out var hint))
            await DelayAsync(hint, cancellationToken).ConfigureAwait(false);
        for (var attempt = 0; attempt < maxAttempts; attempt++)
        {
            var (job, retryAfter) = await GetJobResponseAsync(jobId, cancellationToken).ConfigureAwait(false);
            if (job.Status == DocumentJobStatus.Succeeded) return job;
            if (job.Status is DocumentJobStatus.Failed or DocumentJobStatus.Cancelled)
                throw new CognerisJobTerminalException(job.Status.Value);
            if (attempt < maxAttempts - 1)
                await DelayAsync(retryAfter ?? interval, cancellationToken).ConfigureAwait(false);
        }
        throw new CognerisMaxAttemptsException(maxAttempts);
    }

    /// <summary>Requests cancellation of a document job.</summary>
    public async Task<DocumentJobCancellation> CancelJobAsync(Guid jobId, CancellationToken cancellationToken = default)
    {
        var response = await SendAsync(() => jobs.CancelDocumentJobAsync(jobId, cancellationToken), cancellationToken).ConfigureAwait(false);
        if (!response.IsAccepted) throw new CognerisApiException(response.StatusCode);
        return Parse(() =>
        {
            var envelope = response.Accepted();
            if (envelope is null || envelope.HasErrors || envelope.Data is null)
                throw new CognerisResponseException();
            return envelope.Data;
        });
    }

    private async Task<(DocumentJob Job, TimeSpan? RetryAfter)> GetJobResponseAsync(Guid jobId, CancellationToken cancellationToken)
    {
        var response = await SendAsync(() => jobs.GetDocumentJobAsync(jobId, cancellationToken), cancellationToken).ConfigureAwait(false);
        if (!response.IsOk) throw new CognerisApiException(response.StatusCode);
        var job = Parse(() =>
        {
            var envelope = response.Ok();
            if (envelope is null || envelope.HasErrors || envelope.Data is null || envelope.Data.Status is null)
                throw new CognerisResponseException();
            return envelope.Data;
        });
        return (job, RetryAfter(response));
    }

    private static TimeSpan? RetryAfter(IApiResponse response)
    {
        if (response.Headers.TryGetValues("Retry-After", out var values))
            foreach (var value in values)
                if (int.TryParse(value, NumberStyles.None, CultureInfo.InvariantCulture, out var seconds) && seconds >= 0)
                    return TimeSpan.FromSeconds(seconds);
        return null;
    }

    private static async Task DelayAsync(TimeSpan delay, CancellationToken cancellationToken)
    {
        // Task.Delay limits a single timer to about 49 days. Chunk larger valid
        // hints/intervals while keeping cancellation effective throughout.
        var maximum = TimeSpan.FromMilliseconds(uint.MaxValue - 1);
        while (delay > maximum)
        {
            await Task.Delay(maximum, cancellationToken).ConfigureAwait(false);
            delay -= maximum;
        }
        await Task.Delay(delay, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<T> SendAsync<T>(Func<Task<T>> send, CancellationToken cancellationToken)
    {
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            return await send().ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw new OperationCanceledException("Cogneris API request was cancelled.", cancellationToken);
        }
        catch (Exception error) when (error is HttpRequestException or IOException or OperationCanceledException)
        {
            throw new CognerisTransportException();
        }
        catch (InvalidOperationException)
        {
            // Generated operations decode the response body before returning;
            // unsupported charsets can retain private header text in the cause.
            throw new CognerisResponseException();
        }
    }

    private static T Parse<T>(Func<T> parse)
    {
        try { return parse(); }
        catch (Exception error) when (error is JsonException or ArgumentException or InvalidOperationException or FormatException or OverflowException)
        {
            throw new CognerisResponseException();
        }
    }

    /// <summary>Releases the client's HTTP clients and dependency container.</summary>
    public async ValueTask DisposeAsync()
    {
        foreach (var client in httpClients) client.Dispose();
        submitHints.Clear();
        await services.DisposeAsync().ConfigureAwait(false);
    }

    private sealed class SingleTokenProvider : TokenProvider<BearerToken>
    {
        private readonly BearerToken token;
        internal SingleTokenProvider(BearerToken token) => this.token = token;
        protected internal override ValueTask<BearerToken> GetAsync(string header = "", CancellationToken cancellation = default)
        {
            cancellation.ThrowIfCancellationRequested();
            return ValueTask.FromResult(token);
        }
    }
}
