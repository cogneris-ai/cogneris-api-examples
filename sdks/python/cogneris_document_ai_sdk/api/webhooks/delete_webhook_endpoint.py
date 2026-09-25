from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.problem_details import ProblemDetails
from ...models.webhook_endpoint_deletion_envelope import WebhookEndpointDeletionEnvelope
from ...types import Response


def _get_kwargs(
    id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/api/v1/webhook-endpoints/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    if response.status_code == 200:
        response_200 = WebhookEndpointDeletionEnvelope.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ProblemDetails.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ProblemDetails.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ProblemDetails.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ProblemDetails.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ProblemDetails.from_dict(response.json())

        return response_409

    if response.status_code == 429:
        response_429 = ProblemDetails.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ProblemDetails.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    """Remove a webhook endpoint

    Args:
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    """Remove a webhook endpoint

    Args:
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointDeletionEnvelope]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    """Remove a webhook endpoint

    Args:
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[ProblemDetails, WebhookEndpointDeletionEnvelope]]:
    """Remove a webhook endpoint

    Args:
        id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointDeletionEnvelope]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
