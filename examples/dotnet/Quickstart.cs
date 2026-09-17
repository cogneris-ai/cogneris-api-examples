using Cogneris.DocumentAI;
using Cogneris.DocumentAI.Model;

const string usage = """
Usage:
  dotnet run -- extract <file>
  dotnet run -- submit <input-reference>
  dotnet run -- get <job-id>
  dotnet run -- wait <job-id>
  dotnet run -- cancel <job-id>
""";

var apiKey = Environment.GetEnvironmentVariable("COGNERIS_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
    throw new InvalidOperationException("COGNERIS_API_KEY is required.");

var region = (Environment.GetEnvironmentVariable("COGNERIS_REGION") ?? "us") switch
{
    "us" => CognerisRegion.Us,
    "eu" => CognerisRegion.Eu,
    _ => throw new ArgumentException("COGNERIS_REGION must be either us or eu.")
};

if (args.Length != 2)
    throw new ArgumentException(usage);

await using var client = new CognerisClient(new CognerisClientOptions(apiKey, region));

switch (args[0])
{
    case "extract":
        await using (var input = File.OpenRead(args[1]))
        {
            var envelope = await client.ExtractAsync(input, Path.GetFileName(args[1]));
            Console.WriteLine($"extracted; hasErrors={envelope.HasErrors}");
        }
        break;
    case "submit":
        var submission = await client.SubmitJobAsync(
            DocumentJobSubmitOperation.Extraction,
            args[1]);
        Console.WriteLine($"submitted; jobId={submission.JobId}");
        break;
    case "get":
        var current = await client.GetJobAsync(Guid.Parse(args[1]));
        Console.WriteLine($"jobId={current.JobId}; status={current.Status}");
        break;
    case "wait":
        var completed = await client.WaitForJobAsync(Guid.Parse(args[1]));
        Console.WriteLine($"jobId={completed.JobId}; status={completed.Status}");
        break;
    case "cancel":
        var cancellation = await client.CancelJobAsync(Guid.Parse(args[1]));
        Console.WriteLine($"jobId={cancellation.JobId}; cancellationRequested={cancellation.CancellationRequested}");
        break;
    default:
        throw new ArgumentException(usage);
}
