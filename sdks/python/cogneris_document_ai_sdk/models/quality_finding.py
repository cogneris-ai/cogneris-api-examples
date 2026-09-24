from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.quality_verdict import QualityVerdict

T = TypeVar("T", bound="QualityFinding")


@_attrs_define
class QualityFinding:
    """
    Attributes:
        probe (str): The check that crossed its threshold, such as `blur` or `resolution`.
        level (QualityVerdict): `0` pass, `1` warn, `2` block. Sent as the number, not the name.
        measured (float):
        threshold (float):
        message (str):
    """

    probe: str
    level: QualityVerdict
    measured: float
    threshold: float
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        probe = self.probe

        level = self.level.value

        measured = self.measured

        threshold = self.threshold

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "probe": probe,
                "level": level,
                "measured": measured,
                "threshold": threshold,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        probe = d.pop("probe")

        level = QualityVerdict(d.pop("level"))

        measured = d.pop("measured")

        threshold = d.pop("threshold")

        message = d.pop("message")

        quality_finding = cls(
            probe=probe,
            level=level,
            measured=measured,
            threshold=threshold,
            message=message,
        )

        quality_finding.additional_properties = d
        return quality_finding

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
