from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.quality_verdict import QualityVerdict

if TYPE_CHECKING:
    from ..models.quality_finding import QualityFinding


T = TypeVar("T", bound="QualityAssessment")


@_attrs_define
class QualityAssessment:
    """
    Attributes:
        overall (QualityVerdict): `0` pass, `1` warn, `2` block. Sent as the number, not the name.
        findings (list['QualityFinding']): Each probe that did not pass. Passing probes are left out.
    """

    overall: QualityVerdict
    findings: list["QualityFinding"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        overall = self.overall.value

        findings = []
        for findings_item_data in self.findings:
            findings_item = findings_item_data.to_dict()
            findings.append(findings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "overall": overall,
                "findings": findings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.quality_finding import QualityFinding

        d = dict(src_dict)
        overall = QualityVerdict(d.pop("overall"))

        findings = []
        _findings = d.pop("findings")
        for findings_item_data in _findings:
            findings_item = QualityFinding.from_dict(findings_item_data)

            findings.append(findings_item)

        quality_assessment = cls(
            overall=overall,
            findings=findings,
        )

        quality_assessment.additional_properties = d
        return quality_assessment

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
