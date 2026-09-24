from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FaceMatch")


@_attrs_define
class FaceMatch:
    """
    Attributes:
        source_document_id (Union[Unset, UUID]):
        selfie_document_id (Union[Unset, UUID]):
        score (Union[Unset, float]): Similarity between the selfie and the document face.
        matched (Union[Unset, bool]):
        too_many_faces (Union[Unset, bool]):
    """

    source_document_id: Union[Unset, UUID] = UNSET
    selfie_document_id: Union[Unset, UUID] = UNSET
    score: Union[Unset, float] = UNSET
    matched: Union[Unset, bool] = UNSET
    too_many_faces: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_document_id: Union[Unset, str] = UNSET
        if not isinstance(self.source_document_id, Unset):
            source_document_id = str(self.source_document_id)

        selfie_document_id: Union[Unset, str] = UNSET
        if not isinstance(self.selfie_document_id, Unset):
            selfie_document_id = str(self.selfie_document_id)

        score = self.score

        matched = self.matched

        too_many_faces = self.too_many_faces

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_document_id is not UNSET:
            field_dict["sourceDocumentId"] = source_document_id
        if selfie_document_id is not UNSET:
            field_dict["selfieDocumentId"] = selfie_document_id
        if score is not UNSET:
            field_dict["score"] = score
        if matched is not UNSET:
            field_dict["matched"] = matched
        if too_many_faces is not UNSET:
            field_dict["tooManyFaces"] = too_many_faces

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

        _selfie_document_id = d.pop("selfieDocumentId", UNSET)
        selfie_document_id: Union[Unset, UUID]
        if isinstance(_selfie_document_id, Unset):
            selfie_document_id = UNSET
        else:
            selfie_document_id = UUID(_selfie_document_id)

        score = d.pop("score", UNSET)

        matched = d.pop("matched", UNSET)

        too_many_faces = d.pop("tooManyFaces", UNSET)

        face_match = cls(
            source_document_id=source_document_id,
            selfie_document_id=selfie_document_id,
            score=score,
            matched=matched,
            too_many_faces=too_many_faces,
        )

        face_match.additional_properties = d
        return face_match

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
