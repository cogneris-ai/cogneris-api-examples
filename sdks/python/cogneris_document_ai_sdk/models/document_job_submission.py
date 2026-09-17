from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.document_job_status import DocumentJobStatus

T = TypeVar("T", bound="DocumentJobSubmission")


@_attrs_define
class DocumentJobSubmission:
    """
    Attributes:
        job_id (UUID):
        status (DocumentJobStatus):
        status_url (str):
        retry_after_seconds (int):
    """

    job_id: UUID
    status: DocumentJobStatus
    status_url: str
    retry_after_seconds: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id = str(self.job_id)

        status = self.status.value

        status_url = self.status_url

        retry_after_seconds = self.retry_after_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobId": job_id,
                "status": status,
                "statusUrl": status_url,
                "retryAfterSeconds": retry_after_seconds,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_id = UUID(d.pop("jobId"))

        status = DocumentJobStatus(d.pop("status"))

        status_url = d.pop("statusUrl")

        retry_after_seconds = d.pop("retryAfterSeconds")

        document_job_submission = cls(
            job_id=job_id,
            status=status,
            status_url=status_url,
            retry_after_seconds=retry_after_seconds,
        )

        document_job_submission.additional_properties = d
        return document_job_submission

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
