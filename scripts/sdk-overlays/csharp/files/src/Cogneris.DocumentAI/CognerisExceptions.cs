using System;
using System.Net;
using Cogneris.DocumentAI.Model;

namespace Cogneris.DocumentAI;

/// <summary>A sanitized failure from the maintained Cogneris facade.</summary>
public abstract class CognerisException : Exception
{
    internal CognerisException(string message) : base(message) { }
}

/// <summary>The server returned an unexpected HTTP status.</summary>
public sealed class CognerisApiException : CognerisException
{
    /// <summary>The HTTP status, without response content or credentials.</summary>
    public HttpStatusCode StatusCode { get; }

    internal CognerisApiException(HttpStatusCode statusCode)
        : base($"Cogneris API returned HTTP {(int)statusCode}.") => StatusCode = statusCode;
}

/// <summary>The response did not match the successful public contract.</summary>
public sealed class CognerisResponseException : CognerisException
{
    internal CognerisResponseException() : base("Cogneris API response did not match the public contract.") { }
}

/// <summary>A request could not complete because of a transport failure.</summary>
public sealed class CognerisTransportException : CognerisException
{
    internal CognerisTransportException() : base("Cogneris API transport failed.") { }
}

/// <summary>A job reached Failed or Cancelled instead of Succeeded.</summary>
public sealed class CognerisJobTerminalException : CognerisException
{
    /// <summary>The terminal status; the raw job and its messages are not retained.</summary>
    public DocumentJobStatus Status { get; }

    internal CognerisJobTerminalException(DocumentJobStatus status)
        : base($"Document job reached terminal status {status}.") => Status = status;
}

/// <summary>Polling reached the configured attempt bound.</summary>
public sealed class CognerisMaxAttemptsException : CognerisException
{
    /// <summary>The number of requests permitted by the caller.</summary>
    public int Attempts { get; }

    internal CognerisMaxAttemptsException(int attempts)
        : base($"Document job did not reach a terminal state after {attempts} attempts.") => Attempts = attempts;
}
