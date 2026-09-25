from enum import Enum


class WebhookEvent(str, Enum):
    CLASSIFIER_FAILED = "classifier.failed"
    CLASSIFIER_PROCESSED = "classifier.processed"
    CROP_FAILED = "crop.failed"
    CROP_PROCESSED = "crop.processed"
    EXTRACT_FAILED = "extract.failed"
    EXTRACT_PROCESSED = "extract.processed"
    FACEMATCH_FAILED = "facematch.failed"
    FACEMATCH_PROCESSED = "facematch.processed"
    REDACTION_FAILED = "redaction.failed"
    REDACTION_PROCESSED = "redaction.processed"
    SPLIT_FAILED = "split.failed"
    SPLIT_PROCESSED = "split.processed"
    ZEROSHOT_FAILED = "zeroshot.failed"
    ZEROSHOT_PROCESSED = "zeroshot.processed"

    def __str__(self) -> str:
        return str(self.value)
