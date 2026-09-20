import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.portal_magic_link_opt_in_source import PortalMagicLinkOptInSource
from ..types import UNSET, Unset

T = TypeVar("T", bound="PortalMagicLinkOptIn")


@_attrs_define
class PortalMagicLinkOptIn:
    """A declaration that the recipient agreed to be messaged on WhatsApp.

    Attributes:
        source (PortalMagicLinkOptInSource): How the recipient's consent was collected.
        evidence_text (str): Required, non-blank pointer to the proof of consent, such as a contract number, form id or
            ticket.
        evidence_url (Union[None, Unset, str]): Optional link to the evidence.
        collected_when (Union[None, Unset, datetime.datetime]): When the recipient consented. Defaults to now; supply
            the original date for older consent. Dates more than one day in the future are rejected.
    """

    source: PortalMagicLinkOptInSource
    evidence_text: str
    evidence_url: Union[None, Unset, str] = UNSET
    collected_when: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source = self.source.value

        evidence_text = self.evidence_text

        evidence_url: Union[None, Unset, str]
        if isinstance(self.evidence_url, Unset):
            evidence_url = UNSET
        else:
            evidence_url = self.evidence_url

        collected_when: Union[None, Unset, str]
        if isinstance(self.collected_when, Unset):
            collected_when = UNSET
        elif isinstance(self.collected_when, datetime.datetime):
            collected_when = self.collected_when.isoformat()
        else:
            collected_when = self.collected_when

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source": source,
                "evidenceText": evidence_text,
            }
        )
        if evidence_url is not UNSET:
            field_dict["evidenceUrl"] = evidence_url
        if collected_when is not UNSET:
            field_dict["collectedWhen"] = collected_when

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source = PortalMagicLinkOptInSource(d.pop("source"))

        evidence_text = d.pop("evidenceText")

        def _parse_evidence_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        evidence_url = _parse_evidence_url(d.pop("evidenceUrl", UNSET))

        def _parse_collected_when(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                collected_when_type_0 = isoparse(data)

                return collected_when_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        collected_when = _parse_collected_when(d.pop("collectedWhen", UNSET))

        portal_magic_link_opt_in = cls(
            source=source,
            evidence_text=evidence_text,
            evidence_url=evidence_url,
            collected_when=collected_when,
        )

        portal_magic_link_opt_in.additional_properties = d
        return portal_magic_link_opt_in

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
