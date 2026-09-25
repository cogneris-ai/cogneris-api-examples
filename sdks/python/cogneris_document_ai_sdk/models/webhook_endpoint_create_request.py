from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_event import WebhookEvent
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_endpoint_create_request_headers_type_0 import WebhookEndpointCreateRequestHeadersType0


T = TypeVar("T", bound="WebhookEndpointCreateRequest")


@_attrs_define
class WebhookEndpointCreateRequest:
    """
    Attributes:
        name (str):
        url (str): Absolute HTTPS on a public address. Private, loopback and link-local targets are refused. Example:
            https://hooks.example.com/cogneris.
        events (list[WebhookEvent]):
        headers (Union['WebhookEndpointCreateRequestHeadersType0', None, Unset]): Sent on every delivery, for example
            your receiver's own credential. Stored encrypted.
        body (Union[None, Unset, str]): Sent **instead of** the event payload when set. Leave it unset to receive
            the job fields.
    """

    name: str
    url: str
    events: list[WebhookEvent]
    headers: Union["WebhookEndpointCreateRequestHeadersType0", None, Unset] = UNSET
    body: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_endpoint_create_request_headers_type_0 import WebhookEndpointCreateRequestHeadersType0

        name = self.name

        url = self.url

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.value
            events.append(events_item)

        headers: Union[None, Unset, dict[str, Any]]
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookEndpointCreateRequestHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        body: Union[None, Unset, str]
        if isinstance(self.body, Unset):
            body = UNSET
        else:
            body = self.body

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "url": url,
                "events": events,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if body is not UNSET:
            field_dict["body"] = body

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_endpoint_create_request_headers_type_0 import WebhookEndpointCreateRequestHeadersType0

        d = dict(src_dict)
        name = d.pop("name")

        url = d.pop("url")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = WebhookEvent(events_item_data)

            events.append(events_item)

        def _parse_headers(data: object) -> Union["WebhookEndpointCreateRequestHeadersType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookEndpointCreateRequestHeadersType0.from_dict(data)

                return headers_type_0
            except:  # noqa: E722
                pass
            return cast(Union["WebhookEndpointCreateRequestHeadersType0", None, Unset], data)

        headers = _parse_headers(d.pop("headers", UNSET))

        def _parse_body(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        body = _parse_body(d.pop("body", UNSET))

        webhook_endpoint_create_request = cls(
            name=name,
            url=url,
            events=events,
            headers=headers,
            body=body,
        )

        webhook_endpoint_create_request.additional_properties = d
        return webhook_endpoint_create_request

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
