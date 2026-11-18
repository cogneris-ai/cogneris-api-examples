using System.Net;
using System.Security.Cryptography;
using System.Text;

var secret = Environment.GetEnvironmentVariable("COGNERIS_WEBHOOK_SECRET");
if (string.IsNullOrEmpty(secret)) throw new InvalidOperationException("Set COGNERIS_WEBHOOK_SECRET in the environment.");
var port = int.Parse(Environment.GetEnvironmentVariable("WEBHOOK_PORT") ?? "8080");
var seen = new HashSet<string>(); // Demonstration only: production needs durable atomic deduplication.
using var listener = new HttpListener();
listener.Prefixes.Add($"http://127.0.0.1:{port}/");
listener.Start();
while (true)
{
    var context = await listener.GetContextAsync();
    var request = context.Request;
    try
    {
        if (request.HttpMethod != "POST" || request.ContentLength64 < 0 || request.ContentLength64 > 1024 * 1024) throw new InvalidOperationException();
        using var buffer = new MemoryStream();
        await request.InputStream.CopyToAsync(buffer);
        var parts = (request.Headers["X-Xtrakt-Signature"] ?? "").Split(',');
        if (parts.Length != 2 || !parts[0].StartsWith("t=") || !parts[1].StartsWith("v1=") || !long.TryParse(parts[0][2..], out var timestamp)) throw new InvalidOperationException();
        if (Math.Abs(DateTimeOffset.UtcNow.ToUnixTimeSeconds() - timestamp) > 300) throw new InvalidOperationException();
        var prefix = Encoding.UTF8.GetBytes(timestamp.ToString() + ".");
        var payload = buffer.ToArray();
        var signed = new byte[prefix.Length + payload.Length];
        Buffer.BlockCopy(prefix, 0, signed, 0, prefix.Length); Buffer.BlockCopy(payload, 0, signed, prefix.Length, payload.Length);
        var expected = HMACSHA256.HashData(Encoding.UTF8.GetBytes(secret), signed);
        var supplied = Convert.FromHexString(parts[1][3..]);
        if (!CryptographicOperations.FixedTimeEquals(expected, supplied)) throw new InvalidOperationException();
        var delivery = request.Headers["X-Xtrakt-Delivery"];
        if (string.IsNullOrEmpty(delivery) || delivery.Length > 200) throw new InvalidOperationException();
        if (seen.Add(delivery)) { /* Process only after durable deduplication in a real application. */ }
        context.Response.StatusCode = 200;
    }
    catch (Exception ex) when (ex is InvalidOperationException or FormatException or OverflowException)
    {
        context.Response.StatusCode = 401;
    }
    context.Response.ContentLength64 = 0;
    context.Response.Close();
}
