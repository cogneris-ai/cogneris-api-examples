from enum import Enum


class FraudVerificationPolicyAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    FLAG = "flag"

    def __str__(self) -> str:
        return str(self.value)
