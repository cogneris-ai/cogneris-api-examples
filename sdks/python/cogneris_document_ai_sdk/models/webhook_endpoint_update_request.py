from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_event import WebhookEvent
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_endpoint_update_request_headers_type_0 import WebhookEndpointUpdateRequestHeadersType0


T = TypeVar("T", bound="WebhookEndpointUpdateRequest")


@_attrs_define
class WebhookEndpointUpdateRequest:
    """
    Attributes:
        name (str):
        url (str): Changing it rotates the signing secret.
        events (list[WebhookEvent]):
        id (Union[Unset, UUID]): Ignored. The endpoint is the one named in the path.
        headers (Union['WebhookEndpointUpdateRequestHeadersType0', None, Unset]):
        body (Union[None, Unset, str]):
        is_active (Union[Unset, bool]): An inactive endpoint is kept but receives nothing. Default: True.
    """

    name: str
    url: str
    events: list[WebhookEvent]
    id: Union[Unset, UUID] = UNSET
    headers: Union["WebhookEndpointUpdateRequestHeadersType0", None, Unset] = UNSET
    body: Union[None, Unset, str] = UNSET
    is_active: Union[Unset, bool] = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_endpoint_update_request_headers_type_0 import WebhookEndpointUpdateRequestHeadersType0

        name = self.name

        url = self.url

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.value
            events.append(events_item)

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        headers: Union[None, Unset, dict[str, Any]]
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookEndpointUpdateRequestHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        body: Union[None, Unset, str]
        if isinstance(self.body, Unset):
            body = UNSET
        else:
            body = self.body

        is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "url": url,
                "events": events,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if headers is not UNSET:
            field_dict["headers"] = headers
        if body is not UNSET:
            field_dict["body"] = body
        if is_active is not UNSET:
            field_dict["isActive"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_endpoint_update_request_headers_type_0 import WebhookEndpointUpdateRequestHeadersType0

        d = dict(src_dict)
        name = d.pop("name")

        url = d.pop("url")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = WebhookEvent(events_item_data)

            events.append(events_item)

        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_headers(data: object) -> Union["WebhookEndpointUpdateRequestHeadersType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookEndpointUpdateRequestHeadersType0.from_dict(data)

                return headers_type_0
            except:  # noqa: E722
                pass
            return cast(Union["WebhookEndpointUpdateRequestHeadersType0", None, Unset], data)

        headers = _parse_headers(d.pop("headers", UNSET))

        def _parse_body(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        body = _parse_body(d.pop("body", UNSET))

        is_active = d.pop("isActive", UNSET)

        webhook_endpoint_update_request = cls(
            name=name,
            url=url,
            events=events,
            id=id,
            headers=headers,
            body=body,
            is_active=is_active,
        )

        webhook_endpoint_update_request.additional_properties = d
        return webhook_endpoint_update_request

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
