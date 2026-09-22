from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.artifact_upload_envelope import ArtifactUploadEnvelope
from ...models.service_error_envelope import ServiceErrorEnvelope
from ...models.upload_artifact_body import UploadArtifactBody
from ...types import Response


def _get_kwargs(
    *,
    body: UploadArtifactBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/artifacts",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    if response.status_code == 201:
        response_201 = ArtifactUploadEnvelope.from_dict(response.json())

        return response_201

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 413:
        response_413 = cast(Any, None)
        return response_413

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if response.status_code == 422:
        response_422 = ServiceErrorEnvelope.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if response.status_code == 503:
        response_503 = ServiceErrorEnvelope.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadArtifactBody,
) -> Response[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    """Upload the input document of an asynchronous job

     Stores a document and returns the `artifact://` reference to submit it with.
    This is the only way to obtain one — the asynchronous job endpoints take a
    reference, never a file.

    The document is scanned and normalized before it is stored, exactly as the
    synchronous `/Document/*` endpoints do. Images are stored as uploaded, so
    `Crop` and `Facematch` still see the original pixels; everything else is
    stored in its canonical form, which is what the job will read.

    The reference is reusable and expires after 7 days — see **Artifact
    references** above.

    Args:
        body (UploadArtifactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]
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
    body: UploadArtifactBody,
) -> Optional[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    """Upload the input document of an asynchronous job

     Stores a document and returns the `artifact://` reference to submit it with.
    This is the only way to obtain one — the asynchronous job endpoints take a
    reference, never a file.

    The document is scanned and normalized before it is stored, exactly as the
    synchronous `/Document/*` endpoints do. Images are stored as uploaded, so
    `Crop` and `Facematch` still see the original pixels; everything else is
    stored in its canonical form, which is what the job will read.

    The reference is reusable and expires after 7 days — see **Artifact
    references** above.

    Args:
        body (UploadArtifactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadArtifactBody,
) -> Response[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    """Upload the input document of an asynchronous job

     Stores a document and returns the `artifact://` reference to submit it with.
    This is the only way to obtain one — the asynchronous job endpoints take a
    reference, never a file.

    The document is scanned and normalized before it is stored, exactly as the
    synchronous `/Document/*` endpoints do. Images are stored as uploaded, so
    `Crop` and `Facematch` still see the original pixels; everything else is
    stored in its canonical form, which is what the job will read.

    The reference is reusable and expires after 7 days — see **Artifact
    references** above.

    Args:
        body (UploadArtifactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadArtifactBody,
) -> Optional[Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]]:
    """Upload the input document of an asynchronous job

     Stores a document and returns the `artifact://` reference to submit it with.
    This is the only way to obtain one — the asynchronous job endpoints take a
    reference, never a file.

    The document is scanned and normalized before it is stored, exactly as the
    synchronous `/Document/*` endpoints do. Images are stored as uploaded, so
    `Crop` and `Facematch` still see the original pixels; everything else is
    stored in its canonical form, which is what the job will read.

    The reference is reusable and expires after 7 days — see **Artifact
    references** above.

    Args:
        body (UploadArtifactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ArtifactUploadEnvelope, ServiceErrorEnvelope]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
