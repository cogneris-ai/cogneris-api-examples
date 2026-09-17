package ai.cogneris.consumer;

import ai.cogneris.documentai.*;
import ai.cogneris.documentai.model.*;
import com.sun.net.httpserver.HttpServer;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.Modifier;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.function.Executable;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

@Timeout(15)
class CognerisSdkSmokeTest {
    static final String KEY = "xtkt_live_package_only_secret";
    static final String REFLECTED = "reflected-private-payload";
    static final String DOCUMENT = "document-bytes";
    static final UUID JOB = UUID.fromString("2cabd780-7886-499c-a452-f4d609bd9b1e");
    @TempDir Path files;

    static CognerisClient client(Loopback server) {
        return new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US, server.uri));
    }
    static String envelope(String data) {
        return "{\"data\":" + data + ",\"meta\":{\"httpStatusCode\":200,\"messages\":[\"" + REFLECTED
                + "\"]},\"hasErrors\":false}";
    }
    static String job(String status) {
        return envelope("{\"jobId\":\"" + JOB + "\",\"operation\":\"Extraction\",\"status\":\"" + status
                + "\",\"outputReference\":\"artifact://tenant/output/result\",\"stage\":\"complete\","
                + "\"processedPages\":1,\"totalPages\":1,\"attemptCount\":1,\"failureCode\":\"" + REFLECTED
                + "\",\"retryable\":false,\"startedAt\":\"2026-09-17T12:00:00Z\","
                + "\"completedAt\":\"2026-09-17T12:00:01Z\",\"cancellationRequestedAt\":null,"
                + "\"expiresAt\":\"2026-09-18T12:00:00Z\"}");
    }
    static String submission(int hint) {
        return envelope("{\"jobId\":\"" + JOB + "\",\"status\":\"Queued\",\"statusUrl\":\"/api/v1/document-jobs/"
                + JOB + "\",\"retryAfterSeconds\":" + hint + "}");
    }
    Path document() throws Exception {
        return Files.writeString(files.resolve("identity.pdf"), DOCUMENT);
    }

    @Test void artifactOrigin() throws Exception {
        // Compile through the generated API's exposed transitive types using only the POM.
        assertEquals(7, new ApiClient().getObjectMapper().readTree("{\"id\":7}").get("id").asInt());
        assertFalse(new DocumentJob().getStage_JsonNullable().isPresent());
        var loaded = Path.of(CognerisClient.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        assertEquals(Path.of(System.getenv("COGNERIS_RESOLVED_JAR")).toRealPath(), loaded.toRealPath());
        assertTrue(loaded.toString().endsWith(".jar"));
        System.out.println("Package code source: " + loaded);
        System.out.println("Package SHA256: " + HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(loaded))));
    }

    @Test void workflowAuthenticatesAndUsesGeneratedMultipartAndModels() throws Exception {
        try (var server = new Loopback(
                new Reply(200, envelope("{\"id\":\"" + JOB + "\",\"metadata\":{\"identity\":\"123\"},\"createdDate\":\"2026-09-17T12:00:00Z\"}")),
                new Reply(202, submission(0), "0"), new Reply(200, job("Queued"), "0"),
                new Reply(200, job("Processing"), "0"), new Reply(200, job("Succeeded")),
                new Reply(202, envelope("{\"jobId\":\"" + JOB + "\",\"status\":\"Cancelled\",\"cancellationRequested\":true}")))) {
            var client = client(server);
            var extracted = client.extract(document(), "return id");
            assertEquals(JOB, extracted.getData().getId());
            assertEquals("123", extracted.getData().getMetadata().get("identity"));
            var submitted = client.submitJob(DocumentJobSubmitOperation.EXTRACTION, "artifact://tenant/input/reference");
            assertEquals(JOB, submitted.getJobId());
            var completed = client.waitForJob(JOB, 3, Duration.ofSeconds(2), Duration.ZERO);
            assertEquals(DocumentJobStatus.SUCCEEDED, completed.getStatus());
            assertEquals("artifact://tenant/output/result", completed.getOutputReference());
            var cancelled = client.cancelJob(JOB);
            assertEquals(JOB, cancelled.getJobId());
            assertEquals(true, cancelled.getCancellationRequested());
            assertEquals(6, server.requests.size());
            assertTrue(server.requests.stream().allMatch(r -> r.authorization.equals("Bearer " + KEY)));
            var upload = server.requests.get(0);
            assertEquals("POST /Document/extraction", upload.route);
            assertTrue(upload.contentType.startsWith("multipart/form-data;"));
            for (String part : List.of("name=file", "filename=identity.pdf", DOCUMENT, "ComplementaryPrompt", "return id"))
                assertTrue(upload.body.replace("\"", "").contains(part), part);
            var submit = server.requests.get(1);
            assertEquals("POST /api/v1/document-jobs", submit.route);
            assertTrue(submit.body.contains("\"operation\":\"Extraction\""));
            assertTrue(submit.body.contains("\"inputReference\":\"artifact://tenant/input/reference\""));
            for (var request : server.requests.subList(2, 5)) assertEquals("GET /api/v1/document-jobs/" + JOB, request.route);
            assertEquals("POST /api/v1/document-jobs/" + JOB + "/cancel", server.requests.get(5).route);
        }
    }

    @Test void submissionHeaderBeatsBodyAndIsConsumedOnce() throws Exception {
        try (var server = new Loopback(new Reply(202, submission(30), "1"),
                new Reply(200, job("Succeeded")), new Reply(200, job("Succeeded")))) {
            var client = client(server);
            client.submitJob(DocumentJobSubmitOperation.EXTRACTION, "artifact://tenant/input/reference");
            long start = System.nanoTime();
            client.waitForJob(JOB, 1, Duration.ofSeconds(3), Duration.ZERO);
            assertTrue(System.nanoTime() - start >= 900_000_000L);
            client.waitForJob(JOB, 1, Duration.ofMillis(700), Duration.ZERO);
            assertEquals(3, server.requests.size());
        }
    }

    @Test void multipartPromptPreservesNonLatinUtf8() throws Exception {
        try (var server = new Loopback(new Reply(200, envelope("{\"id\":\"" + JOB + "\"}")))) {
            client(server).extract(document(), "提取姓名");
            assertTrue(server.requests.get(0).body.contains("提取姓名"), "multipart prompt bytes must be UTF-8");
            assertTrue(server.requests.get(0).body.toLowerCase(java.util.Locale.ROOT).contains("charset=utf-8"));
        }
    }

    @Test void utf8JsonIgnoresNonUtf8JvmDefault() throws Exception {
        assertEquals("windows-1252", java.nio.charset.Charset.defaultCharset().name());
        try (var server = new Loopback(
                new Reply(200, envelope("{\"id\":\"" + JOB + "\",\"metadata\":{\"name\":\"José\"}}")),
                new Reply(200, job("Succeeded").replace("artifact://tenant/output/result", "artifact://tenant/output/José")))) {
            var client = client(server);
            assertEquals("José", client.extract(document(), null).getData().getMetadata().get("name"));
            assertEquals("artifact://tenant/output/José", client.getJob(JOB).getOutputReference());
        }
    }

    @Test void invalidHeadersFallBackToBodyAndNegativeBodyFallsBackToInterval() throws Exception {
        for (String hint : List.of("-1", "+1", "0.5", "Thu, 17 Sep 2026 12:00:00 GMT", "999999999999999999999", "garbage")) {
            try (var server = new Loopback(new Reply(202, submission(1), hint))) {
                var client = client(server);
                client.submitJob(DocumentJobSubmitOperation.EXTRACTION, "artifact://tenant/input/reference");
                var error = safe(CognerisTransportException.class, () -> client.waitForJob(JOB, 1, Duration.ofMillis(100), Duration.ZERO));
                assertEquals("Cogneris API request timed out.", error.getMessage());
                assertEquals(1, server.requests.size());
            }
        }
        try (var server = new Loopback(new Reply(202, submission(-1), "bad"), new Reply(200, job("Succeeded")))) {
            var client = client(server);
            client.submitJob(DocumentJobSubmitOperation.EXTRACTION, "artifact://tenant/input/reference");
            client.waitForJob(JOB, 1, Duration.ofSeconds(1), Duration.ZERO);
            assertEquals(2, server.requests.size());
        }
    }

    @Test void pollHeaderDelaysNextGetAndInvalidHeaderUsesCallerInterval() throws Exception {
        for (String hint : List.of("1", "-1")) {
            try (var server = new Loopback(new Reply(200, job("Processing"), hint), new Reply(200, job("Succeeded")))) {
                long start = System.nanoTime();
                client(server).waitForJob(JOB, 2, Duration.ofSeconds(3), Duration.ofMillis(180));
                assertTrue(System.nanoTime() - start >= (hint.equals("1") ? 900_000_000L : 160_000_000L));
                assertEquals(2, server.requests.size());
            }
        }
    }

    @Test void attemptBoundDoesNotSleepAfterFinalAttempt() throws Exception {
        try (var server = new Loopback(new Reply(200, job("Queued"), "0"), new Reply(200, job("Processing"), "30"))) {
            safe(CognerisMaxAttemptsException.class, () -> client(server).waitForJob(JOB, 2, Duration.ofSeconds(1), Duration.ZERO));
            assertEquals(2, server.requests.size());
        }
    }

    @Test void invalidBoundsAndZeroDeadlineDoNotSendRequests() throws Exception {
        try (var server = new Loopback()) {
            var client = client(server);
            assertThrows(IllegalArgumentException.class, () -> client.waitForJob(JOB, 0, Duration.ofSeconds(1), Duration.ZERO));
            for (Duration duration : new Duration[] { null, Duration.ofSeconds(-1), Duration.ofSeconds(Long.MAX_VALUE) }) {
                assertThrows(IllegalArgumentException.class, () -> client.waitForJob(JOB, 1, duration, Duration.ZERO));
                assertThrows(IllegalArgumentException.class, () -> client.waitForJob(JOB, 1, Duration.ofSeconds(1), duration));
            }
            safe(CognerisTransportException.class, () -> client.waitForJob(JOB, 1, Duration.ZERO, Duration.ZERO));
            assertTrue(server.requests.isEmpty());
        }
    }

    @Test void deadlineBoundsSlowHeadersAndSlowBody() throws Exception {
        for (boolean bodyDelay : List.of(false, true)) {
            try (var server = new Loopback(new Reply(200, job("Succeeded"), null, 1800, bodyDelay, "application/json"))) {
                long start = System.nanoTime();
                var error = safe(CognerisTransportException.class, () -> client(server).waitForJob(JOB, 1, Duration.ofMillis(200), Duration.ZERO));
                assertEquals("Cogneris API request timed out.", error.getMessage());
                assertTrue(System.nanoTime() - start < 1_000_000_000L, "total deadline must include response body");
                assertEquals(1, server.requests.size());
                awaitNoSdkWorkers();
            }
        }
    }

    @Test void terminalFailuresAreSafeAndStopPolling() throws Exception {
        for (String status : List.of("Failed", "Cancelled")) {
            try (var server = new Loopback(new Reply(200, job(status)))) {
                safe(CognerisJobTerminalException.class, () -> client(server).waitForJob(JOB, 5, Duration.ofSeconds(2), Duration.ZERO));
                assertEquals(1, server.requests.size());
            }
        }
    }

    @Test void httpErrorsAndUnexpectedSuccessStatusesAreSafe() throws Exception {
        for (int code : new int[] {401, 429, 500, 201}) {
            try (var server = new Loopback(new Reply(code, KEY + REFLECTED + DOCUMENT))) {
                var error = safe(CognerisApiException.class, () -> client(server).getJob(JOB));
                assertEquals(code, error.getStatusCode());
            }
        }
        try (var server = new Loopback(new Reply(200, submission(0)))) {
            safe(CognerisApiException.class, () -> client(server).submitJob(DocumentJobSubmitOperation.EXTRACTION, "artifact://input"));
        }
        try (var server = new Loopback(new Reply(200, envelope("{\"jobId\":\"" + JOB + "\",\"cancellationRequested\":true}")))) {
            safe(CognerisApiException.class, () -> client(server).cancelJob(JOB));
        }
    }

    @Test void malformedEnvelopesAndReflectedEnumsAreSafeResponseErrors() throws Exception {
        for (String body : List.of(KEY + REFLECTED + DOCUMENT, "null", "{}", envelope("null"),
                envelope("{}"), job(REFLECTED), job("Succeeded").replace("\"hasErrors\":false", "\"hasErrors\":true"))) {
            try (var server = new Loopback(new Reply(200, body))) {
                safe(CognerisResponseException.class, () -> client(server).getJob(JOB));
            }
        }
        try (var server = new Loopback(new Reply(200, envelope("{}").replace("\"hasErrors\":false", "\"hasErrors\":true")))) {
            safe(CognerisResponseException.class, () -> client(server).extract(document(), null));
        }
        try (var server = new Loopback(new Reply(200, job("Succeeded"), null, 0, false, "application/json; charset=" + REFLECTED))) {
            safe(CognerisResponseException.class, () -> client(server).getJob(JOB));
        }
    }

    @Test void connectionFailureDoesNotRetainTransportCause() throws Exception {
        URI uri;
        try (var server = new Loopback()) { uri = server.uri; }
        var client = new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US, uri));
        safe(CognerisTransportException.class, () -> client.getJob(JOB));
    }

    @Test void refusedLargeUploadClosesProducerAndDocumentHandle() throws Exception {
        URI uri;
        try (var server = new Loopback()) { uri = server.uri; }
        Path file = Files.write(files.resolve("refused-upload.pdf"), new byte[4 * 1024 * 1024]);
        var client = new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US, uri));
        safe(CognerisTransportException.class, () -> client.extract(file, "提取"));
        awaitNoUploadProducers();
        assertDocumentHandleClosed(file);
    }

    @Test void interruptedLargeUploadClosesProducerAndDocumentHandleWithoutLogging() throws Exception {
        Path file = Files.write(files.resolve("interrupted-upload.pdf"), new byte[16 * 1024 * 1024]);
        var server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        var executor = Executors.newCachedThreadPool();
        var received = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        server.setExecutor(executor);
        server.createContext("/", exchange -> {
            received.countDown();
            try { release.await(10, TimeUnit.SECONDS); }
            catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            finally { exchange.close(); }
        });
        server.start();
        var originalError = System.err;
        var capturedError = new java.io.ByteArrayOutputStream();
        try (var sink = new java.io.PrintStream(capturedError, true, StandardCharsets.UTF_8)) {
            System.setErr(sink);
            var client = new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US,
                    URI.create("http://localhost:" + server.getAddress().getPort())));
            var observed = new AtomicReference<Throwable>();
            var interrupted = new AtomicBoolean();
            var caller = new Thread(() -> {
                try { client.extract(file, "提取"); }
                catch (Throwable failure) { observed.set(failure); interrupted.set(Thread.currentThread().isInterrupted()); }
            });
            caller.setDaemon(true);
            caller.start();
            assertTrue(received.await(3, TimeUnit.SECONDS), "upload must reach the actual server");
            assertFalse(uploadProducers().isEmpty(), "large body must start a real streaming producer");
            caller.interrupt();
            caller.join(2000);
            assertFalse(caller.isAlive());
            assertInstanceOf(CognerisTransportException.class, observed.get());
            assertTrue(interrupted.get());
            assertNull(observed.get().getCause());
            awaitNoUploadProducers();
            assertDocumentHandleClosed(file);
            assertEquals("", capturedError.toString(StandardCharsets.UTF_8), "upload cancellation must not print exceptions");
        } finally {
            System.setErr(originalError);
            release.countDown();
            server.stop(0);
            executor.shutdownNow();
        }
    }

    static List<Thread> uploadProducers() {
        return Thread.getAllStackTraces().entrySet().stream().filter(entry -> entry.getKey().isAlive()
                && (entry.getKey().getName().equals("cogneris-sdk-upload") || java.util.Arrays.stream(entry.getValue())
                    .anyMatch(frame -> frame.getClassName().equals("ai.cogneris.documentai.api.DocumentsApi")
                            && frame.getMethodName().contains("RequestBuilder"))))
                .map(java.util.Map.Entry::getKey).toList();
    }

    static void awaitNoUploadProducers() throws InterruptedException {
        for (int attempt = 0; attempt < 50; attempt++) {
            if (uploadProducers().isEmpty()) return;
            Thread.sleep(20);
        }
        fail("multipart producer must terminate after refused/interrupted upload");
    }

    static void assertDocumentHandleClosed(Path file) throws Exception {
        // Inspect the current JVM's real open descriptors on the supported Unix test hosts.
        if (Files.isDirectory(Path.of("/proc/self/fd"))) {
            try (var descriptors = Files.list(Path.of("/proc/self/fd"))) {
                for (Path descriptor : descriptors.toList()) {
                    try { assertNotEquals(file.toRealPath(), descriptor.toRealPath(), "document handle leaked"); }
                    catch (java.nio.file.NoSuchFileException ignored) { }
                }
            }
        } else if (Files.isExecutable(Path.of("/usr/sbin/lsof"))) {
            var process = new ProcessBuilder("/usr/sbin/lsof", "-a", "-p", Long.toString(ProcessHandle.current().pid()),
                    "-Fn", "--", file.toString()).redirectErrorStream(true).start();
            assertTrue(process.waitFor(3, TimeUnit.SECONDS));
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            assertEquals(1, process.exitValue(), "document handle leaked: " + output);
            assertEquals("", output, "descriptor inspection must report no document handle or diagnostic");
        }
    }

    @Test void onlyExplicitLoopbackOriginsAreAccepted() {
        for (String uri : List.of("https://example.com", "http://127.0.0.2", "http://localhost.example.com", "file:///tmp/test",
                "http://user:secret@localhost", "http://localhost/?secret=1", "http://localhost/#secret", "http://localhost/path", "relative"))
            assertThrows(IllegalArgumentException.class, () -> new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US, URI.create(uri))));
        for (String uri : List.of("http://localhost:12345", "http://127.0.0.1:12345", "http://[::1]:12345"))
            assertDoesNotThrow(() -> new CognerisClient(new CognerisClient.Options(KEY, CognerisClient.Region.US, URI.create(uri))));
        for (var region : CognerisClient.Region.values())
            assertDoesNotThrow(() -> new CognerisClient(new CognerisClient.Options(KEY, region, null)));
        assertThrows(IllegalArgumentException.class, () -> new CognerisClient(new CognerisClient.Options(" ", CognerisClient.Region.US, null)));
    }

    @Test void interruptionDuringRequestBodyAndPollSleepPreservesContract() throws Exception {
        for (int mode : new int[] {0, 1, 2, 3}) {
            Reply reply = mode == 2 ? new Reply(200, job("Processing"), "30")
                    : new Reply(200, job("Succeeded"), null, 5000, mode == 1, "application/json");
            try (var server = new Loopback(reply)) {
                var observed = new AtomicReference<Throwable>();
                var interrupted = new AtomicBoolean();
                var client = client(server);
                var thread = new Thread(() -> {
                    try { client.waitForJob(JOB, 5, Duration.ofSeconds(10), Duration.ZERO); }
                    catch (Throwable error) { observed.set(error); interrupted.set(Thread.currentThread().isInterrupted()); }
                });
                thread.setDaemon(true);
                thread.start();
                if (mode != 3) {
                    assertTrue(server.received.await(3, TimeUnit.SECONDS));
                    Thread.sleep(80);
                }
                thread.interrupt();
                thread.join(2000);
                assertFalse(thread.isAlive(), "interrupted wait must return promptly, mode=" + mode);
                assertInstanceOf(InterruptedException.class, observed.get());
                assertTrue(interrupted.get(), "interrupted flag must be restored");
                assertNull(observed.get().getCause());
                assertEquals(0, observed.get().getSuppressed().length);
                assertTrue(server.requests.size() <= 1);
                awaitNoSdkWorkers();
            }
        }
    }

    static void awaitNoSdkWorkers() throws InterruptedException {
        for (int attempt = 0; attempt < 25; attempt++) {
            if (Thread.getAllStackTraces().keySet().stream()
                    .noneMatch(t -> t.isAlive() && t.getName().equals("cogneris-sdk-request"))) return;
            Thread.sleep(20);
        }
        fail("generated request worker must terminate after deadline or interruption");
    }

    static <T extends CognerisException> T safe(Class<T> type, Executable call) throws Exception {
        T error = assertThrows(type, call);
        assertNull(error.getCause());
        assertEquals(0, error.getSuppressed().length);
        var trace = new StringWriter();
        error.printStackTrace(new PrintWriter(trace));
        for (String secret : List.of(KEY, REFLECTED, DOCUMENT)) assertFalse(trace.toString().contains(secret));
        for (Class<?> current = error.getClass(); current != RuntimeException.class; current = current.getSuperclass()) {
            for (var field : current.getDeclaredFields()) {
                if (Modifier.isStatic(field.getModifiers())) continue;
                field.setAccessible(true);
                Object value = field.get(error);
                assertTrue(value == null || value instanceof Integer || value instanceof Enum<?>,
                        "public error must not retain arbitrary state: " + field.getName());
            }
        }
        return error;
    }

    record Reply(int status, String body, String retryAfter, long delayMillis, boolean delayBody, String contentType) {
        Reply(int status, String body) { this(status, body, null); }
        Reply(int status, String body, String retryAfter) { this(status, body, retryAfter, 0, false, "application/json"); }
    }
    record Request(String route, String authorization, String contentType, String body) {}

    static final class Loopback implements AutoCloseable {
        final HttpServer server;
        final URI uri;
        final List<Request> requests = new CopyOnWriteArrayList<>();
        final CountDownLatch received = new CountDownLatch(1);
        final java.util.concurrent.ExecutorService executor = Executors.newCachedThreadPool();

        Loopback(Reply... replies) throws Exception {
            var queue = new ArrayDeque<>(List.of(replies));
            server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
            String host = server.getAddress().getAddress().getHostAddress();
            uri = URI.create("http://" + (host.contains(":") ? "[" + host + "]" : host) + ":" + server.getAddress().getPort());
            server.setExecutor(executor);
            server.createContext("/", exchange -> {
                try (exchange) {
                    var headers = exchange.getRequestHeaders();
                    requests.add(new Request(exchange.getRequestMethod() + " " + exchange.getRequestURI().getPath(),
                            headers.getFirst("Authorization"), String.valueOf(headers.getFirst("Content-Type")),
                            new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8)));
                    Reply reply;
                    synchronized (queue) { reply = queue.isEmpty() ? new Reply(500, "Unexpected request") : queue.remove(); }
                    if (reply.delayBody) {
                        exchange.getResponseHeaders().set("Content-Type", reply.contentType);
                        exchange.sendResponseHeaders(reply.status, reply.body.getBytes(StandardCharsets.UTF_8).length);
                        exchange.getResponseBody().flush();
                    }
                    received.countDown();
                    Thread.sleep(reply.delayMillis);
                    if (!reply.delayBody) {
                        exchange.getResponseHeaders().set("Content-Type", reply.contentType);
                        if (reply.retryAfter != null) exchange.getResponseHeaders().set("Retry-After", reply.retryAfter);
                        exchange.sendResponseHeaders(reply.status, reply.body.getBytes(StandardCharsets.UTF_8).length);
                    }
                    exchange.getResponseBody().write(reply.body.getBytes(StandardCharsets.UTF_8));
                } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
                catch (java.io.IOException ignored) { /* Client cancellation closes the response stream. */ }
            });
            server.start();
        }
        public void close() { server.stop(0); executor.shutdownNow(); }
    }
}
