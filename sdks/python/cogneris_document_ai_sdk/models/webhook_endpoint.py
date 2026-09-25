import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.webhook_endpoint_environment import WebhookEndpointEnvironment
from ..models.webhook_event import WebhookEvent
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_endpoint_headers_type_0 import WebhookEndpointHeadersType0


T = TypeVar("T", bound="WebhookEndpoint")


@_attrs_define
class WebhookEndpoint:
    """
    Attributes:
        id (UUID):
        name (str):
        url (str):
        events (list[WebhookEvent]):
        is_active (bool):
        created_when (datetime.datetime):
        headers (Union['WebhookEndpointHeadersType0', None, Unset]):
        body (Union[None, Unset, str]):
        environment (Union[Unset, WebhookEndpointEnvironment]): Which environment's events this endpoint receives. Read-
            only: it is taken
            from the API key that registered the endpoint, never from the request body,
            so a sandbox key's endpoint can never be sent production events and a
            production key's endpoint can never be sent sandbox ones.
        changed_when (Union[None, Unset, datetime.datetime]):
        secret (Union[None, Unset, str]): The new signing secret, only on the update response that rotated it
            because `url` changed. Null everywhere else.
             Example: whsec_3f9a0c1e5b7d2468ace013579bdf2468ace013579bdf2468ace013579bdf2468.
    """

    id: UUID
    name: str
    url: str
    events: list[WebhookEvent]
    is_active: bool
    created_when: datetime.datetime
    headers: Union["WebhookEndpointHeadersType0", None, Unset] = UNSET
    body: Union[None, Unset, str] = UNSET
    environment: Union[Unset, WebhookEndpointEnvironment] = UNSET
    changed_when: Union[None, Unset, datetime.datetime] = UNSET
    secret: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_endpoint_headers_type_0 import WebhookEndpointHeadersType0

        id = str(self.id)

        name = self.name

        url = self.url

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.value
            events.append(events_item)

        is_active = self.is_active

        created_when = self.created_when.isoformat()

        headers: Union[None, Unset, dict[str, Any]]
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookEndpointHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        body: Union[None, Unset, str]
        if isinstance(self.body, Unset):
            body = UNSET
        else:
            body = self.body

        environment: Union[Unset, str] = UNSET
        if not isinstance(self.environment, Unset):
            environment = self.environment.value

        changed_when: Union[None, Unset, str]
        if isinstance(self.changed_when, Unset):
            changed_when = UNSET
        elif isinstance(self.changed_when, datetime.datetime):
            changed_when = self.changed_when.isoformat()
        else:
            changed_when = self.changed_when

        secret: Union[None, Unset, str]
        if isinstance(self.secret, Unset):
            secret = UNSET
        else:
            secret = self.secret

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "url": url,
                "events": events,
                "isActive": is_active,
                "createdWhen": created_when,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if body is not UNSET:
            field_dict["body"] = body
        if environment is not UNSET:
            field_dict["environment"] = environment
        if changed_when is not UNSET:
            field_dict["changedWhen"] = changed_when
        if secret is not UNSET:
            field_dict["secret"] = secret

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_endpoint_headers_type_0 import WebhookEndpointHeadersType0

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        url = d.pop("url")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = WebhookEvent(events_item_data)

            events.append(events_item)

        is_active = d.pop("isActive")

        created_when = isoparse(d.pop("createdWhen"))

        def _parse_headers(data: object) -> Union["WebhookEndpointHeadersType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookEndpointHeadersType0.from_dict(data)

                return headers_type_0
            except:  # noqa: E722
                pass
            return cast(Union["WebhookEndpointHeadersType0", None, Unset], data)

        headers = _parse_headers(d.pop("headers", UNSET))

        def _parse_body(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        body = _parse_body(d.pop("body", UNSET))

        _environment = d.pop("environment", UNSET)
        environment: Union[Unset, WebhookEndpointEnvironment]
        if isinstance(_environment, Unset):
            environment = UNSET
        else:
            environment = WebhookEndpointEnvironment(_environment)

        def _parse_changed_when(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                changed_when_type_0 = isoparse(data)

                return changed_when_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        changed_when = _parse_changed_when(d.pop("changedWhen", UNSET))

        def _parse_secret(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        secret = _parse_secret(d.pop("secret", UNSET))

        webhook_endpoint = cls(
            id=id,
            name=name,
            url=url,
            events=events,
            is_active=is_active,
            created_when=created_when,
            headers=headers,
            body=body,
            environment=environment,
            changed_when=changed_when,
            secret=secret,
        )

        webhook_endpoint.additional_properties = d
        return webhook_endpoint

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
