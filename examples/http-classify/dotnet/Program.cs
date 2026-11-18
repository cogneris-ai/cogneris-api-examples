using System.Net.Http.Headers;
using System.Text.Json;

if (args.Length != 1) throw new ArgumentException("Usage: dotnet run -- DOCUMENT.pdf");
var key = Environment.GetEnvironmentVariable("COGNERIS_API_KEY");
if (string.IsNullOrWhiteSpace(key)) throw new InvalidOperationException("Set COGNERIS_API_KEY in the environment.");
var baseUrl = (Environment.GetEnvironmentVariable("COGNERIS_API_BASE") ?? "https://api-eu.cogneris.ai").TrimEnd('/');
var baseUri = new Uri(baseUrl);
if (baseUri.Scheme != Uri.UriSchemeHttps && !(baseUri.Scheme == Uri.UriSchemeHttp && (baseUri.Host == "127.0.0.1" || baseUri.Host == "localhost")))
    throw new InvalidOperationException("Use HTTPS for the API; HTTP is allowed only for a local test server.");
using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
await using var input = File.OpenRead(args[0]);
using var file = new StreamContent(input);
file.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
using var form = new MultipartFormDataContent();
form.Add(file, "files", Path.GetFileName(args[0]));
using var response = await client.PostAsync(baseUrl + "/Document/classifier", form);
response.EnsureSuccessStatusCode();
var body = await response.Content.ReadAsStringAsync();
using var result = JsonDocument.Parse(body);
if (result.RootElement.GetProperty("hasErrors").GetBoolean()) throw new InvalidOperationException("Classification reported an error.");
Console.WriteLine(body);
