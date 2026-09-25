from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.problem_details import ProblemDetails
from ...models.webhook_endpoint_create_request import WebhookEndpointCreateRequest
from ...models.webhook_endpoint_created_envelope import WebhookEndpointCreatedEnvelope
from ...types import Response


def _get_kwargs(
    *,
    body: WebhookEndpointCreateRequest,
    idempotency_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/webhook-endpoints",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    if response.status_code == 200:
        response_200 = WebhookEndpointCreatedEnvelope.from_dict(response.json())

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
) -> Response[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: WebhookEndpointCreateRequest,
    idempotency_key: str,
) -> Response[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    """Register a webhook endpoint

     Registers an endpoint and returns its signing secret. **This is the only
    time the secret is shown** — store it before you close the response.

    `Idempotency-Key` is required. Repeating the request with the same key and
    body returns the same endpoint and the same secret, with
    `Idempotency-Replayed: true`; the same key with a different body answers
    `409`.

    Args:
        idempotency_key (str):
        body (WebhookEndpointCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]
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
    body: WebhookEndpointCreateRequest,
    idempotency_key: str,
) -> Optional[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    """Register a webhook endpoint

     Registers an endpoint and returns its signing secret. **This is the only
    time the secret is shown** — store it before you close the response.

    `Idempotency-Key` is required. Repeating the request with the same key and
    body returns the same endpoint and the same secret, with
    `Idempotency-Replayed: true`; the same key with a different body answers
    `409`.

    Args:
        idempotency_key (str):
        body (WebhookEndpointCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointCreatedEnvelope]
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: WebhookEndpointCreateRequest,
    idempotency_key: str,
) -> Response[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    """Register a webhook endpoint

     Registers an endpoint and returns its signing secret. **This is the only
    time the secret is shown** — store it before you close the response.

    `Idempotency-Key` is required. Repeating the request with the same key and
    body returns the same endpoint and the same secret, with
    `Idempotency-Replayed: true`; the same key with a different body answers
    `409`.

    Args:
        idempotency_key (str):
        body (WebhookEndpointCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]
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
    body: WebhookEndpointCreateRequest,
    idempotency_key: str,
) -> Optional[Union[ProblemDetails, WebhookEndpointCreatedEnvelope]]:
    """Register a webhook endpoint

     Registers an endpoint and returns its signing secret. **This is the only
    time the secret is shown** — store it before you close the response.

    `Idempotency-Key` is required. Repeating the request with the same key and
    body returns the same endpoint and the same secret, with
    `Idempotency-Replayed: true`; the same key with a different body answers
    `409`.

    Args:
        idempotency_key (str):
        body (WebhookEndpointCreateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, WebhookEndpointCreatedEnvelope]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed
