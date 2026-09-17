from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.envelope import Envelope
from ...models.split_document_body import SplitDocumentBody
from ...types import Response


def _get_kwargs(
    *,
    body: SplitDocumentBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/Document/split",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Envelope]]:
    if response.status_code == 200:
        response_200 = Envelope.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 413:
        response_413 = cast(Any, None)
        return response_413

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, Envelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SplitDocumentBody,
) -> Response[Union[Any, Envelope]]:
    """Split a bundle into its documents

     Breaks one file into the documents it contains, returning a detected type and
    page range per segment. Accepts files up to 500 MB — well above the 10 MB
    limit that applies to the other document endpoints. PDFs work best; other
    supported formats are accepted but usually return a single segment.

    Args:
        body (SplitDocumentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Envelope]]
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
    body: SplitDocumentBody,
) -> Optional[Union[Any, Envelope]]:
    """Split a bundle into its documents

     Breaks one file into the documents it contains, returning a detected type and
    page range per segment. Accepts files up to 500 MB — well above the 10 MB
    limit that applies to the other document endpoints. PDFs work best; other
    supported formats are accepted but usually return a single segment.

    Args:
        body (SplitDocumentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Envelope]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SplitDocumentBody,
) -> Response[Union[Any, Envelope]]:
    """Split a bundle into its documents

     Breaks one file into the documents it contains, returning a detected type and
    page range per segment. Accepts files up to 500 MB — well above the 10 MB
    limit that applies to the other document endpoints. PDFs work best; other
    supported formats are accepted but usually return a single segment.

    Args:
        body (SplitDocumentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Envelope]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SplitDocumentBody,
) -> Optional[Union[Any, Envelope]]:
    """Split a bundle into its documents

     Breaks one file into the documents it contains, returning a detected type and
    page range per segment. Accepts files up to 500 MB — well above the 10 MB
    limit that applies to the other document endpoints. PDFs work best; other
    supported formats are accepted but usually return a single segment.

    Args:
        body (SplitDocumentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Envelope]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
