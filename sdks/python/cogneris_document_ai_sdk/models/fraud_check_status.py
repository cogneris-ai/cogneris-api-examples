from enum import Enum


class FraudCheckStatus(str, Enum):
    CLEAR = "clear"
    FAILED = "failed"
    FLAGGED = "flagged"

    def __str__(self) -> str:
        return str(self.value)
