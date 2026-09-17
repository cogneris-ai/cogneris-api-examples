package ai.cogneris.documentai;

/** An unexpected HTTP status, without response content or credentials. */
public final class CognerisApiException extends CognerisException {
    private final int statusCode;

    CognerisApiException(int statusCode) {
        super("Cogneris API returned HTTP " + statusCode + ".");
        this.statusCode = statusCode;
    }

    public int getStatusCode() { return statusCode; }
}
