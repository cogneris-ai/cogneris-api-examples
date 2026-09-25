from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.webhook_endpoint import WebhookEndpoint


T = TypeVar("T", bound="WebhookEndpointCreated")


@_attrs_define
class WebhookEndpointCreated:
    """
    Attributes:
        endpoint (WebhookEndpoint):
        secret (str): The signing secret. Shown once — store it now. Example:
            whsec_3f9a0c1e5b7d2468ace013579bdf2468ace013579bdf2468ace013579bdf2468.
    """

    endpoint: "WebhookEndpoint"
    secret: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        endpoint = self.endpoint.to_dict()

        secret = self.secret

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "endpoint": endpoint,
                "secret": secret,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_endpoint import WebhookEndpoint

        d = dict(src_dict)
        endpoint = WebhookEndpoint.from_dict(d.pop("endpoint"))

        secret = d.pop("secret")

        webhook_endpoint_created = cls(
            endpoint=endpoint,
            secret=secret,
        )

        webhook_endpoint_created.additional_properties = d
        return webhook_endpoint_created

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
