from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.envelope_data import EnvelopeData
    from ..models.envelope_meta import EnvelopeMeta


T = TypeVar("T", bound="Envelope")


@_attrs_define
class Envelope:
    """
    Attributes:
        data (Union[Unset, EnvelopeData]):
        meta (Union[Unset, EnvelopeMeta]):
        has_errors (Union[Unset, bool]):
    """

    data: Union[Unset, "EnvelopeData"] = UNSET
    meta: Union[Unset, "EnvelopeMeta"] = UNSET
    has_errors: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        meta: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.meta, Unset):
            meta = self.meta.to_dict()

        has_errors = self.has_errors

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if meta is not UNSET:
            field_dict["meta"] = meta
        if has_errors is not UNSET:
            field_dict["hasErrors"] = has_errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.envelope_data import EnvelopeData
        from ..models.envelope_meta import EnvelopeMeta

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: Union[Unset, EnvelopeData]
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = EnvelopeData.from_dict(_data)

        _meta = d.pop("meta", UNSET)
        meta: Union[Unset, EnvelopeMeta]
        if isinstance(_meta, Unset):
            meta = UNSET
        else:
            meta = EnvelopeMeta.from_dict(_meta)

        has_errors = d.pop("hasErrors", UNSET)

        envelope = cls(
            data=data,
            meta=meta,
            has_errors=has_errors,
        )

        envelope.additional_properties = d
        return envelope

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
