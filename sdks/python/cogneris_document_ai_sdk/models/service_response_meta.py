from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_error import ApiError


T = TypeVar("T", bound="ServiceResponseMeta")


@_attrs_define
class ServiceResponseMeta:
    """
    Attributes:
        http_status_code (int):
        messages (Union[Unset, list[str]]):
        errors (Union[Unset, list['ApiError']]):
        credits_consumed (Union[None, Unset, float]):
    """

    http_status_code: int
    messages: Union[Unset, list[str]] = UNSET
    errors: Union[Unset, list["ApiError"]] = UNSET
    credits_consumed: Union[None, Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        http_status_code = self.http_status_code

        messages: Union[Unset, list[str]] = UNSET
        if not isinstance(self.messages, Unset):
            messages = self.messages

        errors: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.errors, Unset):
            errors = []
            for errors_item_data in self.errors:
                errors_item = errors_item_data.to_dict()
                errors.append(errors_item)

        credits_consumed: Union[None, Unset, float]
        if isinstance(self.credits_consumed, Unset):
            credits_consumed = UNSET
        else:
            credits_consumed = self.credits_consumed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "httpStatusCode": http_status_code,
            }
        )
        if messages is not UNSET:
            field_dict["messages"] = messages
        if errors is not UNSET:
            field_dict["errors"] = errors
        if credits_consumed is not UNSET:
            field_dict["creditsConsumed"] = credits_consumed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_error import ApiError

        d = dict(src_dict)
        http_status_code = d.pop("httpStatusCode")

        messages = cast(list[str], d.pop("messages", UNSET))

        errors = []
        _errors = d.pop("errors", UNSET)
        for errors_item_data in _errors or []:
            errors_item = ApiError.from_dict(errors_item_data)

            errors.append(errors_item)

        def _parse_credits_consumed(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        credits_consumed = _parse_credits_consumed(d.pop("creditsConsumed", UNSET))

        service_response_meta = cls(
            http_status_code=http_status_code,
            messages=messages,
            errors=errors,
            credits_consumed=credits_consumed,
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
