from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EnvelopeMeta")


@_attrs_define
class EnvelopeMeta:
    """
    Attributes:
        http_status_code (Union[Unset, int]):
        messages (Union[Unset, list[str]]):
    """

    http_status_code: Union[Unset, int] = UNSET
    messages: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        http_status_code = self.http_status_code

        messages: Union[Unset, list[str]] = UNSET
        if not isinstance(self.messages, Unset):
            messages = self.messages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if http_status_code is not UNSET:
            field_dict["httpStatusCode"] = http_status_code
        if messages is not UNSET:
            field_dict["messages"] = messages

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        http_status_code = d.pop("httpStatusCode", UNSET)

        messages = cast(list[str], d.pop("messages", UNSET))

        envelope_meta = cls(
            http_status_code=http_status_code,
            messages=messages,
        )

        envelope_meta.additional_properties = d
        return envelope_meta

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
