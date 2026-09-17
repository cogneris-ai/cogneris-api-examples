from enum import Enum


class DocumentJobOperation(str, Enum):
    CLASSIFICATION = "Classification"
    CROP = "Crop"
    EXTRACTION = "Extraction"
    SPLIT = "Split"
    ZEROSHOT = "ZeroShot"

    def __str__(self) -> str:
        return str(self.value)
