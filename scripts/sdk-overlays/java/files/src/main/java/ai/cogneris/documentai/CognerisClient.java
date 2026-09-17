package ai.cogneris.documentai;

import ai.cogneris.documentai.api.DocumentsApi;
import ai.cogneris.documentai.api.JobsApi;
import ai.cogneris.documentai.model.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpTimeoutException;
import java.nio.file.Path;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.apache.http.entity.ContentType;

/** Document workflows over the generated Java 17 client and public models. */
public final class CognerisClient {
    public enum Region { US, EU }
    public record Options(String apiKey, Region region, URI baseUriForTesting) {}

    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(60);
    private final String apiKey;
    private final URI baseUri;
    private final ConcurrentHashMap<UUID, Long> submitHints = new ConcurrentHashMap<>();

    public CognerisClient(Options options) {
        if (options == null || options.apiKey() == null || options.apiKey().isBlank() || options.region() == null)
            throw new IllegalArgumentException("An API key and region are required.");
        apiKey = options.apiKey();
        baseUri = options.baseUriForTesting() == null
                ? URI.create(options.region() == Region.US ? "https://api-us.cogneris.ai" : "https://api-eu.cogneris.ai")
                : loopback(options.baseUriForTesting());
    }

    public Envelope extract(Path file, String complementaryPrompt) {
        if (file == null) throw new IllegalArgumentException("A document path is required.");
        var response = send(200, REQUEST_TIMEOUT, api -> new DocumentsApi(api)
                .extractDocumentWithHttpInfo(file.toFile(), complementaryPrompt));
        var envelope = response.getData();
        if (envelope == null || Boolean.TRUE.equals(envelope.getHasErrors()) || envelope.getData() == null)
            throw new CognerisResponseException();
        return envelope;
    }

    public DocumentJobSubmission submitJob(DocumentJobSubmitOperation operation, String inputReference) {
        if (operation == null || inputReference == null || inputReference.isBlank())
            throw new IllegalArgumentException("A job operation and input reference are required.");
        var request = new SubmitDocumentJobRequest().operation(operation).inputReference(inputReference);
        var response = send(202, REQUEST_TIMEOUT, api -> new JobsApi(api).submitDocumentJobWithHttpInfo(request));
        var envelope = response.getData();
        if (envelope == null || Boolean.TRUE.equals(envelope.getHasErrors()) || envelope.getData() == null
                || envelope.getData().getJobId() == null)
            throw new CognerisResponseException();
        var result = envelope.getData();
        Long hint = retryAfter(response);
        if (hint == null && result.getRetryAfterSeconds() != null && result.getRetryAfterSeconds() >= 0)
            hint = Duration.ofSeconds(result.getRetryAfterSeconds()).toNanos();
        if (hint != null) submitHints.put(result.getJobId(), hint);
        return result;
    }

    public DocumentJob getJob(UUID jobId) {
        requireJobId(jobId);
        return job(send(200, REQUEST_TIMEOUT, api -> new JobsApi(api).getDocumentJobWithHttpInfo(jobId)));
    }

    /** Polls within both a request-count bound and a total deadline, including retry delays. */
    public DocumentJob waitForJob(UUID jobId, int maxAttempts, Duration timeout, Duration pollInterval)
            throws InterruptedException {
        requireJobId(jobId);
        if (maxAttempts < 1) throw new IllegalArgumentException("The attempt bound must be positive.");
        long timeoutNanos = durationNanos(timeout);
        long intervalNanos = durationNanos(pollInterval);
        long start = System.nanoTime();
        try {
            checkInterrupted();
            Long hint = submitHints.remove(jobId);
            if (hint != null) sleep(hint, start, timeoutNanos);
            for (int attempt = 0; attempt < maxAttempts; attempt++) {
                checkInterrupted();
                var response = sendInterruptibly(200, Duration.ofNanos(remaining(start, timeoutNanos)),
                        api -> new JobsApi(api).getDocumentJobWithHttpInfo(jobId));
                remaining(start, timeoutNanos);
                var result = job(response);
                if (result.getStatus() == DocumentJobStatus.SUCCEEDED) return result;
                if (result.getStatus() == DocumentJobStatus.FAILED || result.getStatus() == DocumentJobStatus.CANCELLED)
                    throw new CognerisJobTerminalException(result.getStatus());
                if (attempt < maxAttempts - 1) {
                    hint = retryAfter(response);
                    sleep(hint == null ? intervalNanos : hint, start, timeoutNanos);
                }
            }
            throw new CognerisMaxAttemptsException(maxAttempts);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new InterruptedException("Cogneris API wait was interrupted.");
        }
    }

    public DocumentJobCancellation cancelJob(UUID jobId) {
        requireJobId(jobId);
        var response = send(202, REQUEST_TIMEOUT, api -> new JobsApi(api).cancelDocumentJobWithHttpInfo(jobId));
        var envelope = response.getData();
        if (envelope == null || Boolean.TRUE.equals(envelope.getHasErrors()) || envelope.getData() == null
                || envelope.getData().getJobId() == null)
            throw new CognerisResponseException();
        submitHints.remove(jobId);
        return envelope.getData();
    }

    private static DocumentJob job(ApiResponse<DocumentJobEnvelope> response) {
        var envelope = response.getData();
        if (envelope == null || Boolean.TRUE.equals(envelope.getHasErrors()) || envelope.getData() == null
                || envelope.getData().getJobId() == null || envelope.getData().getStatus() == null)
            throw new CognerisResponseException();
        return envelope.getData();
    }

    private ApiClient configuredApi(int expectedStatus, Duration timeout, InFlight inFlight) {
        return new ApiClient().setScheme(baseUri.getScheme()).setHost(baseUri.getHost()).setPort(baseUri.getPort())
                .setBasePath("").setConnectTimeout(timeout).setReadTimeout(timeout)
                .setRequestInterceptor(request -> {
                    request.setHeader("Authorization", "Bearer " + apiKey);
                    request.build().bodyPublisher().ifPresent(publisher -> {
                        // Only the private generated publisher we own is eligible for closure.
                        if (publisher.getClass().getEnclosingClass() == DocumentsApi.class
                                && publisher.getClass().getSimpleName().equals("MultipartBodyPublisher")
                                && publisher instanceof AutoCloseable upload) inFlight.attachUpload(upload);
                    });
                })
                .setResponseInterceptor(response -> {
                    inFlight.attach(response.body());
                    try {
                        if (response.statusCode() != expectedStatus) throw new CognerisApiException(response.statusCode());
                        // The generator decodes inside the operation. Reject invalid charset metadata
                        // here so a reflected decoder failure can never escape the facade.
                        response.headers().firstValue("Content-Type").ifPresent(ContentType::parse);
                    } catch (RuntimeException error) {
                        try { response.body().close(); } catch (IOException ignored) { }
                        if (error instanceof CognerisException safe) throw safe;
                        throw new CognerisResponseException();
                    }
                });
    }

    @FunctionalInterface
    private interface ApiCall<T> { ApiResponse<T> run(ApiClient api) throws ApiException; }

    private <T> ApiResponse<T> send(int status, Duration timeout, ApiCall<T> call) {
        try { return sendInterruptibly(status, timeout, call); }
        catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new CognerisTransportException(false);
        }
    }

    private <T> ApiResponse<T> sendInterruptibly(int status, Duration timeout, ApiCall<T> call)
            throws InterruptedException {
        checkInterrupted();
        long start = System.nanoTime();
        var inFlight = new InFlight();
        // The generated native operation reads an InputStream after send() returns.
        // Bound its entire lifecycle, including body decoding, without duplicating transport.
        var task = new FutureTask<>(() -> call.run(configuredApi(status, timeout, inFlight)));
        var worker = new Thread(task, "cogneris-sdk-request");
        worker.setDaemon(true);
        worker.start();
        try {
            return task.get(remaining(start, timeout.toNanos()), TimeUnit.NANOSECONDS);
        } catch (TimeoutException error) {
            throw new CognerisTransportException(true);
        } catch (ExecutionException error) {
            Throwable failure = error.getCause();
            if (failure instanceof CognerisException safe) throw safe;
            for (Throwable cause = failure; cause != null; cause = cause.getCause()) {
                if (cause instanceof InterruptedException)
                    throw new InterruptedException("Cogneris API wait was interrupted.");
                if (cause instanceof HttpTimeoutException) throw new CognerisTransportException(true);
                if (cause instanceof JsonProcessingException) throw new CognerisResponseException();
            }
            if (failure instanceof ApiException api && api.getCode() > 0) throw new CognerisApiException(api.getCode());
            if (failure instanceof RuntimeException) throw new CognerisResponseException();
            if (failure instanceof Error fatal) throw fatal;
            throw new CognerisTransportException(false);
        } finally {
            task.cancel(true);
            inFlight.close();
        }
    }

    /** Coordinates cancellation before or after the generated response interceptor runs. */
    private static final class InFlight {
        private InputStream body;
        private AutoCloseable upload;
        private boolean closed;

        synchronized void attachUpload(AutoCloseable publisher) {
            if (closed) {
                closeUpload(publisher);
                throw new CognerisTransportException(false);
            }
            upload = publisher;
        }

        synchronized void attach(InputStream stream) {
            if (closed) {
                closeBody(stream);
                throw new CognerisTransportException(false);
            }
            body = stream;
        }

        synchronized void close() {
            closed = true;
            closeBody(body);
            body = null;
            closeUpload(upload);
            upload = null;
        }

        private static void closeUpload(AutoCloseable publisher) {
            if (publisher != null) {
                try { publisher.close(); } catch (Exception ignored) { }
            }
        }

        private static void closeBody(InputStream stream) {
            if (stream != null) {
                try { stream.close(); } catch (IOException ignored) { }
            }
        }
    }

    private static Long retryAfter(ApiResponse<?> response) {
        for (var entry : response.getHeaders().entrySet()) {
            if (!entry.getKey().equalsIgnoreCase("Retry-After")) continue;
            for (String value : entry.getValue()) {
                if (!value.matches("[0-9]+")) continue;
                try { return Duration.ofSeconds(Integer.parseInt(value)).toNanos(); }
                catch (NumberFormatException ignored) { }
            }
        }
        return null;
    }

    private static long durationNanos(Duration duration) {
        if (duration == null || duration.isNegative()) throw new IllegalArgumentException("Durations must be finite and non-negative.");
        try { return duration.toNanos(); }
        catch (ArithmeticException error) { throw new IllegalArgumentException("Duration exceeds the supported range."); }
    }

    private static long remaining(long start, long timeout) {
        long left = timeout - (System.nanoTime() - start);
        if (left <= 0) throw new CognerisTransportException(true);
        return left;
    }

    private static void sleep(long delay, long start, long timeout) throws InterruptedException {
        long nanos = Math.min(delay, remaining(start, timeout));
        Thread.sleep(nanos / 1_000_000, (int) (nanos % 1_000_000));
        remaining(start, timeout);
    }

    private static void checkInterrupted() throws InterruptedException {
        if (Thread.currentThread().isInterrupted()) throw new InterruptedException("Cogneris API wait was interrupted.");
    }

    private static void requireJobId(UUID jobId) {
        if (jobId == null) throw new IllegalArgumentException("A job ID is required.");
    }

    private static URI loopback(URI uri) {
        String host = uri.getHost();
        if (!("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme()))
                || host == null || !(host.equalsIgnoreCase("localhost") || host.equals("127.0.0.1") || host.equals("[::1]"))
                || uri.getRawUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null
                || !(uri.getRawPath().isEmpty() || uri.getRawPath().equals("/")))
            throw new IllegalArgumentException("The test base URI must be a loopback HTTP origin.");
        return uri;
    }
}
