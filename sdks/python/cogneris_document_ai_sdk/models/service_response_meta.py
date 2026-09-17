from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.service_response_meta_errors_item import ServiceResponseMetaErrorsItem


T = TypeVar("T", bound="ServiceResponseMeta")


@_attrs_define
class ServiceResponseMeta:
    """
    Attributes:
        http_status_code (int):
        messages (list[str]):
        errors (list['ServiceResponseMetaErrorsItem']):
    """

    http_status_code: int
    messages: list[str]
    errors: list["ServiceResponseMetaErrorsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        http_status_code = self.http_status_code

        messages = self.messages

        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "httpStatusCode": http_status_code,
                "messages": messages,
                "errors": errors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_response_meta_errors_item import ServiceResponseMetaErrorsItem

        d = dict(src_dict)
        http_status_code = d.pop("httpStatusCode")

        messages = cast(list[str], d.pop("messages"))

        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = ServiceResponseMetaErrorsItem.from_dict(errors_item_data)

            errors.append(errors_item)

        service_response_meta = cls(
            http_status_code=http_status_code,
            messages=messages,
            errors=errors,
        )

        service_response_meta.additional_properties = d
        return service_response_meta

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
