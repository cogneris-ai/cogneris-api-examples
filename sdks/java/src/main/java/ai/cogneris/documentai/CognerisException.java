package ai.cogneris.documentai;

/** A sanitized failure from the maintained Cogneris facade. */
public abstract class CognerisException extends RuntimeException {
    CognerisException(String message) {
        // Neither an unsafe cause nor suppressed failures can be attached.
        super(message, null, false, true);
    }
}
