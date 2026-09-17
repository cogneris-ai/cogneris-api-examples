from enum import Enum


class DocumentJobStatus(str, Enum):
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    PROCESSING = "Processing"
    QUEUED = "Queued"
    SUCCEEDED = "Succeeded"

    def __str__(self) -> str:
        return str(self.value)
