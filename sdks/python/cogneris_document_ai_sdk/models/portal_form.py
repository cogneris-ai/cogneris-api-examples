from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PortalForm")


@_attrs_define
class PortalForm:
    """
    Attributes:
        form_id (Union[Unset, int]):
        form_name (Union[Unset, str]):
        form_description (Union[None, Unset, str]):
    """

    form_id: Union[Unset, int] = UNSET
    form_name: Union[Unset, str] = UNSET
    form_description: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        form_id = self.form_id

        form_name = self.form_name

        form_description: Union[None, Unset, str]
        if isinstance(self.form_description, Unset):
            form_description = UNSET
        else:
            form_description = self.form_description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if form_id is not UNSET:
            field_dict["formId"] = form_id
        if form_name is not UNSET:
            field_dict["formName"] = form_name
        if form_description is not UNSET:
            field_dict["formDescription"] = form_description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        form_id = d.pop("formId", UNSET)

        form_name = d.pop("formName", UNSET)

        def _parse_form_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        form_description = _parse_form_description(d.pop("formDescription", UNSET))

        portal_form = cls(
            form_id=form_id,
            form_name=form_name,
            form_description=form_description,
        )

        portal_form.additional_properties = d
        return portal_form

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
