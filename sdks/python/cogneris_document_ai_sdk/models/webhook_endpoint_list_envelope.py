from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.service_response_meta import ServiceResponseMeta
    from ..models.webhook_endpoint_list import WebhookEndpointList


T = TypeVar("T", bound="WebhookEndpointListEnvelope")


@_attrs_define
class WebhookEndpointListEnvelope:
    """
    Attributes:
        data (WebhookEndpointList):
        meta (ServiceResponseMeta):
        has_errors (bool):
    """

    data: "WebhookEndpointList"
    meta: "ServiceResponseMeta"
    has_errors: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        meta = self.meta.to_dict()

        has_errors = self.has_errors

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "meta": meta,
                "hasErrors": has_errors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_response_meta import ServiceResponseMeta
        from ..models.webhook_endpoint_list import WebhookEndpointList

        d = dict(src_dict)
        data = WebhookEndpointList.from_dict(d.pop("data"))

        meta = ServiceResponseMeta.from_dict(d.pop("meta"))

        has_errors = d.pop("hasErrors")

        webhook_endpoint_list_envelope = cls(
            data=data,
            meta=meta,
            has_errors=has_errors,
        )

        webhook_endpoint_list_envelope.additional_properties = d
        return webhook_endpoint_list_envelope

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
