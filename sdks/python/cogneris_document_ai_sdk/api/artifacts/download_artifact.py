from http import HTTPStatus
from io import BytesIO
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.service_error_envelope import ServiceErrorEnvelope
from ...types import UNSET, File, Response


def _get_kwargs(
    *,
    reference: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["reference"] = reference

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/artifacts/content",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, File, ServiceErrorEnvelope]]:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

        return response_200

    if response.status_code == 400:
        response_400 = ServiceErrorEnvelope.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 410:
        response_410 = ServiceErrorEnvelope.from_dict(response.json())

        return response_410

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, File, ServiceErrorEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    reference: str,
) -> Response[Union[Any, File, ServiceErrorEnvelope]]:
    """Download the bytes behind a reference

     Returns the stored bytes of an upload, or of a finished job's
    `outputReference`. For a completed job this is the result document —
    `application/json` for the extraction, classification and zero-shot
    operations.

    The reference is a query parameter, not a path segment, because it is a URI
    in its own right. Percent-encode it.

    Args:
        reference (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, File, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        reference=reference,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    reference: str,
) -> Optional[Union[Any, File, ServiceErrorEnvelope]]:
    """Download the bytes behind a reference

     Returns the stored bytes of an upload, or of a finished job's
    `outputReference`. For a completed job this is the result document —
    `application/json` for the extraction, classification and zero-shot
    operations.

    The reference is a query parameter, not a path segment, because it is a URI
    in its own right. Percent-encode it.

    Args:
        reference (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, File, ServiceErrorEnvelope]
    """

    return sync_detailed(
        client=client,
        reference=reference,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    reference: str,
) -> Response[Union[Any, File, ServiceErrorEnvelope]]:
    """Download the bytes behind a reference

     Returns the stored bytes of an upload, or of a finished job's
    `outputReference`. For a completed job this is the result document —
    `application/json` for the extraction, classification and zero-shot
    operations.

    The reference is a query parameter, not a path segment, because it is a URI
    in its own right. Percent-encode it.

    Args:
        reference (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, File, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        reference=reference,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    reference: str,
) -> Optional[Union[Any, File, ServiceErrorEnvelope]]:
    """Download the bytes behind a reference

     Returns the stored bytes of an upload, or of a finished job's
    `outputReference`. For a completed job this is the result document —
    `application/json` for the extraction, classification and zero-shot
    operations.

    The reference is a query parameter, not a path segment, because it is a URI
    in its own right. Percent-encode it.

    Args:
        reference (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, File, ServiceErrorEnvelope]
    """

    return (
        await asyncio_detailed(
            client=client,
            reference=reference,
        )
    ).parsed
