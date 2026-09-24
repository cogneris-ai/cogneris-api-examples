from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.problem_details_errors_item_details_type_0 import ProblemDetailsErrorsItemDetailsType0


T = TypeVar("T", bound="ProblemDetailsErrorsItem")


@_attrs_define
class ProblemDetailsErrorsItem:
    """
    Attributes:
        code (Union[Unset, str]):
        message (Union[Unset, str]):
        field (Union[None, Unset, str]): Present on validation failures.
        retryable (Union[Unset, bool]):
        details (Union['ProblemDetailsErrorsItemDetailsType0', None, Unset]):
    """

    code: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    field: Union[None, Unset, str] = UNSET
    retryable: Union[Unset, bool] = UNSET
    details: Union["ProblemDetailsErrorsItemDetailsType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.problem_details_errors_item_details_type_0 import ProblemDetailsErrorsItemDetailsType0

        code = self.code

        message = self.message

        field: Union[None, Unset, str]
        if isinstance(self.field, Unset):
            field = UNSET
        else:
            field = self.field

        retryable = self.retryable

        details: Union[None, Unset, dict[str, Any]]
        if isinstance(self.details, Unset):
            details = UNSET
        elif isinstance(self.details, ProblemDetailsErrorsItemDetailsType0):
            details = self.details.to_dict()
        else:
            details = self.details

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
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.problem_details_errors_item_details_type_0 import ProblemDetailsErrorsItemDetailsType0

        d = dict(src_dict)
        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        def _parse_field(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        field = _parse_field(d.pop("field", UNSET))

        retryable = d.pop("retryable", UNSET)

        def _parse_details(data: object) -> Union["ProblemDetailsErrorsItemDetailsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                details_type_0 = ProblemDetailsErrorsItemDetailsType0.from_dict(data)

                return details_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ProblemDetailsErrorsItemDetailsType0", None, Unset], data)

        details = _parse_details(d.pop("details", UNSET))

        problem_details_errors_item = cls(
            code=code,
            message=message,
            field=field,
            retryable=retryable,
            details=details,
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
