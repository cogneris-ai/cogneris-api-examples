import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="Artifact")


@_attrs_define
class Artifact:
    """
    Attributes:
        reference (str): Pass this as a job's `inputReference`. Reusable until it expires — treat
            it as opaque rather than parsing it.
             Example: artifact://uploads/9f2c1b7a4d8e4f06b1a25c3e7d9f0a11/invoice.pdf.
        file_name (str): The stored name. Characters outside `A-Z a-z 0-9 . _ -` are replaced and
            long names are truncated, so this can differ from what you sent. The
            extension is always preserved.
             Example: invoice.pdf.
        content_type (str): The type the bytes were stored under. A non-image document is normalized
            to `application/pdf` before storage, so this can differ from what you
            uploaded.
             Example: application/pdf.
        size_bytes (int): Size of the stored document, which is not the size you sent when it was normalized. Example:
            248713.
        expires_at (datetime.datetime): When the reference stops resolving — 7 days from upload. Reads after this
            answer `410`.
             Example: 2026-09-29T14:03:11.482Z.
    """

    reference: str
    file_name: str
    content_type: str
    size_bytes: int
    expires_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reference = self.reference

        file_name = self.file_name

        content_type = self.content_type

        size_bytes = self.size_bytes

        expires_at = self.expires_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reference": reference,
                "fileName": file_name,
                "contentType": content_type,
                "sizeBytes": size_bytes,
                "expiresAt": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference = d.pop("reference")

        file_name = d.pop("fileName")

        content_type = d.pop("contentType")

        size_bytes = d.pop("sizeBytes")

        expires_at = isoparse(d.pop("expiresAt"))

        artifact = cls(
            reference=reference,
            file_name=file_name,
            content_type=content_type,
            size_bytes=size_bytes,
            expires_at=expires_at,
        )

        artifact.additional_properties = d
        return artifact

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
