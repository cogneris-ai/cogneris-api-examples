package ai.cogneris.documentai;

/** Polling exhausted its configured request limit. */
public final class CognerisMaxAttemptsException extends CognerisException {
    private final int attempts;

    CognerisMaxAttemptsException(int attempts) {
        super("Document job did not reach a terminal state after " + attempts + " attempts.");
        this.attempts = attempts;
    }

    public int getAttempts() { return attempts; }
}
