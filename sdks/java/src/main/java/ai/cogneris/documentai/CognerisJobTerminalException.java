package ai.cogneris.documentai;

import ai.cogneris.documentai.model.DocumentJobStatus;

/** A job failed or was cancelled; the raw job is never retained. */
public final class CognerisJobTerminalException extends CognerisException {
    private final DocumentJobStatus status;

    CognerisJobTerminalException(DocumentJobStatus status) {
        super("Document job reached terminal status " + status + ".");
        this.status = status;
    }

    public DocumentJobStatus getStatus() { return status; }
}
