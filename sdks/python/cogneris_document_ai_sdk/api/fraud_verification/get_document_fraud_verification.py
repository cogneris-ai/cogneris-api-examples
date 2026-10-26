from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.fraud_verification_envelope import FraudVerificationEnvelope
from ...models.problem_details import ProblemDetails
from ...models.service_error_envelope import ServiceErrorEnvelope
from ...types import Response


def _get_kwargs(
    request_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/fraud-verify/{request_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    if response.status_code == 200:
        response_200 = FraudVerificationEnvelope.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ProblemDetails.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ProblemDetails.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ServiceErrorEnvelope.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ServiceErrorEnvelope.from_dict(response.json())

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

    if response.status_code == 502:
        response_502 = ServiceErrorEnvelope.from_dict(response.json())

        return response_502

    if response.status_code == 503:
        response_503 = ServiceErrorEnvelope.from_dict(response.json())

        return response_503

    if response.status_code == 504:
        response_504 = ServiceErrorEnvelope.from_dict(response.json())

        return response_504

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    request_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Get a fraud verification

     Reads an analysis back by the `requestId` the verification returned. It also reads
    the analysis of a document a workflow or an extraction checked, when fraud
    detection is enabled for them. Requires the `fraud-verify.read` scope.

    Args:
        request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    request_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Get a fraud verification

     Reads an analysis back by the `requestId` the verification returned. It also reads
    the analysis of a document a workflow or an extraction checked, when fraud
    detection is enabled for them. Requires the `fraud-verify.read` scope.

    Args:
        request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]
    """

    return sync_detailed(
        request_id=request_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    request_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Get a fraud verification

     Reads an analysis back by the `requestId` the verification returned. It also reads
    the analysis of a document a workflow or an extraction checked, when fraud
    detection is enabled for them. Requires the `fraud-verify.read` scope.

    Args:
        request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    request_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Get a fraud verification

     Reads an analysis back by the `requestId` the verification returned. It also reads
    the analysis of a document a workflow or an extraction checked, when fraud
    detection is enabled for them. Requires the `fraud-verify.read` scope.

    Args:
        request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]
    """

    return (
        await asyncio_detailed(
            request_id=request_id,
            client=client,
        )
    ).parsed
