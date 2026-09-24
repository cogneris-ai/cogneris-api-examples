from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.document_job_submit_operation import DocumentJobSubmitOperation
from ..types import UNSET, Unset

T = TypeVar("T", bound="SubmitDocumentJobBody")


@_attrs_define
class SubmitDocumentJobBody:
    """
    Attributes:
        operation (DocumentJobSubmitOperation):
        input_reference (str): The `reference` returned by `POST /api/v1/artifacts`. That upload
            is the only way to obtain one, and it can back more than one job
            until it expires.
             Example: artifact://uploads/9f2c1b7a4d8e4f06b1a25c3e7d9f0a11/invoice.pdf.
        template_id (Union[Unset, UUID]): Optional, Extraction only. The id of one of your tenant's finished
            templates; its schema drives the extraction instead of the template
            the platform would select from the document. Any other operation
            rejects the submit when this is set. An id the platform cannot resolve
            to a finished template of yours is rejected; the job never falls back
            to a generic extraction without the schema you asked for.
    """

    operation: DocumentJobSubmitOperation
    input_reference: str
    template_id: Union[Unset, UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        input_reference = self.input_reference

        template_id: Union[Unset, str] = UNSET
        if not isinstance(self.template_id, Unset):
            template_id = str(self.template_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "operation": operation,
                "inputReference": input_reference,
            }
        )
        if template_id is not UNSET:
            field_dict["templateId"] = template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = DocumentJobSubmitOperation(d.pop("operation"))

        input_reference = d.pop("inputReference")

        _template_id = d.pop("templateId", UNSET)
        template_id: Union[Unset, UUID]
        if isinstance(_template_id, Unset):
            template_id = UNSET
        else:
            template_id = UUID(_template_id)

        submit_document_job_body = cls(
            operation=operation,
            input_reference=input_reference,
            template_id=template_id,
        )

        submit_document_job_body.additional_properties = d
        return submit_document_job_body

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
