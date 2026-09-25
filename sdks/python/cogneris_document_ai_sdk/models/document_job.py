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
        template_id (Union[None, UUID, Unset]): The finished extraction template explicitly selected when the job was
            submitted. Null when the job did not use a template. Obtain available ids
            from `GET /api/v1/templates`; synchronous `/Document/*` endpoints always
            select a tenant template from the document and do not take this parameter.
        output_reference (Union[None, Unset, str]): Where the finished result is stored, as an `artifact://` reference.
            Read it
            with `GET /api/v1/artifacts/content`. Null until the job succeeds, and always
            null for `Redaction`, which has its own download route.

            For `Extraction` and `ZeroShot` its field entries are the same
            `ExtractedField` objects a synchronous call returns for that document — same
            source-coordinate convention, same `0`-`100` confidence scale.

            The stored `result.json` is not the response envelope and does not repeat its
            casing: it holds the extraction result directly, with `Metadata` where the
            synchronous body has `data.metadata`. The field names inside are your
            template's either way.

            Jobs that completed before 2026-09-22 carry a bucket-qualified path rather
            than an `artifact://` reference; the download accepts both.
             Example: artifact://document-jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7/result.json.
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
        credits_consumed (Union[None, Unset, float]): What the job consumed, in credits. Absent — never `0` — while the
            cost is
            unknown: a job still queued or running, an operation that is not metered,
            or one billing could not price. `0` is a real value meaning the job was
            free. It is a property of the job, so polling a finished job twice reports
            the same figure; it is not a charge per read.
    """

    job_id: Union[Unset, UUID] = UNSET
    operation: Union[Unset, DocumentJobOperation] = UNSET
    status: Union[Unset, DocumentJobStatus] = UNSET
    template_id: Union[None, UUID, Unset] = UNSET
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
    credits_consumed: Union[None, Unset, float] = UNSET
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

        template_id: Union[None, Unset, str]
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        elif isinstance(self.template_id, UUID):
            template_id = str(self.template_id)
        else:
            template_id = self.template_id

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

        credits_consumed: Union[None, Unset, float]
        if isinstance(self.credits_consumed, Unset):
            credits_consumed = UNSET
        else:
            credits_consumed = self.credits_consumed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if operation is not UNSET:
            field_dict["operation"] = operation
        if status is not UNSET:
            field_dict["status"] = status
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
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
        if credits_consumed is not UNSET:
            field_dict["creditsConsumed"] = credits_consumed

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

        def _parse_credits_consumed(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        credits_consumed = _parse_credits_consumed(d.pop("creditsConsumed", UNSET))

        document_job = cls(
            job_id=job_id,
            operation=operation,
            status=status,
            template_id=template_id,
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
            credits_consumed=credits_consumed,
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
