from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.submit_document_job_body import SubmitDocumentJobBody
from ...models.submit_document_job_response_202 import SubmitDocumentJobResponse202
from ...types import Response


def _get_kwargs(
    *,
    body: SubmitDocumentJobBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/document-jobs",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, SubmitDocumentJobResponse202]]:
    if response.status_code == 202:
        response_202 = SubmitDocumentJobResponse202.from_dict(response.json())

        return response_202

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, SubmitDocumentJobResponse202]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubmitDocumentJobBody,
) -> Response[Union[Any, SubmitDocumentJobResponse202]]:
    """Submit an asynchronous document job

     Queues a long-running operation. Answers `202` with a `Location` header
    pointing at the job and a `Retry-After` hint. Poll that URL, or subscribe to
    webhooks and let the completion event come to you.

    Args:
        body (SubmitDocumentJobBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SubmitDocumentJobResponse202]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubmitDocumentJobBody,
) -> Optional[Union[Any, SubmitDocumentJobResponse202]]:
    """Submit an asynchronous document job

     Queues a long-running operation. Answers `202` with a `Location` header
    pointing at the job and a `Retry-After` hint. Poll that URL, or subscribe to
    webhooks and let the completion event come to you.

    Args:
        body (SubmitDocumentJobBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SubmitDocumentJobResponse202]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubmitDocumentJobBody,
) -> Response[Union[Any, SubmitDocumentJobResponse202]]:
    """Submit an asynchronous document job

     Queues a long-running operation. Answers `202` with a `Location` header
    pointing at the job and a `Retry-After` hint. Poll that URL, or subscribe to
    webhooks and let the completion event come to you.

    Args:
        body (SubmitDocumentJobBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SubmitDocumentJobResponse202]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubmitDocumentJobBody,
) -> Optional[Union[Any, SubmitDocumentJobResponse202]]:
    """Submit an asynchronous document job

     Queues a long-running operation. Answers `202` with a `Location` header
    pointing at the job and a `Retry-After` hint. Poll that URL, or subscribe to
    webhooks and let the completion event come to you.

    Args:
        body (SubmitDocumentJobBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SubmitDocumentJobResponse202]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
