from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, Unset

T = TypeVar("T", bound="ExtractDocumentBody")


@_attrs_define
class ExtractDocumentBody:
    """
    Attributes:
        file (File): The document to extract from.
        complementary_prompt (Union[Unset, str]): Free-text instruction appended to the model prompt. Use it to ask
            for extra fields, enforce formatting, or narrow the scope.
             Example: Also return the payment terms and the PO number..
    """

    file: File
    complementary_prompt: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file.to_tuple()

        complementary_prompt = self.complementary_prompt

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if complementary_prompt is not UNSET:
            field_dict["ComplementaryPrompt"] = complementary_prompt

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", self.file.to_tuple()))

        if not isinstance(self.complementary_prompt, Unset):
            files.append(("ComplementaryPrompt", (None, str(self.complementary_prompt).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = File(payload=BytesIO(d.pop("file")))

        complementary_prompt = d.pop("ComplementaryPrompt", UNSET)

        extract_document_body = cls(
            file=file,
            complementary_prompt=complementary_prompt,
        )

        extract_document_body.additional_properties = d
        return extract_document_body

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
