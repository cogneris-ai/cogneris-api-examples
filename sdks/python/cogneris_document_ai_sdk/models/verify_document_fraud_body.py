from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..models.verify_document_fraud_body_sensitivity import VerifyDocumentFraudBodySensitivity
from ..types import UNSET, File, Unset

T = TypeVar("T", bound="VerifyDocumentFraudBody")


@_attrs_define
class VerifyDocumentFraudBody:
    """
    Attributes:
        file (File): The document, as received from its holder. PDF or image, up to 10 MB.
        sensitivity (Union[Unset, VerifyDocumentFraudBodySensitivity]): How readily signals turn into `review` and
            `suspect`. Default: the
            sensitivity saved on `templateId`, otherwise `medium`.
        template_id (Union[Unset, UUID]): A template whose saved fraud settings supply the default sensitivity.
        reuse (Union[Unset, bool]): Return an earlier analysis of the same file instead of running a new one. Default:
            True.
        fields (Union[Unset, str]): A JSON object of values already extracted from this document, for
            example `{"cpf":"123.456.789-09","issueDate":"2026-02-30"}`. Enables the
            checks on tax ids, dates and totals.
    """

    file: File
    sensitivity: Union[Unset, VerifyDocumentFraudBodySensitivity] = UNSET
    template_id: Union[Unset, UUID] = UNSET
    reuse: Union[Unset, bool] = True
    fields: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file.to_tuple()

        sensitivity: Union[Unset, str] = UNSET
        if not isinstance(self.sensitivity, Unset):
            sensitivity = self.sensitivity.value

        template_id: Union[Unset, str] = UNSET
        if not isinstance(self.template_id, Unset):
            template_id = str(self.template_id)

        reuse = self.reuse

        fields = self.fields

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if sensitivity is not UNSET:
            field_dict["sensitivity"] = sensitivity
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if reuse is not UNSET:
            field_dict["reuse"] = reuse
        if fields is not UNSET:
            field_dict["fields"] = fields

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", self.file.to_tuple()))

        if not isinstance(self.sensitivity, Unset):
            files.append(("sensitivity", (None, str(self.sensitivity.value).encode(), "text/plain")))

        if not isinstance(self.template_id, Unset):
            files.append(("templateId", (None, str(self.template_id).encode(), "text/plain")))

        if not isinstance(self.reuse, Unset):
            files.append(("reuse", (None, str(self.reuse).encode(), "text/plain")))

        if not isinstance(self.fields, Unset):
            files.append(("fields", (None, str(self.fields).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = File(payload=BytesIO(d.pop("file")))

        _sensitivity = d.pop("sensitivity", UNSET)
        sensitivity: Union[Unset, VerifyDocumentFraudBodySensitivity]
        if isinstance(_sensitivity, Unset):
            sensitivity = UNSET
        else:
            sensitivity = VerifyDocumentFraudBodySensitivity(_sensitivity)

        _template_id = d.pop("templateId", UNSET)
        template_id: Union[Unset, UUID]
        if isinstance(_template_id, Unset):
            template_id = UNSET
        else:
            template_id = UUID(_template_id)

        reuse = d.pop("reuse", UNSET)

        fields = d.pop("fields", UNSET)

        verify_document_fraud_body = cls(
            file=file,
            sensitivity=sensitivity,
            template_id=template_id,
            reuse=reuse,
            fields=fields,
        )

        verify_document_fraud_body.additional_properties = d
        return verify_document_fraud_body

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
