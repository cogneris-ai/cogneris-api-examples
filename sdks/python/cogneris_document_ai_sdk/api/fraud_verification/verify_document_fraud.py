from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.fraud_verification_envelope import FraudVerificationEnvelope
from ...models.problem_details import ProblemDetails
from ...models.service_error_envelope import ServiceErrorEnvelope
from ...models.verify_document_fraud_body import VerifyDocumentFraudBody
from ...types import Response


def _get_kwargs(
    *,
    body: VerifyDocumentFraudBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/fraud-verify",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
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
        response_404 = ProblemDetails.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ProblemDetails.from_dict(response.json())

        return response_409

    if response.status_code == 413:
        response_413 = cast(Any, None)
        return response_413

    if response.status_code == 415:
        response_415 = ServiceErrorEnvelope.from_dict(response.json())

        return response_415

    if response.status_code == 422:
        response_422 = ServiceErrorEnvelope.from_dict(response.json())

        return response_422

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
) -> Response[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: VerifyDocumentFraudBody,
) -> Response[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Verify a document for fraud

     Checks one document — a PDF or an image — for signs that it was edited after it
    was issued, fabricated, or submitted before, and returns a verdict:

    - `trusted` — nothing worth a second look;
    - `review` — a person should look before relying on it;
    - `suspect` — strong signs; a person must look.

    A verdict never rejects a document by itself. It tells you whether to route the
    document to a person.

    **What is checked.** PDF edit history and metadata, compression inconsistencies
    between image regions, content credentials (C2PA), digital signatures, and whether
    the same file or the same layout was submitted to your tenant before. When you
    send `fields` — values already extracted from this document — tax ids, dates and
    totals are checked as well. `checks` lists every check that ran and what it
    answered; `failedCoverage` lists the ones that could not run. A check that did not
    run is not a clear result.

    **The file is analysed as you sent it.** Send the original file, not a re-saved or
    printed copy: re-saving erases the edit history several checks read.

    **Opt-in.** Fraud verification runs only for a tenant whose administrator enabled
    fraud detection. Otherwise the call is refused with `fraud.not_enabled` and nothing
    is charged.

    **Credits.** 8 credits per analysis, reported in `meta.creditsConsumed`. With
    `reuse` (the default), sending the same file again at the same sensitivity within
    24 hours returns the earlier analysis with `reused: true`, free of charge. An
    analysis that could not complete (`fraud.unavailable`) is not charged.

    Production keys only. Requires the `fraud-verify.write` scope (a `*` key holds it).

    Args:
        body (VerifyDocumentFraudBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]
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
    body: VerifyDocumentFraudBody,
) -> Optional[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Verify a document for fraud

     Checks one document — a PDF or an image — for signs that it was edited after it
    was issued, fabricated, or submitted before, and returns a verdict:

    - `trusted` — nothing worth a second look;
    - `review` — a person should look before relying on it;
    - `suspect` — strong signs; a person must look.

    A verdict never rejects a document by itself. It tells you whether to route the
    document to a person.

    **What is checked.** PDF edit history and metadata, compression inconsistencies
    between image regions, content credentials (C2PA), digital signatures, and whether
    the same file or the same layout was submitted to your tenant before. When you
    send `fields` — values already extracted from this document — tax ids, dates and
    totals are checked as well. `checks` lists every check that ran and what it
    answered; `failedCoverage` lists the ones that could not run. A check that did not
    run is not a clear result.

    **The file is analysed as you sent it.** Send the original file, not a re-saved or
    printed copy: re-saving erases the edit history several checks read.

    **Opt-in.** Fraud verification runs only for a tenant whose administrator enabled
    fraud detection. Otherwise the call is refused with `fraud.not_enabled` and nothing
    is charged.

    **Credits.** 8 credits per analysis, reported in `meta.creditsConsumed`. With
    `reuse` (the default), sending the same file again at the same sensitivity within
    24 hours returns the earlier analysis with `reused: true`, free of charge. An
    analysis that could not complete (`fraud.unavailable`) is not charged.

    Production keys only. Requires the `fraud-verify.write` scope (a `*` key holds it).

    Args:
        body (VerifyDocumentFraudBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: VerifyDocumentFraudBody,
) -> Response[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Verify a document for fraud

     Checks one document — a PDF or an image — for signs that it was edited after it
    was issued, fabricated, or submitted before, and returns a verdict:

    - `trusted` — nothing worth a second look;
    - `review` — a person should look before relying on it;
    - `suspect` — strong signs; a person must look.

    A verdict never rejects a document by itself. It tells you whether to route the
    document to a person.

    **What is checked.** PDF edit history and metadata, compression inconsistencies
    between image regions, content credentials (C2PA), digital signatures, and whether
    the same file or the same layout was submitted to your tenant before. When you
    send `fields` — values already extracted from this document — tax ids, dates and
    totals are checked as well. `checks` lists every check that ran and what it
    answered; `failedCoverage` lists the ones that could not run. A check that did not
    run is not a clear result.

    **The file is analysed as you sent it.** Send the original file, not a re-saved or
    printed copy: re-saving erases the edit history several checks read.

    **Opt-in.** Fraud verification runs only for a tenant whose administrator enabled
    fraud detection. Otherwise the call is refused with `fraud.not_enabled` and nothing
    is charged.

    **Credits.** 8 credits per analysis, reported in `meta.creditsConsumed`. With
    `reuse` (the default), sending the same file again at the same sensitivity within
    24 hours returns the earlier analysis with `reused: true`, free of charge. An
    analysis that could not complete (`fraud.unavailable`) is not charged.

    Production keys only. Requires the `fraud-verify.write` scope (a `*` key holds it).

    Args:
        body (VerifyDocumentFraudBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: VerifyDocumentFraudBody,
) -> Optional[Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]]:
    """Verify a document for fraud

     Checks one document — a PDF or an image — for signs that it was edited after it
    was issued, fabricated, or submitted before, and returns a verdict:

    - `trusted` — nothing worth a second look;
    - `review` — a person should look before relying on it;
    - `suspect` — strong signs; a person must look.

    A verdict never rejects a document by itself. It tells you whether to route the
    document to a person.

    **What is checked.** PDF edit history and metadata, compression inconsistencies
    between image regions, content credentials (C2PA), digital signatures, and whether
    the same file or the same layout was submitted to your tenant before. When you
    send `fields` — values already extracted from this document — tax ids, dates and
    totals are checked as well. `checks` lists every check that ran and what it
    answered; `failedCoverage` lists the ones that could not run. A check that did not
    run is not a clear result.

    **The file is analysed as you sent it.** Send the original file, not a re-saved or
    printed copy: re-saving erases the edit history several checks read.

    **Opt-in.** Fraud verification runs only for a tenant whose administrator enabled
    fraud detection. Otherwise the call is refused with `fraud.not_enabled` and nothing
    is charged.

    **Credits.** 8 credits per analysis, reported in `meta.creditsConsumed`. With
    `reuse` (the default), sending the same file again at the same sensitivity within
    24 hours returns the earlier analysis with `reused: true`, free of charge. An
    analysis that could not complete (`fraud.unavailable`) is not charged.

    Production keys only. Requires the `fraud-verify.write` scope (a `*` key holds it).

    Args:
        body (VerifyDocumentFraudBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, FraudVerificationEnvelope, ProblemDetails, ServiceErrorEnvelope]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
