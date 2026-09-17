from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.document_job import DocumentJob


T = TypeVar("T", bound="ListDocumentJobsResponse200")


@_attrs_define
class ListDocumentJobsResponse200:
    """
    Attributes:
        jobs (Union[Unset, list['DocumentJob']]):
    """

    jobs: Union[Unset, list["DocumentJob"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobs is not UNSET:
            field_dict["jobs"] = jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.document_job import DocumentJob

        d = dict(src_dict)
        jobs = []
        _jobs = d.pop("jobs", UNSET)
        for jobs_item_data in _jobs or []:
            jobs_item = DocumentJob.from_dict(jobs_item_data)

            jobs.append(jobs_item)

        list_document_jobs_response_200 = cls(
            jobs=jobs,
        )

        list_document_jobs_response_200.additional_properties = d
        return list_document_jobs_response_200

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
