from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.portal_magic_link import PortalMagicLink
from ...models.portal_magic_link_request import PortalMagicLinkRequest
from ...models.problem_details import ProblemDetails
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PortalMagicLinkRequest,
    idempotency_key: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/portal/magic-link",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, PortalMagicLink, ProblemDetails]]:
    if response.status_code == 201:
        response_201 = PortalMagicLink.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 402:
        response_402 = cast(Any, None)
        return response_402

    if response.status_code == 403:
        response_403 = ProblemDetails.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

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
) -> Response[Union[Any, PortalMagicLink, ProblemDetails]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PortalMagicLinkRequest,
    idempotency_key: Union[Unset, str] = UNSET,
) -> Response[Union[Any, PortalMagicLink, ProblemDetails]]:
    """Create a magic link

     Creates a link to an intake form for a named recipient and, when `sendChannel`
    is set, dispatches it on that channel. Omit `sendChannel` to create the link
    without sending anything and deliver it yourself.

    Send a stable `Idempotency-Key` to make retries safe: a repeat resolves to the
    same link rather than creating a second one or charging twice.

    `url` is returned **only on the first create**. The raw token is never stored
    in readable form, so an idempotent replay returns the same `id` with `url`
    absent — persist it from the original `201`.

    Args:
        idempotency_key (Union[Unset, str]):
        body (PortalMagicLinkRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, PortalMagicLink, ProblemDetails]]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PortalMagicLinkRequest,
    idempotency_key: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, PortalMagicLink, ProblemDetails]]:
    """Create a magic link

     Creates a link to an intake form for a named recipient and, when `sendChannel`
    is set, dispatches it on that channel. Omit `sendChannel` to create the link
    without sending anything and deliver it yourself.

    Send a stable `Idempotency-Key` to make retries safe: a repeat resolves to the
    same link rather than creating a second one or charging twice.

    `url` is returned **only on the first create**. The raw token is never stored
    in readable form, so an idempotent replay returns the same `id` with `url`
    absent — persist it from the original `201`.

    Args:
        idempotency_key (Union[Unset, str]):
        body (PortalMagicLinkRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, PortalMagicLink, ProblemDetails]
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PortalMagicLinkRequest,
    idempotency_key: Union[Unset, str] = UNSET,
) -> Response[Union[Any, PortalMagicLink, ProblemDetails]]:
    """Create a magic link

     Creates a link to an intake form for a named recipient and, when `sendChannel`
    is set, dispatches it on that channel. Omit `sendChannel` to create the link
    without sending anything and deliver it yourself.

    Send a stable `Idempotency-Key` to make retries safe: a repeat resolves to the
    same link rather than creating a second one or charging twice.

    `url` is returned **only on the first create**. The raw token is never stored
    in readable form, so an idempotent replay returns the same `id` with `url`
    absent — persist it from the original `201`.

    Args:
        idempotency_key (Union[Unset, str]):
        body (PortalMagicLinkRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, PortalMagicLink, ProblemDetails]]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PortalMagicLinkRequest,
    idempotency_key: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, PortalMagicLink, ProblemDetails]]:
    """Create a magic link

     Creates a link to an intake form for a named recipient and, when `sendChannel`
    is set, dispatches it on that channel. Omit `sendChannel` to create the link
    without sending anything and deliver it yourself.

    Send a stable `Idempotency-Key` to make retries safe: a repeat resolves to the
    same link rather than creating a second one or charging twice.

    `url` is returned **only on the first create**. The raw token is never stored
    in readable form, so an idempotent replay returns the same `id` with `url`
    absent — persist it from the original `201`.

    Args:
        idempotency_key (Union[Unset, str]):
        body (PortalMagicLinkRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, PortalMagicLink, ProblemDetails]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
