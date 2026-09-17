from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.portal_send_channel import PortalSendChannel
from ..types import UNSET, Unset

T = TypeVar("T", bound="PortalMagicLinkRequest")


@_attrs_define
class PortalMagicLinkRequest:
    """
    Attributes:
        form_id (int): Target form, from `GET /api/v1/portal/forms`. Must be greater than zero.
        name (str): Recipient display name.
        send_channel (Union[None, PortalSendChannel, Unset]): Channel to deliver the link on. Omit it to create the link
            without
            sending anything.
        email (Union[None, Unset, str]): Required when `sendChannel` is `email`.
        phone (Union[None, Unset, str]): Required when `sendChannel` is `sms` or `whatsapp`.
        tax_id (Union[None, Unset, str]): Recipient tax id.
        due_days (Union[Unset, int]): Days until the link expires. A value of zero or less is treated as 30. Default:
            30.
        max_accesses (Union[None, Unset, int]): How many times the link may be opened. Null means unlimited; 1 makes it
            single-use.
        notes (Union[None, Unset, str]): Internal note kept against the link, never shown to the recipient.
    """

    form_id: int
    name: str
    send_channel: Union[None, PortalSendChannel, Unset] = UNSET
    email: Union[None, Unset, str] = UNSET
    phone: Union[None, Unset, str] = UNSET
    tax_id: Union[None, Unset, str] = UNSET
    due_days: Union[Unset, int] = 30
    max_accesses: Union[None, Unset, int] = UNSET
    notes: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        form_id = self.form_id

        name = self.name

        send_channel: Union[None, Unset, str]
        if isinstance(self.send_channel, Unset):
            send_channel = UNSET
        elif isinstance(self.send_channel, PortalSendChannel):
            send_channel = self.send_channel.value
        else:
            send_channel = self.send_channel

        email: Union[None, Unset, str]
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        phone: Union[None, Unset, str]
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        tax_id: Union[None, Unset, str]
        if isinstance(self.tax_id, Unset):
            tax_id = UNSET
        else:
            tax_id = self.tax_id

        due_days = self.due_days

        max_accesses: Union[None, Unset, int]
        if isinstance(self.max_accesses, Unset):
            max_accesses = UNSET
        else:
            max_accesses = self.max_accesses

        notes: Union[None, Unset, str]
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "formId": form_id,
                "name": name,
            }
        )
        if send_channel is not UNSET:
            field_dict["sendChannel"] = send_channel
        if email is not UNSET:
            field_dict["email"] = email
        if phone is not UNSET:
            field_dict["phone"] = phone
        if tax_id is not UNSET:
            field_dict["taxId"] = tax_id
        if due_days is not UNSET:
            field_dict["dueDays"] = due_days
        if max_accesses is not UNSET:
            field_dict["maxAccesses"] = max_accesses
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        form_id = d.pop("formId")

        name = d.pop("name")

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

        def _parse_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_phone(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_tax_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tax_id = _parse_tax_id(d.pop("taxId", UNSET))

        due_days = d.pop("dueDays", UNSET)

        def _parse_max_accesses(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_accesses = _parse_max_accesses(d.pop("maxAccesses", UNSET))

        def _parse_notes(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        notes = _parse_notes(d.pop("notes", UNSET))

        portal_magic_link_request = cls(
            form_id=form_id,
            name=name,
            send_channel=send_channel,
            email=email,
            phone=phone,
            tax_id=tax_id,
            due_days=due_days,
            max_accesses=max_accesses,
            notes=notes,
        )

        portal_magic_link_request.additional_properties = d
        return portal_magic_link_request

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
