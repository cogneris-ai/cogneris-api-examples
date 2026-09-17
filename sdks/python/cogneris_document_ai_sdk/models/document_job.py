import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.document_job_operation import DocumentJobOperation
from ..models.document_job_status import DocumentJobStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="DocumentJob")


@_attrs_define
class DocumentJob:
    """
    Attributes:
        job_id (Union[Unset, UUID]):
        operation (Union[Unset, DocumentJobOperation]):
        status (Union[Unset, DocumentJobStatus]):
        output_reference (Union[None, Unset, str]):
        stage (Union[None, Unset, str]):
        processed_pages (Union[None, Unset, int]):
        total_pages (Union[None, Unset, int]):
        attempt_count (Union[Unset, int]):
        failure_code (Union[None, Unset, str]):
        retryable (Union[Unset, bool]):
        started_at (Union[None, Unset, datetime.datetime]):
        completed_at (Union[None, Unset, datetime.datetime]):
        cancellation_requested_at (Union[None, Unset, datetime.datetime]):
        expires_at (Union[Unset, datetime.datetime]):
    """

    job_id: Union[Unset, UUID] = UNSET
    operation: Union[Unset, DocumentJobOperation] = UNSET
    status: Union[Unset, DocumentJobStatus] = UNSET
    output_reference: Union[None, Unset, str] = UNSET
    stage: Union[None, Unset, str] = UNSET
    processed_pages: Union[None, Unset, int] = UNSET
    total_pages: Union[None, Unset, int] = UNSET
    attempt_count: Union[Unset, int] = UNSET
    failure_code: Union[None, Unset, str] = UNSET
    retryable: Union[Unset, bool] = UNSET
    started_at: Union[None, Unset, datetime.datetime] = UNSET
    completed_at: Union[None, Unset, datetime.datetime] = UNSET
    cancellation_requested_at: Union[None, Unset, datetime.datetime] = UNSET
    expires_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id: Union[Unset, str] = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        operation: Union[Unset, str] = UNSET
        if not isinstance(self.operation, Unset):
            operation = self.operation.value

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        output_reference: Union[None, Unset, str]
        if isinstance(self.output_reference, Unset):
            output_reference = UNSET
        else:
            output_reference = self.output_reference

        stage: Union[None, Unset, str]
        if isinstance(self.stage, Unset):
            stage = UNSET
        else:
            stage = self.stage

        processed_pages: Union[None, Unset, int]
        if isinstance(self.processed_pages, Unset):
            processed_pages = UNSET
        else:
            processed_pages = self.processed_pages

        total_pages: Union[None, Unset, int]
        if isinstance(self.total_pages, Unset):
            total_pages = UNSET
        else:
            total_pages = self.total_pages

        attempt_count = self.attempt_count

        failure_code: Union[None, Unset, str]
        if isinstance(self.failure_code, Unset):
            failure_code = UNSET
        else:
            failure_code = self.failure_code

        retryable = self.retryable

        started_at: Union[None, Unset, str]
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        completed_at: Union[None, Unset, str]
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        cancellation_requested_at: Union[None, Unset, str]
        if isinstance(self.cancellation_requested_at, Unset):
            cancellation_requested_at = UNSET
        elif isinstance(self.cancellation_requested_at, datetime.datetime):
            cancellation_requested_at = self.cancellation_requested_at.isoformat()
        else:
            cancellation_requested_at = self.cancellation_requested_at

        expires_at: Union[Unset, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if operation is not UNSET:
            field_dict["operation"] = operation
        if status is not UNSET:
            field_dict["status"] = status
        if output_reference is not UNSET:
            field_dict["outputReference"] = output_reference
        if stage is not UNSET:
            field_dict["stage"] = stage
        if processed_pages is not UNSET:
            field_dict["processedPages"] = processed_pages
        if total_pages is not UNSET:
            field_dict["totalPages"] = total_pages
        if attempt_count is not UNSET:
            field_dict["attemptCount"] = attempt_count
        if failure_code is not UNSET:
            field_dict["failureCode"] = failure_code
        if retryable is not UNSET:
            field_dict["retryable"] = retryable
        if started_at is not UNSET:
            field_dict["startedAt"] = started_at
        if completed_at is not UNSET:
            field_dict["completedAt"] = completed_at
        if cancellation_requested_at is not UNSET:
            field_dict["cancellationRequestedAt"] = cancellation_requested_at
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at

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

        _operation = d.pop("operation", UNSET)
        operation: Union[Unset, DocumentJobOperation]
        if isinstance(_operation, Unset):
            operation = UNSET
        else:
            operation = DocumentJobOperation(_operation)

        _status = d.pop("status", UNSET)
        status: Union[Unset, DocumentJobStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DocumentJobStatus(_status)

        def _parse_output_reference(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        output_reference = _parse_output_reference(d.pop("outputReference", UNSET))

        def _parse_stage(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        stage = _parse_stage(d.pop("stage", UNSET))

        def _parse_processed_pages(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        processed_pages = _parse_processed_pages(d.pop("processedPages", UNSET))

        def _parse_total_pages(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        total_pages = _parse_total_pages(d.pop("totalPages", UNSET))

        attempt_count = d.pop("attemptCount", UNSET)

        def _parse_failure_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        failure_code = _parse_failure_code(d.pop("failureCode", UNSET))

        retryable = d.pop("retryable", UNSET)

        def _parse_started_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        started_at = _parse_started_at(d.pop("startedAt", UNSET))

        def _parse_completed_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        completed_at = _parse_completed_at(d.pop("completedAt", UNSET))

        def _parse_cancellation_requested_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                cancellation_requested_at_type_0 = isoparse(data)

                return cancellation_requested_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        cancellation_requested_at = _parse_cancellation_requested_at(d.pop("cancellationRequestedAt", UNSET))

        _expires_at = d.pop("expiresAt", UNSET)
        expires_at: Union[Unset, datetime.datetime]
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        document_job = cls(
            job_id=job_id,
            operation=operation,
            status=status,
            output_reference=output_reference,
            stage=stage,
            processed_pages=processed_pages,
            total_pages=total_pages,
            attempt_count=attempt_count,
            failure_code=failure_code,
            retryable=retryable,
            started_at=started_at,
            completed_at=completed_at,
            cancellation_requested_at=cancellation_requested_at,
            expires_at=expires_at,
        )

        document_job.additional_properties = d
        return document_job

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
