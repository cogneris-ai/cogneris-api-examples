from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template import Template


T = TypeVar("T", bound="TemplateList")


@_attrs_define
class TemplateList:
    """
    Attributes:
        templates (list['Template']):
        has_more (bool):
        limit (int):
        next_cursor (Union[None, Unset, str]):
    """

    templates: list["Template"]
    has_more: bool
    limit: int
    next_cursor: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        templates = []
        for templates_item_data in self.templates:
            templates_item = templates_item_data.to_dict()
            templates.append(templates_item)

        has_more = self.has_more

        limit = self.limit

        next_cursor: Union[None, Unset, str]
        if isinstance(self.next_cursor, Unset):
            next_cursor = UNSET
        else:
            next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "templates": templates,
                "hasMore": has_more,
                "limit": limit,
            }
        )
        if next_cursor is not UNSET:
            field_dict["nextCursor"] = next_cursor

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template import Template

        d = dict(src_dict)
        templates = []
        _templates = d.pop("templates")
        for templates_item_data in _templates:
            templates_item = Template.from_dict(templates_item_data)

            templates.append(templates_item)

        has_more = d.pop("hasMore")

        limit = d.pop("limit")

        def _parse_next_cursor(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor", UNSET))

        template_list = cls(
            templates=templates,
            has_more=has_more,
            limit=limit,
            next_cursor=next_cursor,
        )

        template_list.additional_properties = d
        return template_list

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
