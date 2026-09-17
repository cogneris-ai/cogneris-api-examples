import ai.cogneris.documentai.CognerisClient;
import ai.cogneris.documentai.model.DocumentJobSubmitOperation;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Objects;
import java.util.UUID;

public final class Quickstart {
    private static final String USAGE = """
            Usage:
              java Quickstart extract <file>
              java Quickstart submit <input-reference>
              java Quickstart get <job-id>
              java Quickstart wait <job-id>
              java Quickstart cancel <job-id>
            """;

    private Quickstart() { }

    public static void main(String[] args) throws InterruptedException {
        if (args.length != 2) throw new IllegalArgumentException(USAGE);
        String apiKey = Objects.requireNonNull(
                System.getenv("COGNERIS_API_KEY"),
                "COGNERIS_API_KEY is required");
        var region = switch (System.getenv().getOrDefault("COGNERIS_REGION", "us")) {
            case "us" -> CognerisClient.Region.US;
            case "eu" -> CognerisClient.Region.EU;
            default -> throw new IllegalArgumentException("COGNERIS_REGION must be either us or eu.");
        };
        var client = new CognerisClient(new CognerisClient.Options(apiKey, region, null));

        switch (args[0]) {
            case "extract" -> {
                var envelope = client.extract(Path.of(args[1]), null);
                System.out.println("extracted; hasErrors=" + envelope.getHasErrors());
            }
            case "submit" -> {
                var submission = client.submitJob(DocumentJobSubmitOperation.EXTRACTION, args[1]);
                System.out.println("submitted; jobId=" + submission.getJobId());
            }
            case "get" -> {
                var job = client.getJob(UUID.fromString(args[1]));
                System.out.println("jobId=" + job.getJobId() + "; status=" + job.getStatus());
            }
            case "wait" -> {
                var job = client.waitForJob(
                        UUID.fromString(args[1]),
                        20,
                        Duration.ofMinutes(2),
                        Duration.ofSeconds(1));
                System.out.println("jobId=" + job.getJobId() + "; status=" + job.getStatus());
            }
            case "cancel" -> {
                var cancellation = client.cancelJob(UUID.fromString(args[1]));
                System.out.println("jobId=" + cancellation.getJobId()
                        + "; cancellationRequested=" + cancellation.getCancellationRequested());
            }
            default -> throw new IllegalArgumentException(USAGE);
        }
    }
}
