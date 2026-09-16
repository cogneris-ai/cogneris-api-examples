import io
import json
import time
from collections.abc import Mapping
from typing import BinaryIO, Optional, Union
from urllib.parse import urlsplit
from uuid import UUID

from .api.documents import extract_document
from .api.jobs import cancel_document_job, get_document_job, submit_document_job
from .client import AuthenticatedClient
from .models.document_job import DocumentJob
from .models.document_job_operation import DocumentJobOperation
from .models.document_job_status import DocumentJobStatus
from .models.envelope import Envelope
from .models.extract_document_body import ExtractDocumentBody
from .models.submit_document_job_body import SubmitDocumentJobBody
from .models.submit_document_job_response_202 import SubmitDocumentJobResponse202
from .types import File, Response


COGNERIS_REGION_URLS: Mapping[str, str] = {
    "us": "https://api-us.cogneris.ai",
    "eu": "https://api-eu.cogneris.ai",
}


def cogneris_base_url(region: str) -> str:
    """Return the public API base URL for a supported region."""
    if region not in COGNERIS_REGION_URLS:
        raise ValueError('region must be either "us" or "eu".')
    return COGNERIS_REGION_URLS[region]


class CognerisError(Exception):
    """Base error for the maintained Cogneris helper surface."""


class CognerisApiError(CognerisError):
    """An actionable HTTP/API failure without request credentials or content."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: Optional[str] = None,
        retryable: Optional[bool] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable


class CognerisJobTerminalError(CognerisError):
    """A job stopped in Failed or Cancelled instead of succeeding."""

    def __init__(self, job: DocumentJob) -> None:
        status = str(job.status)
        failure_code = job.failure_code if isinstance(job.failure_code, str) else None
        suffix = f" ({failure_code})" if failure_code else ""
        super().__init__(f"Document job reached terminal status {status}{suffix}.")
        self.job = job
        self.failure_code = failure_code


class CognerisMaxAttemptsError(CognerisError):
    """Polling reached its configured attempt bound."""

    def __init__(self, attempts: int) -> None:
        super().__init__(f"Document job did not reach a terminal state after {attempts} attempts.")
        self.attempts = attempts


def _loopback_base_url(value: str) -> str:
    hostname = urlsplit(value).hostname
    if hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("_base_url_for_testing accepts loopback hosts only.")
    return value.rstrip("/")


def _api_error(response: Response[object]) -> CognerisApiError:
    payload = None
    try:
        payload = json.loads(response.content)
    except (TypeError, ValueError, UnicodeDecodeError):
        pass
    problem = payload if isinstance(payload, dict) else {}
    code = problem.get("code") if isinstance(problem.get("code"), str) else None
    title = problem.get("title") if isinstance(problem.get("title"), str) else None
    retryable = problem.get("retryable") if isinstance(problem.get("retryable"), bool) else None
    label = title or code or f"HTTP {int(response.status_code)}"
    return CognerisApiError(
        f"Cogneris API request failed: {label}.",
        status=int(response.status_code),
        code=code,
        retryable=retryable,
    )


def _require_data(response: Response[object], expected_type: type):
    if 200 <= int(response.status_code) < 300 and isinstance(response.parsed, expected_type):
        return response.parsed
    raise _api_error(response)


def _retry_after(response: Response[object], fallback: float) -> float:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return fallback
    try:
        seconds = float(raw)
    except ValueError:
        return fallback
    return seconds if seconds >= 0 else fallback


class CognerisClient:
    """Small synchronous client for the public first-result and job flows."""

    def __init__(
        self,
        *,
        api_key: str,
        region: str = "us",
        _base_url_for_testing: Optional[str] = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key must be a non-empty string.")
        self.region = region
        base_url = (
            _loopback_base_url(_base_url_for_testing)
            if _base_url_for_testing is not None
            else cogneris_base_url(region)
        )
        self._client = AuthenticatedClient(base_url=base_url, token=api_key)

    def extract(
        self,
        content: Union[bytes, BinaryIO],
        *,
        file_name: str,
        content_type: Optional[str] = None,
        complementary_prompt: Optional[str] = None,
    ) -> Envelope:
        payload = content if hasattr(content, "read") else io.BytesIO(content)
        body = ExtractDocumentBody(file=File(payload=payload, file_name=file_name, mime_type=content_type))
        if complementary_prompt is not None:
            body.complementary_prompt = complementary_prompt
        response = extract_document.sync_detailed(client=self._client, body=body)
        return _require_data(response, Envelope)

    def submit_job(
        self,
        operation: Union[str, DocumentJobOperation],
        input_reference: str,
    ) -> SubmitDocumentJobResponse202:
        parsed_operation = operation if isinstance(operation, DocumentJobOperation) else DocumentJobOperation(operation)
        response = submit_document_job.sync_detailed(
            client=self._client,
            body=SubmitDocumentJobBody(operation=parsed_operation, input_reference=input_reference),
        )
        return _require_data(response, SubmitDocumentJobResponse202)

    def get_job(self, job_id: Union[str, UUID]) -> DocumentJob:
        response = self._get_job_detailed(job_id)
        return _require_data(response, DocumentJob)

    def wait_for_job(
        self,
        job_id: Union[str, UUID],
        *,
        max_attempts: int = 20,
        poll_interval_seconds: float = 1.0,
    ) -> DocumentJob:
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer.")
        if poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be non-negative.")

        for attempt in range(1, max_attempts + 1):
            response = self._get_job_detailed(job_id)
            job = _require_data(response, DocumentJob)
            if job.status == DocumentJobStatus.SUCCEEDED:
                return job
            if job.status in {DocumentJobStatus.FAILED, DocumentJobStatus.CANCELLED}:
                raise CognerisJobTerminalError(job)
            if attempt < max_attempts:
                time.sleep(_retry_after(response, poll_interval_seconds))
        raise CognerisMaxAttemptsError(max_attempts)

    def cancel_job(self, job_id: Union[str, UUID]) -> DocumentJob:
        response = cancel_document_job.sync_detailed(self._job_uuid(job_id), client=self._client)
        return _require_data(response, DocumentJob)

    def close(self) -> None:
        self._client.get_httpx_client().close()

    def _get_job_detailed(self, job_id: Union[str, UUID]):
        return get_document_job.sync_detailed(self._job_uuid(job_id), client=self._client)

    @staticmethod
    def _job_uuid(job_id: Union[str, UUID]) -> UUID:
        return job_id if isinstance(job_id, UUID) else UUID(job_id)


__all__ = [
    "COGNERIS_REGION_URLS",
    "CognerisApiError",
    "CognerisClient",
    "CognerisError",
    "CognerisJobTerminalError",
    "CognerisMaxAttemptsError",
    "cogneris_base_url",
]
