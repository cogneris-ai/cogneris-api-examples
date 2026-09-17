from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.service_error_envelope_data_type_0 import ServiceErrorEnvelopeDataType0
    from ..models.service_response_meta import ServiceResponseMeta


T = TypeVar("T", bound="ServiceErrorEnvelope")


@_attrs_define
class ServiceErrorEnvelope:
    """
    Attributes:
        data (Union['ServiceErrorEnvelopeDataType0', None]):
        meta (ServiceResponseMeta):
        has_errors (bool):
    """

    data: Union["ServiceErrorEnvelopeDataType0", None]
    meta: "ServiceResponseMeta"
    has_errors: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.service_error_envelope_data_type_0 import ServiceErrorEnvelopeDataType0

        data: Union[None, dict[str, Any]]
        if isinstance(self.data, ServiceErrorEnvelopeDataType0):
            data = self.data.to_dict()
        else:
            data = self.data

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
        from ..models.service_error_envelope_data_type_0 import ServiceErrorEnvelopeDataType0
        from ..models.service_response_meta import ServiceResponseMeta

        d = dict(src_dict)

        def _parse_data(data: object) -> Union["ServiceErrorEnvelopeDataType0", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = ServiceErrorEnvelopeDataType0.from_dict(data)

                return data_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ServiceErrorEnvelopeDataType0", None], data)

        data = _parse_data(d.pop("data"))

        meta = ServiceResponseMeta.from_dict(d.pop("meta"))

        has_errors = d.pop("hasErrors")

        service_error_envelope = cls(
            data=data,
            meta=meta,
            has_errors=has_errors,
        )

        service_error_envelope.additional_properties = d
        return service_error_envelope

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
