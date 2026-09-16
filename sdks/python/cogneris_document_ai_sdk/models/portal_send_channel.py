from enum import Enum


class PortalSendChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"

    def __str__(self) -> str:
        return str(self.value)
