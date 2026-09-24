from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FaceExtraction")


@_attrs_define
class FaceExtraction:
    """
    Attributes:
        source_document_id (Union[Unset, UUID]):
        has_face (Union[Unset, bool]):
        document_type (Union[Unset, str]):
        crop_signed_url (Union[None, Unset, str]): Signed URL of the face crop. Null when none was produced.
    """

    source_document_id: Union[Unset, UUID] = UNSET
    has_face: Union[Unset, bool] = UNSET
    document_type: Union[Unset, str] = UNSET
    crop_signed_url: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_document_id: Union[Unset, str] = UNSET
        if not isinstance(self.source_document_id, Unset):
            source_document_id = str(self.source_document_id)

        has_face = self.has_face

        document_type = self.document_type

        crop_signed_url: Union[None, Unset, str]
        if isinstance(self.crop_signed_url, Unset):
            crop_signed_url = UNSET
        else:
            crop_signed_url = self.crop_signed_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_document_id is not UNSET:
            field_dict["sourceDocumentId"] = source_document_id
        if has_face is not UNSET:
            field_dict["hasFace"] = has_face
        if document_type is not UNSET:
            field_dict["documentType"] = document_type
        if crop_signed_url is not UNSET:
            field_dict["cropSignedUrl"] = crop_signed_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _source_document_id = d.pop("sourceDocumentId", UNSET)
        source_document_id: Union[Unset, UUID]
        if isinstance(_source_document_id, Unset):
            source_document_id = UNSET
        else:
            source_document_id = UUID(_source_document_id)

        has_face = d.pop("hasFace", UNSET)

        document_type = d.pop("documentType", UNSET)

        def _parse_crop_signed_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        crop_signed_url = _parse_crop_signed_url(d.pop("cropSignedUrl", UNSET))

        face_extraction = cls(
            source_document_id=source_document_id,
            has_face=has_face,
            document_type=document_type,
            crop_signed_url=crop_signed_url,
        )

        face_extraction.additional_properties = d
        return face_extraction

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
