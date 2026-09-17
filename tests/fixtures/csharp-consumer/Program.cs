using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Cogneris.DocumentAI;
using Cogneris.DocumentAI.Model;

await Smoke.RunAsync();

static class Smoke
{
    const string Key = "xtkt_live_package_only_secret";
    const string Reflected = "reflected-private-payload";
    const string Document = "document-bytes";
    static readonly Guid JobId = Guid.Parse("2cabd780-7886-499c-a452-f4d609bd9b1e");

    public static async Task RunAsync()
    {
        var dll = typeof(CognerisClient).Assembly.Location;
        Check(dll.StartsWith(Environment.GetEnvironmentVariable("NUGET_PACKAGES")! + Path.DirectorySeparatorChar),
            "SDK assembly must load from the isolated NuGet cache");
        Console.WriteLine("Package assembly: " + dll);
        foreach (var test in new Func<Task>[] {
            Workflow, RetryHints, BoundedAndTerminal, Cancellation, SafeErrors, LoopbackSeam, TransportFailure })
        {
            await test();
            Console.WriteLine("PASS " + test.Method.Name);
        }
    }

    static CognerisClient Client(Loopback server) => new(new(Key, BaseUriForTesting: server.BaseUri));
    static string Envelope(object? data, bool hasErrors = false) => JsonSerializer.Serialize(new {
        data, meta = new { httpStatusCode = 200, messages = new[] { Reflected } }, hasErrors });
    static string Job(string status) => Envelope(new {
        jobId = JobId, operation = "Extraction", status, outputReference = "artifact://tenant/output/result",
        stage = "complete", processedPages = 1, totalPages = 1, attemptCount = 1,
        failureCode = Reflected, retryable = false, startedAt = "2026-09-17T12:00:00Z",
        completedAt = "2026-09-17T12:00:01Z", cancellationRequestedAt = (string?)null,
        expiresAt = "2026-09-18T12:00:00Z" });
    static string Submission(int hint = 0) => Envelope(new {
        jobId = JobId, status = "Queued", statusUrl = $"/api/v1/document-jobs/{JobId}", retryAfterSeconds = hint });

    static async Task Workflow()
    {
        await using var server = new Loopback(
            new(200, Envelope(new { id = JobId, metadata = new { identity = "123" }, createdDate = "2026-09-17T12:00:00Z" })),
            new(202, Submission(), "0"), new(200, Job("Queued"), "0"),
            new(200, Job("Processing"), "0"), new(200, Job("Succeeded")),
            new(202, Envelope(new { jobId = JobId, status = "Cancelled", cancellationRequested = true })));
        await using var client = Client(server);
        var extracted = await client.ExtractAsync(new MemoryStream(Encoding.UTF8.GetBytes(Document)),
            "identity.pdf", "application/pdf", "return id");
        Check(extracted.Data?.Id == JobId && extracted.HasErrors == false, "extraction must decode envelope");
        Check(extracted.Data?.Metadata?["identity"].ToString() == "123", "metadata must survive generated model");
        var submission = await client.SubmitJobAsync(DocumentJobSubmitOperation.Extraction, "artifact://tenant/input/reference");
        Check(submission.JobId == JobId, "submission must unwrap data");
        var completed = await client.WaitForJobAsync(submission.JobId, maxAttempts: 3, pollInterval: TimeSpan.Zero);
        Check(completed.Status == DocumentJobStatus.Succeeded && completed.OutputReference == "artifact://tenant/output/result",
            "polling must return terminal result data");
        var cancelled = await client.CancelJobAsync(submission.JobId);
        Check(cancelled.JobId == JobId && cancelled.CancellationRequested == true, "cancel must unwrap accepted data");
        var requests = server.Requests.ToArray();
        Check(requests.Length == 6, "workflow must use exactly six HTTP calls");
        Check(requests.All(r => r.Authorization == "Bearer " + Key), "every request must authenticate");
        Check(requests[0].Method == "POST" && requests[0].Path == "/Document/extraction", "extraction route");
        Check(requests[0].ContentType.StartsWith("multipart/form-data;"), "multipart transport");
        foreach (var part in new[] { "name=file", "filename=identity.pdf", "application/pdf", Document, "ComplementaryPrompt", "return id" })
            Check(requests[0].Body.Replace("\"", "").Contains(part), "missing multipart part: " + part);
        Check(requests[1].Method == "POST" && requests[1].Path == "/api/v1/document-jobs", "submit route");
        using var payload = JsonDocument.Parse(requests[1].Body);
        Check(payload.RootElement.GetProperty("operation").GetString() == "Extraction", "generated enum serialization");
        Check(payload.RootElement.GetProperty("inputReference").GetString() == "artifact://tenant/input/reference", "input reference");
        Check(requests.Skip(2).Take(3).All(r => r.Method == "GET" && r.Path == $"/api/v1/document-jobs/{JobId}"), "poll routes");
        Check(requests[5].Method == "POST" && requests[5].Path == $"/api/v1/document-jobs/{JobId}/cancel", "cancel route");
    }

    static async Task RetryHints()
    {
        // Header beats submit body, is consumed once, and delays the first GET.
        await using (var server = new Loopback(new(202, Submission(30), "1"), new(200, Job("Succeeded")), new(200, Job("Succeeded"))))
        await using (var client = Client(server))
        {
            await client.SubmitJobAsync(DocumentJobSubmitOperation.Extraction, "artifact://tenant/input/reference");
            var watch = Stopwatch.StartNew();
            await client.WaitForJobAsync(JobId, pollInterval: TimeSpan.Zero);
            Check(watch.Elapsed >= TimeSpan.FromMilliseconds(900), "submit Retry-After must delay first poll");
            using var deadline = new CancellationTokenSource(TimeSpan.FromMilliseconds(700));
            await client.WaitForJobAsync(JobId, pollInterval: TimeSpan.Zero, cancellationToken: deadline.Token);
            Check(server.Requests.Count == 3, "submit hint must be consumed once");
        }
        // Invalid headers fall back to the body hint, without accepting signed/fractional/date values.
        foreach (var hint in new[] { "-1", "+1", "0.5", "Thu, 17 Sep 2026 12:00:00 GMT", "999999999999999999999", "garbage" })
        {
            await using var server = new Loopback(new(202, Submission(1), hint), new(200, Job("Succeeded")));
            await using var client = Client(server);
            await client.SubmitJobAsync(DocumentJobSubmitOperation.Extraction, "artifact://tenant/input/reference");
            using var stop = new CancellationTokenSource(TimeSpan.FromMilliseconds(150));
            await Cancelled(() => client.WaitForJobAsync(JobId, pollInterval: TimeSpan.Zero, cancellationToken: stop.Token), stop.Token);
            Check(server.Requests.Count == 1, "invalid header must preserve non-negative body hint");
        }
        await using (var server = new Loopback(new(200, Job("Processing"), "1"), new(200, Job("Succeeded"))))
        await using (var client = Client(server))
        {
            var watch = Stopwatch.StartNew();
            await client.WaitForJobAsync(JobId, maxAttempts: 2, pollInterval: TimeSpan.Zero);
            Check(watch.Elapsed >= TimeSpan.FromMilliseconds(900), "poll Retry-After must delay next GET");
        }
        await using (var server = new Loopback(new(200, Job("Queued"), "-1"), new(200, Job("Succeeded"))))
        await using (var client = Client(server))
        {
            var watch = Stopwatch.StartNew();
            await client.WaitForJobAsync(JobId, maxAttempts: 2, pollInterval: TimeSpan.FromMilliseconds(180));
            Check(watch.Elapsed >= TimeSpan.FromMilliseconds(160), "invalid poll hint must use caller interval");
        }
    }

    static async Task BoundedAndTerminal()
    {
        await using (var server = new Loopback(new(200, Job("Queued"), "0"), new(200, Job("Processing"), "30")))
        await using (var client = Client(server))
        {
            using var stop = new CancellationTokenSource(TimeSpan.FromSeconds(2));
            await Safe<CognerisMaxAttemptsException>(() => client.WaitForJobAsync(JobId, maxAttempts: 2,
                pollInterval: TimeSpan.Zero, cancellationToken: stop.Token));
            Check(server.Requests.Count == 2, "attempt bound must stop without a final delay");
            await Throws<ArgumentOutOfRangeException>(() => client.WaitForJobAsync(JobId, maxAttempts: 0));
            await Throws<ArgumentOutOfRangeException>(() => client.WaitForJobAsync(JobId, pollInterval: TimeSpan.FromSeconds(-1)));
            Check(server.Requests.Count == 2, "invalid options must not send requests");
        }
        foreach (var status in new[] { "Failed", "Cancelled" })
        {
            await using var server = new Loopback(new Reply(200, Job(status)));
            await using var client = Client(server);
            await Safe<CognerisJobTerminalException>(() => client.WaitForJobAsync(JobId));
            Check(server.Requests.Count == 1, "terminal failure must stop polling");
        }
    }

    static async Task Cancellation()
    {
        // An in-flight request is cancelled after it reaches the actual HTTP listener.
        await using (var server = new Loopback(new Reply(200, Job("Succeeded"), Delay: TimeSpan.FromSeconds(10))))
        await using (var client = Client(server))
        using (var stop = new CancellationTokenSource())
        {
            var pending = client.GetJobAsync(JobId, stop.Token);
            await server.Received.Task.WaitAsync(TimeSpan.FromSeconds(3));
            stop.Cancel();
            await Cancelled(() => pending, stop.Token);
        }
        // Poll sleeps honor cancellation and cannot issue another request afterwards.
        await using (var server = new Loopback(new Reply(200, Job("Processing"), "30")))
        await using (var client = Client(server))
        using (var stop = new CancellationTokenSource(TimeSpan.FromMilliseconds(250)))
        {
            await Cancelled(() => client.WaitForJobAsync(JobId, cancellationToken: stop.Token), stop.Token);
            Check(server.Requests.Count == 1, "cancellation during poll delay must stop HTTP calls");
        }
        await using (var server = new Loopback())
        await using (var client = Client(server))
        using (var stop = new CancellationTokenSource())
        {
            stop.Cancel();
            await Cancelled(() => client.ExtractAsync(new MemoryStream(), "identity.pdf", cancellationToken: stop.Token), stop.Token);
            await Cancelled(() => client.SubmitJobAsync(DocumentJobSubmitOperation.Extraction, "artifact://input", stop.Token), stop.Token);
            await Cancelled(() => client.CancelJobAsync(JobId, stop.Token), stop.Token);
            Check(server.Requests.IsEmpty, "pre-cancelled calls must not send requests");
        }
    }

    static async Task SafeErrors()
    {
        foreach (var code in new[] { 401, 429, 500, 201 })
        {
            await using var server = new Loopback(new Reply(code, Key + Reflected + Document));
            await using var client = Client(server);
            var error = await Safe<CognerisApiException>(() => client.GetJobAsync(JobId));
            Check(error.StatusCode == (HttpStatusCode)code, "API error must preserve only safe status metadata");
        }
        foreach (var body in new[] { Key + Reflected + Document, "null", "{}", Envelope(null), Envelope(new { jobId = JobId }, true) })
        {
            await using var server = new Loopback(new Reply(200, body));
            await using var client = Client(server);
            await Safe<CognerisResponseException>(() => client.GetJobAsync(JobId));
        }
        await using (var server = new Loopback(new Reply(200, Envelope(new { }, true))))
        await using (var client = Client(server))
            await Safe<CognerisResponseException>(() => client.ExtractAsync(new MemoryStream(Encoding.UTF8.GetBytes(Document)), "identity.pdf"));
        await using (var server = new Loopback(new Reply(200, Submission())))
        await using (var client = Client(server))
            await Safe<CognerisApiException>(() => client.SubmitJobAsync(DocumentJobSubmitOperation.Extraction, "artifact://input"));
        await using (var server = new Loopback(new Reply(200, Envelope(new { jobId = JobId, cancellationRequested = true }))))
        await using (var client = Client(server))
            await Safe<CognerisApiException>(() => client.CancelJobAsync(JobId));
    }

    static async Task LoopbackSeam()
    {
        foreach (var uri in new[] { "https://example.com", "http://127.0.0.2", "http://localhost.example.com", "file:///tmp/test", "http://user:secret@localhost", "http://localhost/?secret=1", "relative" })
            await Throws<ArgumentException>(async () => { await using var _ = new CognerisClient(new(Key, BaseUriForTesting: new Uri(uri, UriKind.RelativeOrAbsolute))); });
        foreach (var uri in new[] { "http://localhost:12345", "http://127.0.0.1:12345", "http://[::1]:12345" })
        {
            await using var client = new CognerisClient(new(Key, BaseUriForTesting: new Uri(uri)));
        }
        await using var us = new CognerisClient(new(Key, CognerisRegion.Us));
        await using var eu = new CognerisClient(new(Key, CognerisRegion.Eu));
        await Throws<ArgumentException>(async () => { await using var _ = new CognerisClient(new(" ")); });
    }

    static async Task TransportFailure()
    {
        Uri uri;
        await using (var server = new Loopback()) uri = server.BaseUri;
        await using var client = new CognerisClient(new(Key, BaseUriForTesting: uri));
        await Safe<CognerisTransportException>(() => client.GetJobAsync(JobId));
    }

    static async Task<T> Throws<T>(Func<Task> action) where T : Exception
    {
        try { await action().WaitAsync(TimeSpan.FromSeconds(5)); }
        catch (T error) { return error; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    static async Task<T> Safe<T>(Func<Task> action) where T : CognerisException
    {
        var error = await Throws<T>(action);
        foreach (var secret in new[] { Key, Reflected, Document })
            Check(!error.ToString().Contains(secret), "exception must not retain private content");
        Check(error.InnerException is null && error.Data.Count == 0, "exception must not retain unsafe causes or data");
        return error;
    }
    static async Task Cancelled(Func<Task> action, CancellationToken token)
    {
        var error = await Throws<OperationCanceledException>(action);
        Check(error.CancellationToken == token, "cancellation must retain caller token");
        foreach (var secret in new[] { Key, Reflected, Document })
            Check(!error.ToString().Contains(secret), "cancellation must be safe");
    }
    static void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
}

record Reply(int Status, string Body, string? RetryAfter = null, TimeSpan Delay = default);
record Request(string Method, string Path, string Authorization, string ContentType, string Body);

sealed class Loopback : IAsyncDisposable
{
    readonly HttpListener listener = new();
    readonly CancellationTokenSource stopping = new();
    readonly Queue<Reply> replies;
    readonly Task serving;
    public Uri BaseUri { get; }
    public ConcurrentQueue<Request> Requests { get; } = new();
    public TaskCompletionSource Received { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);

    public Loopback(params Reply[] replies)
    {
        this.replies = new(replies);
        using var reservation = new TcpListener(IPAddress.Loopback, 0);
        reservation.Start();
        var port = ((IPEndPoint)reservation.LocalEndpoint).Port;
        reservation.Stop();
        BaseUri = new Uri($"http://127.0.0.1:{port}/");
        listener.Prefixes.Add(BaseUri.ToString());
        listener.Start();
        serving = Serve();
    }

    async Task Serve()
    {
        try
        {
            while (!stopping.IsCancellationRequested)
            {
                var context = await listener.GetContextAsync().WaitAsync(stopping.Token);
                var request = context.Request;
                using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
                var body = await reader.ReadToEndAsync(stopping.Token);
                Requests.Enqueue(new(request.HttpMethod, request.Url!.AbsolutePath, request.Headers["Authorization"] ?? "", request.ContentType ?? "", body));
                Received.TrySetResult();
                var reply = replies.Count > 0 ? replies.Dequeue() : new Reply(500, "Unexpected request");
                await Task.Delay(reply.Delay, stopping.Token);
                context.Response.StatusCode = reply.Status;
                context.Response.ContentType = "application/json";
                if (reply.RetryAfter is not null) context.Response.Headers["Retry-After"] = reply.RetryAfter;
                var bytes = Encoding.UTF8.GetBytes(reply.Body);
                context.Response.ContentLength64 = bytes.Length;
                await context.Response.OutputStream.WriteAsync(bytes, stopping.Token);
                context.Response.Close();
            }
        }
        catch (OperationCanceledException) when (stopping.IsCancellationRequested) { }
        catch (HttpListenerException) when (stopping.IsCancellationRequested) { }
    }

    public async ValueTask DisposeAsync()
    {
        stopping.Cancel();
        listener.Close();
        await serving;
        stopping.Dispose();
    }
}
