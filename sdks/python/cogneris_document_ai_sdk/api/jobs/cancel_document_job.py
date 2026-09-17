from http import HTTPStatus
from typing import Any, Optional, Union, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.document_job import DocumentJob
from ...types import Response


def _get_kwargs(
    job_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/document-jobs/{job_id}/cancel",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, DocumentJob]]:
    if response.status_code == 200:
        response_200 = DocumentJob.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, DocumentJob]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, DocumentJob]]:
    """Cancel a document job

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, DocumentJob]]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, DocumentJob]]:
    """Cancel a document job

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, DocumentJob]
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    job_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, DocumentJob]]:
    """Cancel a document job

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, DocumentJob]]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, DocumentJob]]:
    """Cancel a document job

    Args:
        job_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, DocumentJob]
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
        )
    ).parsed
