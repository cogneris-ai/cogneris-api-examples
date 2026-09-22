from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EnvelopeDataMetadata")


@_attrs_define
class EnvelopeDataMetadata:
    """Operation-specific payload, shaped by the template or operation that ran.
    The keys are your template's, so the object itself is left open here.

    Extraction and zero-shot fill it with one entry per extracted field, and
    each entry is an `ExtractedField`: the value, how certain the model is of
    it, and — when the value was visually located on the page — where it was
    read from. A table-shaped field carries an `items` array instead, whose
    rows hold `ExtractedField` cells under the same keys.

    Source coordinates follow one convention, the same on every engine:

    - `page` is 1-indexed, and never past the document's last page.
    - `bbox` is `[x0, y0, x1, y1]` as fractions of the page size with the
      origin at the top-left, so `x0,y0` is the top-left corner and `x1,y1`
      the bottom-right. Values are clamped into `0`–`1` and the corners are
      ordered, so `x0 <= x1` and `y0 <= y1` always hold.
    - `page`, `bbox` and `bbox_confidence` are omitted **together** for any
      value the model could not locate on the page — a computed total, for
      instance. Their absence is not an error, and a field object carrying
      none of the three is ordinary.

    Every confidence this API returns is a number from `0` to `100`,
    `bbox_confidence` included. There is no second scale to convert from.

    A document job's stored `result.json` holds the same field entries,
    sanitized the same way, so the asynchronous answer agrees with the
    synchronous one for the same document. It wraps them differently — see
    `outputReference`.

        Example:
            {'policyNumber': {'value': '254H089SJ425', 'confidence': 98, 'page': 1, 'bbox': [0.62, 0.11, 0.83, 0.14],
                'bbox_confidence': 92}, 'totalPremium': {'value': '1840.00', 'confidence': 95}}

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        envelope_data_metadata = cls()

        envelope_data_metadata.additional_properties = d
        return envelope_data_metadata

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
