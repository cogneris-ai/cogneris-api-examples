from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClassificationResult")


@_attrs_define
class ClassificationResult:
    """
    Attributes:
        file_name (Union[Unset, str]): The uploaded file this entry classifies.
        document_type (Union[Unset, str]):
        confidence (Union[Unset, float]): Certainty in `documentType`.
        pages (Union[None, Unset, int]):
        template_id (Union[None, UUID, Unset]): The template the document type resolves to, when one is configured.
        template_metadata (Union[None, Unset, str]): The matched template's schema. Null when `templateId` is, or the
            template has no schema yet.
    """

    file_name: Union[Unset, str] = UNSET
    document_type: Union[Unset, str] = UNSET
    confidence: Union[Unset, float] = UNSET
    pages: Union[None, Unset, int] = UNSET
    template_id: Union[None, UUID, Unset] = UNSET
    template_metadata: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_name = self.file_name

        document_type = self.document_type

        confidence = self.confidence

        pages: Union[None, Unset, int]
        if isinstance(self.pages, Unset):
            pages = UNSET
        else:
            pages = self.pages

        template_id: Union[None, Unset, str]
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        elif isinstance(self.template_id, UUID):
            template_id = str(self.template_id)
        else:
            template_id = self.template_id

        template_metadata: Union[None, Unset, str]
        if isinstance(self.template_metadata, Unset):
            template_metadata = UNSET
        else:
            template_metadata = self.template_metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_name is not UNSET:
            field_dict["fileName"] = file_name
        if document_type is not UNSET:
            field_dict["documentType"] = document_type
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if pages is not UNSET:
            field_dict["pages"] = pages
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if template_metadata is not UNSET:
            field_dict["templateMetadata"] = template_metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_name = d.pop("fileName", UNSET)

        document_type = d.pop("documentType", UNSET)

        confidence = d.pop("confidence", UNSET)

        def _parse_pages(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pages = _parse_pages(d.pop("pages", UNSET))

        def _parse_template_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                template_id_type_0 = UUID(data)

                return template_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        template_id = _parse_template_id(d.pop("templateId", UNSET))

        def _parse_template_metadata(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        template_metadata = _parse_template_metadata(d.pop("templateMetadata", UNSET))

        classification_result = cls(
            file_name=file_name,
            document_type=document_type,
            confidence=confidence,
            pages=pages,
            template_id=template_id,
            template_metadata=template_metadata,
        )

        classification_result.additional_properties = d
        return classification_result

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
