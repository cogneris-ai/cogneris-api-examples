from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.portal_send_channel import PortalSendChannel
from ..types import UNSET, Unset

T = TypeVar("T", bound="PortalChannels")


@_attrs_define
class PortalChannels:
    """
    Attributes:
        channels (Union[Unset, list[PortalSendChannel]]):
    """

    channels: Union[Unset, list[PortalSendChannel]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        channels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.channels, Unset):
            channels = []
            for channels_item_data in self.channels:
                channels_item = channels_item_data.value
                channels.append(channels_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if channels is not UNSET:
            field_dict["channels"] = channels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        channels = []
        _channels = d.pop("channels", UNSET)
        for channels_item_data in _channels or []:
            channels_item = PortalSendChannel(channels_item_data)

            channels.append(channels_item)

        portal_channels = cls(
            channels=channels,
        )

        portal_channels.additional_properties = d
        return portal_channels

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
