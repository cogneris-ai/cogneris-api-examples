package ai.cogneris.documentai;

/** A response could not be decoded or did not match the successful contract. */
public final class CognerisResponseException extends CognerisException {
    CognerisResponseException() {
        super("Cogneris API response did not match the public contract.");
    }
}
