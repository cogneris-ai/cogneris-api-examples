from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fraud_check_status import FraudCheckStatus

if TYPE_CHECKING:
    from ..models.fraud_signal import FraudSignal


T = TypeVar("T", bound="FraudCheck")


@_attrs_define
class FraudCheck:
    """
    Attributes:
        name (str): The check, for example `pdf_structure`, `image_ela`, `c2pa_provenance`, `pdf_signature`, `semantic`.
        status (FraudCheckStatus):
        signals (list['FraudSignal']):
    """

    name: str
    status: FraudCheckStatus
    signals: list["FraudSignal"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        status = self.status.value

        signals = []
        for signals_item_data in self.signals:
            signals_item = signals_item_data.to_dict()
            signals.append(signals_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "status": status,
                "signals": signals,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fraud_signal import FraudSignal

        d = dict(src_dict)
        name = d.pop("name")

        status = FraudCheckStatus(d.pop("status"))

        signals = []
        _signals = d.pop("signals")
        for signals_item_data in _signals:
            signals_item = FraudSignal.from_dict(signals_item_data)

            signals.append(signals_item)

        fraud_check = cls(
            name=name,
            status=status,
            signals=signals,
        )

        fraud_check.additional_properties = d
        return fraud_check

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
