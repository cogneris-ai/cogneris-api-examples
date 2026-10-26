from enum import Enum


class FraudVerificationVerdict(str, Enum):
    REVIEW = "review"
    SUSPECT = "suspect"
    TRUSTED = "trusted"

    def __str__(self) -> str:
        return str(self.value)
