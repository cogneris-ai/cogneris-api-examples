from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import File

T = TypeVar("T", bound="FaceMatchDocumentBody")


@_attrs_define
class FaceMatchDocumentBody:
    """
    Attributes:
        selfie (File): The selfie to compare.
        documents (list[File]): One or more identity documents to compare against.
    """

    selfie: File
    documents: list[File]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        selfie = self.selfie.to_tuple()

        documents = []
        for documents_item_data in self.documents:
            documents_item = documents_item_data.to_tuple()

            documents.append(documents_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "selfie": selfie,
                "documents": documents,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("selfie", self.selfie.to_tuple()))

        for documents_item_element in self.documents:
            files.append(("documents", documents_item_element.to_tuple()))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        selfie = File(payload=BytesIO(d.pop("selfie")))

        documents = []
        _documents = d.pop("documents")
        for documents_item_data in _documents:
            documents_item = File(payload=BytesIO(documents_item_data))

            documents.append(documents_item)

        face_match_document_body = cls(
            selfie=selfie,
            documents=documents,
        )

        face_match_document_body.additional_properties = d
        return face_match_document_body

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
