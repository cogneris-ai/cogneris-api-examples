from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.problem_details import ProblemDetails
from ...models.webhook_endpoint_envelope import WebhookEndpointEnvelope
from ...models.webhook_endpoint_update_request import WebhookEndpointUpdateRequest
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    body: WebhookEndpointUpdateRequest,
    idempotency_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/webhook-endpoints/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProblemDetails, WebhookEndpointEnvelope]]:
    if response.status_code == 200:
        response_200 = WebhookEndpointEnvelope.from_dict(response.json())

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
) -> Response[Union[ProblemDetails, WebhookEndpointEnvelope]]:
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
    body: WebhookEndpointUpdateRequest,
    idempotency_key: str,
) -> Response[Union[ProblemDetails, WebhookEndpointEnvelope]]:
    """Replace a webhook endpoint

     Replaces every field. **Changing `url` rotates the signing secret**, and the
    new one is returned as `data.secret` on this response only. Deliveries already
    in flight were signed with the old secret, so accept both until they drain.
    An update that keeps the `url` keeps the secret and returns `secret: null`.

    `Idempotency-Key` is required, with the same replay rules as the create.

    Args:
        id (UUID):
        idempotency_key (str):
        body (WebhookEndpointUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointEnvelope]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: WebhookEndpointUpdateRequest,
    idempotency_key: str,
) -> Optional[Union[ProblemDetails, WebhookEndpointEnvelope]]:
    """Replace a webhook endpoint

     Replaces every field. **Changing `url` rotates the signing secret**, and the
    new one is returned as `data.secret` on this response only. Deliveries already
    in flight were signed with the old secret, so accept both until they drain.
    An update that keeps the `url` keeps the secret and returns `secret: null`.

    `Idempotency-Key` is required, with the same replay rules as the create.

    Args:
        id (UUID):
        idempotency_key (str):
        body (WebhookEndpointUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointEnvelope]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: WebhookEndpointUpdateRequest,
    idempotency_key: str,
) -> Response[Union[ProblemDetails, WebhookEndpointEnvelope]]:
    """Replace a webhook endpoint

     Replaces every field. **Changing `url` rotates the signing secret**, and the
    new one is returned as `data.secret` on this response only. Deliveries already
    in flight were signed with the old secret, so accept both until they drain.
    An update that keeps the `url` keeps the secret and returns `secret: null`.

    `Idempotency-Key` is required, with the same replay rules as the create.

    Args:
        id (UUID):
        idempotency_key (str):
        body (WebhookEndpointUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointEnvelope]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: WebhookEndpointUpdateRequest,
    idempotency_key: str,
) -> Optional[Union[ProblemDetails, WebhookEndpointEnvelope]]:
    """Replace a webhook endpoint

     Replaces every field. **Changing `url` rotates the signing secret**, and the
    new one is returned as `data.secret` on this response only. Deliveries already
    in flight were signed with the old secret, so accept both until they drain.
    An update that keeps the `url` keeps the secret and returns `secret: null`.

    `Idempotency-Key` is required, with the same replay rules as the create.

    Args:
        id (UUID):
        idempotency_key (str):
        body (WebhookEndpointUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointEnvelope]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
