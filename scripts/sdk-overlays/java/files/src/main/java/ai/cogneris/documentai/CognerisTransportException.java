package ai.cogneris.documentai;

/** A request failed at the transport layer or reached its deadline. */
public final class CognerisTransportException extends CognerisException {
    CognerisTransportException(boolean timedOut) {
        super(timedOut ? "Cogneris API request timed out." : "Cogneris API transport failed.");
    }
}
