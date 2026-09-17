import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.envelope_data_metadata import EnvelopeDataMetadata


T = TypeVar("T", bound="EnvelopeData")


@_attrs_define
class EnvelopeData:
    """
    Attributes:
        id (Union[Unset, UUID]):
        metadata (Union[Unset, EnvelopeDataMetadata]): Operation-specific payload.
        created_date (Union[Unset, datetime.datetime]):
    """

    id: Union[Unset, UUID] = UNSET
    metadata: Union[Unset, "EnvelopeDataMetadata"] = UNSET
    created_date: Union[Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        created_date: Union[Unset, str] = UNSET
        if not isinstance(self.created_date, Unset):
            created_date = self.created_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if created_date is not UNSET:
            field_dict["createdDate"] = created_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.envelope_data_metadata import EnvelopeDataMetadata

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _metadata = d.pop("metadata", UNSET)
        metadata: Union[Unset, EnvelopeDataMetadata]
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = EnvelopeDataMetadata.from_dict(_metadata)

        _created_date = d.pop("createdDate", UNSET)
        created_date: Union[Unset, datetime.datetime]
        if isinstance(_created_date, Unset):
            created_date = UNSET
        else:
            created_date = isoparse(_created_date)

        envelope_data = cls(
            id=id,
            metadata=metadata,
            created_date=created_date,
        )

        envelope_data.additional_properties = d
        return envelope_data

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
