from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.document_job_submit_operation import DocumentJobSubmitOperation

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
    """

    operation: DocumentJobSubmitOperation
    input_reference: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        input_reference = self.input_reference

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "operation": operation,
                "inputReference": input_reference,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = DocumentJobSubmitOperation(d.pop("operation"))

        input_reference = d.pop("inputReference")

        submit_document_job_body = cls(
            operation=operation,
            input_reference=input_reference,
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
