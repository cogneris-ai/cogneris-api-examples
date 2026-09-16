from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.portal_send_channel import PortalSendChannel
from ..types import UNSET, Unset

T = TypeVar("T", bound="PortalMagicLink")


@_attrs_define
class PortalMagicLink:
    """
    Attributes:
        id (Union[Unset, int]): The created magic link.
        url (Union[None, Unset, str]): The link the recipient opens. Present only on the first create — the token
            is a one-time secret that is never stored in readable form, so an
            idempotent replay omits this field.
        sent (Union[Unset, bool]): Whether Cogneris dispatched the link. False when `sendChannel` was omitted or the
            send was suppressed.
        send_channel (Union[None, PortalSendChannel, Unset]): The channel actually used, when one was.
    """

    id: Union[Unset, int] = UNSET
    url: Union[None, Unset, str] = UNSET
    sent: Union[Unset, bool] = UNSET
    send_channel: Union[None, PortalSendChannel, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        url: Union[None, Unset, str]
        if isinstance(self.url, Unset):
            url = UNSET
        else:
            url = self.url

        sent = self.sent

        send_channel: Union[None, Unset, str]
        if isinstance(self.send_channel, Unset):
            send_channel = UNSET
        elif isinstance(self.send_channel, PortalSendChannel):
            send_channel = self.send_channel.value
        else:
            send_channel = self.send_channel

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if url is not UNSET:
            field_dict["url"] = url
        if sent is not UNSET:
            field_dict["sent"] = sent
        if send_channel is not UNSET:
            field_dict["sendChannel"] = send_channel

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        url = _parse_url(d.pop("url", UNSET))

        sent = d.pop("sent", UNSET)

        def _parse_send_channel(data: object) -> Union[None, PortalSendChannel, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                send_channel_type_0 = PortalSendChannel(data)

                return send_channel_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, PortalSendChannel, Unset], data)

        send_channel = _parse_send_channel(d.pop("sendChannel", UNSET))

        portal_magic_link = cls(
            id=id,
            url=url,
            sent=sent,
            send_channel=send_channel,
        )

        portal_magic_link.additional_properties = d
        return portal_magic_link

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
