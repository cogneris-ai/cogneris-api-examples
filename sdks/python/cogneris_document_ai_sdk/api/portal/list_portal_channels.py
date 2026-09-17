from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.portal_channels import PortalChannels
from ...models.problem_details import ProblemDetails
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/portal/available-channels",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, PortalChannels, ProblemDetails]]:
    if response.status_code == 200:
        response_200 = PortalChannels.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = ProblemDetails.from_dict(response.json())

        return response_403

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if response.status_code == 502:
        response_502 = ProblemDetails.from_dict(response.json())

        return response_502

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, PortalChannels, ProblemDetails]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, PortalChannels, ProblemDetails]]:
    """List the send channels this environment can use

     The channels available for delivering a magic link. This is a property of the
    environment — it follows the delivery credentials configured there — rather
    than a per-tenant or per-plan entitlement, so it may be shorter than expected.

    WhatsApp additionally requires a Meta-approved template and respects the
    24-hour service window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, PortalChannels, ProblemDetails]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, PortalChannels, ProblemDetails]]:
    """List the send channels this environment can use

     The channels available for delivering a magic link. This is a property of the
    environment — it follows the delivery credentials configured there — rather
    than a per-tenant or per-plan entitlement, so it may be shorter than expected.

    WhatsApp additionally requires a Meta-approved template and respects the
    24-hour service window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, PortalChannels, ProblemDetails]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, PortalChannels, ProblemDetails]]:
    """List the send channels this environment can use

     The channels available for delivering a magic link. This is a property of the
    environment — it follows the delivery credentials configured there — rather
    than a per-tenant or per-plan entitlement, so it may be shorter than expected.

    WhatsApp additionally requires a Meta-approved template and respects the
    24-hour service window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, PortalChannels, ProblemDetails]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, PortalChannels, ProblemDetails]]:
    """List the send channels this environment can use

     The channels available for delivering a magic link. This is a property of the
    environment — it follows the delivery credentials configured there — rather
    than a per-tenant or per-plan entitlement, so it may be shorter than expected.

    WhatsApp additionally requires a Meta-approved template and respects the
    24-hour service window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, PortalChannels, ProblemDetails]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
