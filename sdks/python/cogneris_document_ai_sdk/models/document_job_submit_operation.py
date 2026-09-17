from enum import Enum


class DocumentJobSubmitOperation(str, Enum):
    CLASSIFICATION = "Classification"
    CROP = "Crop"
    EXTRACTION = "Extraction"
    FACEMATCH = "Facematch"
    SPLIT = "Split"
    ZEROSHOT = "ZeroShot"

    def __str__(self) -> str:
        return str(self.value)
