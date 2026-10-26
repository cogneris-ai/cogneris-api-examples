from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fraud_signal_severity import FraudSignalSeverity

T = TypeVar("T", bound="FraudSignal")


@_attrs_define
class FraudSignal:
    """
    Attributes:
        code (str): Stable signal code, for example `pdf_incremental_updates` or `duplicate_document`.
        label (str): The signal in plain English, for example "PDF edited after it was created".
        severity (FraudSignalSeverity):
        score (float):
        evidence (str): What was found, in a sentence.
    """

    code: str
    label: str
    severity: FraudSignalSeverity
    score: float
    evidence: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        label = self.label

        severity = self.severity.value

        score = self.score

        evidence = self.evidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "label": label,
                "severity": severity,
                "score": score,
                "evidence": evidence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        label = d.pop("label")

        severity = FraudSignalSeverity(d.pop("severity"))

        score = d.pop("score")

        evidence = d.pop("evidence")

        fraud_signal = cls(
            code=code,
            label=label,
            severity=severity,
            score=score,
            evidence=evidence,
        )

        fraud_signal.additional_properties = d
        return fraud_signal

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
