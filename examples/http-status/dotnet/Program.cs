using System.Net.Http.Headers;
using System.Text.Json;

if (args.Length != 1 || !Guid.TryParse(args[0], out var jobId)) throw new ArgumentException("Usage: dotnet run -- JOB_ID");
var key = Environment.GetEnvironmentVariable("COGNERIS_API_KEY");
if (string.IsNullOrWhiteSpace(key)) throw new InvalidOperationException("Set COGNERIS_API_KEY in the environment.");
var baseUrl = (Environment.GetEnvironmentVariable("COGNERIS_API_BASE") ?? "https://api-eu.cogneris.ai").TrimEnd('/');
var baseUri = new Uri(baseUrl);
if (baseUri.Scheme != Uri.UriSchemeHttps && !(baseUri.Scheme == Uri.UriSchemeHttp && (baseUri.Host == "127.0.0.1" || baseUri.Host == "localhost")))
    throw new InvalidOperationException("Use HTTPS for the API; HTTP is allowed only for a local test server.");
using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
using var response = await client.GetAsync(baseUrl + "/api/v1/document-jobs/" + jobId);
response.EnsureSuccessStatusCode();
var body = await response.Content.ReadAsStringAsync();
using var result = JsonDocument.Parse(body);
if (result.RootElement.GetProperty("hasErrors").GetBoolean()) throw new InvalidOperationException("Status request reported an error.");
Console.WriteLine(body);
var data = result.RootElement.GetProperty("data");
if (data.GetProperty("status").GetString() == "Succeeded" && data.TryGetProperty("outputReference", out var reference) && reference.ValueKind == JsonValueKind.String)
{
    using var output = await client.GetAsync(baseUrl + "/api/v1/artifacts/content?reference=" + Uri.EscapeDataString(reference.GetString()!));
    output.EnsureSuccessStatusCode();
    Console.WriteLine(await output.Content.ReadAsStringAsync());
}
