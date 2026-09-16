from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.document_job_status import DocumentJobStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SubmitDocumentJobResponse202")


@_attrs_define
class SubmitDocumentJobResponse202:
    """
    Attributes:
        job_id (Union[Unset, UUID]):
        status (Union[Unset, DocumentJobStatus]):
        status_url (Union[Unset, str]):
        retry_after_seconds (Union[Unset, int]):
    """

    job_id: Union[Unset, UUID] = UNSET
    status: Union[Unset, DocumentJobStatus] = UNSET
    status_url: Union[Unset, str] = UNSET
    retry_after_seconds: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id: Union[Unset, str] = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        status_url = self.status_url

        retry_after_seconds = self.retry_after_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if status is not UNSET:
            field_dict["status"] = status
        if status_url is not UNSET:
            field_dict["statusUrl"] = status_url
        if retry_after_seconds is not UNSET:
            field_dict["retryAfterSeconds"] = retry_after_seconds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _job_id = d.pop("jobId", UNSET)
        job_id: Union[Unset, UUID]
        if isinstance(_job_id, Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)

        _status = d.pop("status", UNSET)
        status: Union[Unset, DocumentJobStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DocumentJobStatus(_status)

        status_url = d.pop("statusUrl", UNSET)

        retry_after_seconds = d.pop("retryAfterSeconds", UNSET)

        submit_document_job_response_202 = cls(
            job_id=job_id,
            status=status,
            status_url=status_url,
            retry_after_seconds=retry_after_seconds,
        )

        submit_document_job_response_202.additional_properties = d
        return submit_document_job_response_202

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
