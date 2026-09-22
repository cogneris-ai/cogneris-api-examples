from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExtractedField")


@_attrs_define
class ExtractedField:
    """One extracted field: the value, how certain the model is of it, and where on the
    document it was read from. These are the objects that fill `data.metadata`, and
    the cells inside a table-shaped field's `items` rows.

    The three location keys are present or absent together — see `data.metadata` for
    the coordinate convention they follow.

        Example:
            {'value': '254H089SJ425', 'confidence': 98, 'page': 1, 'bbox': [0.62, 0.11, 0.83, 0.14], 'bbox_confidence': 92}

        Attributes:
            value (Union[None, Unset, str]): The extracted value, or `null` when the field was not found.
            confidence (Union[Unset, float]): Certainty in the value, from `0` to `100`. This is the one confidence scale
                the API uses; `bbox_confidence` is on the same one.
            page (Union[Unset, int]): 1-indexed page the value was read from. Absent when the value could not be
                located on the page.
            bbox (Union[Unset, list[float]]): Where a value sits on its page, as `[x0, y0, x1, y1]` fractions of the page
                size
                with the origin at the top-left: `x0,y0` is the top-left corner and `x1,y1` the
                bottom-right. Fractions rather than pixels, so the box survives any rendering
                scale — multiply by the width and height you draw the page at.
                 Example: [0.62, 0.11, 0.83, 0.14].
            bbox_confidence (Union[Unset, float]): Certainty in the location, from `0` to `100` — the same scale as
                `confidence`,
                not a `0`–`1` fraction. Absent whenever `bbox` is.
    """

    value: Union[None, Unset, str] = UNSET
    confidence: Union[Unset, float] = UNSET
    page: Union[Unset, int] = UNSET
    bbox: Union[Unset, list[float]] = UNSET
    bbox_confidence: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value: Union[None, Unset, str]
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        confidence = self.confidence

        page = self.page

        bbox: Union[Unset, list[float]] = UNSET
        if not isinstance(self.bbox, Unset):
            bbox = self.bbox

        bbox_confidence = self.bbox_confidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if value is not UNSET:
            field_dict["value"] = value
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if page is not UNSET:
            field_dict["page"] = page
        if bbox is not UNSET:
            field_dict["bbox"] = bbox
        if bbox_confidence is not UNSET:
            field_dict["bbox_confidence"] = bbox_confidence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_value(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        value = _parse_value(d.pop("value", UNSET))

        confidence = d.pop("confidence", UNSET)

        page = d.pop("page", UNSET)

        bbox = cast(list[float], d.pop("bbox", UNSET))

        bbox_confidence = d.pop("bbox_confidence", UNSET)

        extracted_field = cls(
            value=value,
            confidence=confidence,
            page=page,
            bbox=bbox,
            bbox_confidence=bbox_confidence,
        )

        extracted_field.additional_properties = d
        return extracted_field

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
