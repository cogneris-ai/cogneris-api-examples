from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CropDocument")


@_attrs_define
class CropDocument:
    """
    Attributes:
        box_2d (Union[Unset, list[int]]): Where the document sits on the source image.
        mask (Union[Unset, list[list[int]]]): The document's outline on the source image, as a list of points.
        side (Union[Unset, str]):
        type_ (Union[Unset, str]): The detected document type.
        confidence (Union[None, Unset, float]):
        image_url (Union[Unset, str]): Signed URL of this document's crop.
    """

    box_2d: Union[Unset, list[int]] = UNSET
    mask: Union[Unset, list[list[int]]] = UNSET
    side: Union[Unset, str] = UNSET
    type_: Union[Unset, str] = UNSET
    confidence: Union[None, Unset, float] = UNSET
    image_url: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        box_2d: Union[Unset, list[int]] = UNSET
        if not isinstance(self.box_2d, Unset):
            box_2d = self.box_2d

        mask: Union[Unset, list[list[int]]] = UNSET
        if not isinstance(self.mask, Unset):
            mask = []
            for mask_item_data in self.mask:
                mask_item = mask_item_data

                mask.append(mask_item)

        side = self.side

        type_ = self.type_

        confidence: Union[None, Unset, float]
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        image_url = self.image_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if box_2d is not UNSET:
            field_dict["box2D"] = box_2d
        if mask is not UNSET:
            field_dict["mask"] = mask
        if side is not UNSET:
            field_dict["side"] = side
        if type_ is not UNSET:
            field_dict["type"] = type_
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if image_url is not UNSET:
            field_dict["imageUrl"] = image_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        box_2d = cast(list[int], d.pop("box2D", UNSET))

        mask = []
        _mask = d.pop("mask", UNSET)
        for mask_item_data in _mask or []:
            mask_item = cast(list[int], mask_item_data)

            mask.append(mask_item)

        side = d.pop("side", UNSET)

        type_ = d.pop("type", UNSET)

        def _parse_confidence(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        image_url = d.pop("imageUrl", UNSET)

        crop_document = cls(
            box_2d=box_2d,
            mask=mask,
            side=side,
            type_=type_,
            confidence=confidence,
            image_url=image_url,
        )

        crop_document.additional_properties = d
        return crop_document

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
