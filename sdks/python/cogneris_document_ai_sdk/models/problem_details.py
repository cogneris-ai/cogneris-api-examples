from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.problem_details_errors_item import ProblemDetailsErrorsItem


T = TypeVar("T", bound="ProblemDetails")


@_attrs_define
class ProblemDetails:
    """RFC 9457 problem document, sent as `application/problem+json`.

    Attributes:
        type_ (Union[Unset, str]): Opaque stable identifier for the error class.
        title (Union[Unset, str]):
        status (Union[Unset, int]):
        detail (Union[None, Unset, str]):
        instance (Union[Unset, str]): The path that produced the error.
        code (Union[Unset, str]): Stable machine-readable error code — branch on this.
        correlation_id (Union[Unset, str]): Also returned in the `x-correlation-id` header.
        retryable (Union[Unset, bool]):
        field (Union[None, Unset, str]): The request field at fault, on validation failures.
        errors (Union[Unset, list['ProblemDetailsErrorsItem']]):
    """

    type_: Union[Unset, str] = UNSET
    title: Union[Unset, str] = UNSET
    status: Union[Unset, int] = UNSET
    detail: Union[None, Unset, str] = UNSET
    instance: Union[Unset, str] = UNSET
    code: Union[Unset, str] = UNSET
    correlation_id: Union[Unset, str] = UNSET
    retryable: Union[Unset, bool] = UNSET
    field: Union[None, Unset, str] = UNSET
    errors: Union[Unset, list["ProblemDetailsErrorsItem"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        title = self.title

        status = self.status

        detail: Union[None, Unset, str]
        if isinstance(self.detail, Unset):
            detail = UNSET
        else:
            detail = self.detail

        instance = self.instance

        code = self.code

        correlation_id = self.correlation_id

        retryable = self.retryable

        field: Union[None, Unset, str]
        if isinstance(self.field, Unset):
            field = UNSET
        else:
            field = self.field

        errors: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.errors, Unset):
            errors = []
            for errors_item_data in self.errors:
                errors_item = errors_item_data.to_dict()
                errors.append(errors_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if title is not UNSET:
            field_dict["title"] = title
        if status is not UNSET:
            field_dict["status"] = status
        if detail is not UNSET:
            field_dict["detail"] = detail
        if instance is not UNSET:
            field_dict["instance"] = instance
        if code is not UNSET:
            field_dict["code"] = code
        if correlation_id is not UNSET:
            field_dict["correlationId"] = correlation_id
        if retryable is not UNSET:
            field_dict["retryable"] = retryable
        if field is not UNSET:
            field_dict["field"] = field
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.problem_details_errors_item import ProblemDetailsErrorsItem

        d = dict(src_dict)
        type_ = d.pop("type", UNSET)

        title = d.pop("title", UNSET)

        status = d.pop("status", UNSET)

        def _parse_detail(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        detail = _parse_detail(d.pop("detail", UNSET))

        instance = d.pop("instance", UNSET)

        code = d.pop("code", UNSET)

        correlation_id = d.pop("correlationId", UNSET)

        retryable = d.pop("retryable", UNSET)

        def _parse_field(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        field = _parse_field(d.pop("field", UNSET))

        errors = []
        _errors = d.pop("errors", UNSET)
        for errors_item_data in _errors or []:
            errors_item = ProblemDetailsErrorsItem.from_dict(errors_item_data)

            errors.append(errors_item)

        problem_details = cls(
            type_=type_,
            title=title,
            status=status,
            detail=detail,
            instance=instance,
            code=code,
            correlation_id=correlation_id,
            retryable=retryable,
            field=field,
            errors=errors,
        )

        problem_details.additional_properties = d
        return problem_details

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
