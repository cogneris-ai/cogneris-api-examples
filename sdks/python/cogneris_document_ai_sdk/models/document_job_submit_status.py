from enum import Enum


class DocumentJobSubmitStatus(str, Enum):
    QUEUED = "Queued"

    def __str__(self) -> str:
        return str(self.value)
