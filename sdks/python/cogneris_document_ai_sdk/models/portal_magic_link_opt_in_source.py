from enum import Enum


class PortalMagicLinkOptInSource(str, Enum):
    API = "api"
    CONTRACT = "contract"
    IMPORT = "import"
    IN_PERSON = "in_person"
    WEB_FORM = "web_form"

    def __str__(self) -> str:
        return str(self.value)
