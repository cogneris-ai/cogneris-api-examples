from enum import Enum


class TemplateStatus(str, Enum):
    FINISHED = "Finished"

    def __str__(self) -> str:
        return str(self.value)
