from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProblemDetailsErrorsItem")


@_attrs_define
class ProblemDetailsErrorsItem:
    """
    Attributes:
        code (Union[Unset, str]):
        message (Union[Unset, str]):
        field (Union[Unset, str]): Present on validation failures.
        retryable (Union[Unset, bool]):
    """

    code: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    field: Union[Unset, str] = UNSET
    retryable: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        message = self.message

        field = self.field

        retryable = self.retryable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message
        if field is not UNSET:
            field_dict["field"] = field
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        field = d.pop("field", UNSET)

        retryable = d.pop("retryable", UNSET)

        problem_details_errors_item = cls(
            code=code,
            message=message,
            field=field,
            retryable=retryable,
        )

        problem_details_errors_item.additional_properties = d
        return problem_details_errors_item

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
