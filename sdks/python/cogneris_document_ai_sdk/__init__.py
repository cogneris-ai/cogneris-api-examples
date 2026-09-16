"""A client library for accessing Cogneris Document AI API"""

from .client import AuthenticatedClient, Client

__all__ = (
    "AuthenticatedClient",
    "Client",
)
from .cogneris import (
    COGNERIS_REGION_URLS,
    CognerisApiError,
    CognerisClient,
    CognerisError,
    CognerisJobTerminalError,
    CognerisMaxAttemptsError,
    CognerisResponseError,
    CognerisTransportError,
    cogneris_base_url,
)

__all__ += (
    "COGNERIS_REGION_URLS",
    "CognerisApiError",
    "CognerisClient",
    "CognerisError",
    "CognerisJobTerminalError",
    "CognerisMaxAttemptsError",
    "CognerisResponseError",
    "CognerisTransportError",
    "cogneris_base_url",
)
