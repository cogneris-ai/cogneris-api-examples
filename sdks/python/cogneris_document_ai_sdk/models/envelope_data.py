import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.classification_result import ClassificationResult
    from ..models.crop_document import CropDocument
    from ..models.envelope_data_metadata import EnvelopeDataMetadata
    from ..models.face_extraction import FaceExtraction
    from ..models.face_match import FaceMatch
    from ..models.quality_assessment import QualityAssessment


T = TypeVar("T", bound="EnvelopeData")


@_attrs_define
class EnvelopeData:
    """
    Attributes:
        id (Union[Unset, UUID]):
        metadata (Union[Unset, EnvelopeDataMetadata]): Operation-specific payload, shaped by the template or operation
            that ran.
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
             Example: {'policyNumber': {'value': '254H089SJ425', 'confidence': 98, 'page': 1, 'bbox': [0.62, 0.11, 0.83,
            0.14], 'bbox_confidence': 92}, 'totalPremium': {'value': '1840.00', 'confidence': 95}}.
        created_date (Union[Unset, datetime.datetime]):
        results (Union[Unset, list['ClassificationResult']]): `/Document/classifier` only: one entry per uploaded file.
        document_type (Union[Unset, str]): `/Document/zero-shot` only: the document type the model recognized.
        confidence (Union[Unset, float]): `/Document/zero-shot` only: certainty in `documentType`.
        fraud_blocked (Union[Unset, bool]): `/Document/extraction` only. Always `false`: fraud screening is advisory
            and never withholds the extraction. Kept for clients that already read it.
        fraud_request_id (Union[None, UUID, Unset]): `/Document/extraction` only: the fraud screening that ran on this
            document. Null when screening was disabled, not enabled for the tenant,
            or failed.
        quality (Union['QualityAssessment', None, Unset]): `/Document/extraction` only: the input-quality pre-flight.
            Null when it
            did not run. On a `2` (block) verdict the extraction did not run and
            `metadata` is null; on a `1` (warn) it ran and this carries the findings.
        image_urls (Union[None, Unset, list[str]]): `/Document/crop` only: signed URLs of the cropped images.
        documents (Union[Unset, list['CropDocument']]): `/Document/crop` only: each document found on the page, with
            where it sits.
        composite_image_url (Union[None, Unset, str]): `/Document/crop` only: signed URL of the composite image, when
            one was produced.
        request_id (Union[Unset, UUID]): `/Document/facematch` only: identifies this comparison. Facematch carries no
            `id`.
        extractions (Union[Unset, list['FaceExtraction']]): `/Document/facematch` only: the face found, or not, in each
            uploaded document.
        matches (Union[Unset, list['FaceMatch']]): `/Document/facematch` only: the selfie compared against each document
            face.
    """

    id: Union[Unset, UUID] = UNSET
    metadata: Union[Unset, "EnvelopeDataMetadata"] = UNSET
    created_date: Union[Unset, datetime.datetime] = UNSET
    results: Union[Unset, list["ClassificationResult"]] = UNSET
    document_type: Union[Unset, str] = UNSET
    confidence: Union[Unset, float] = UNSET
    fraud_blocked: Union[Unset, bool] = UNSET
    fraud_request_id: Union[None, UUID, Unset] = UNSET
    quality: Union["QualityAssessment", None, Unset] = UNSET
    image_urls: Union[None, Unset, list[str]] = UNSET
    documents: Union[Unset, list["CropDocument"]] = UNSET
    composite_image_url: Union[None, Unset, str] = UNSET
    request_id: Union[Unset, UUID] = UNSET
    extractions: Union[Unset, list["FaceExtraction"]] = UNSET
    matches: Union[Unset, list["FaceMatch"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.quality_assessment import QualityAssessment

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        metadata: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        created_date: Union[Unset, str] = UNSET
        if not isinstance(self.created_date, Unset):
            created_date = self.created_date.isoformat()

        results: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        document_type = self.document_type

        confidence = self.confidence

        fraud_blocked = self.fraud_blocked

        fraud_request_id: Union[None, Unset, str]
        if isinstance(self.fraud_request_id, Unset):
            fraud_request_id = UNSET
        elif isinstance(self.fraud_request_id, UUID):
            fraud_request_id = str(self.fraud_request_id)
        else:
            fraud_request_id = self.fraud_request_id

        quality: Union[None, Unset, dict[str, Any]]
        if isinstance(self.quality, Unset):
            quality = UNSET
        elif isinstance(self.quality, QualityAssessment):
            quality = self.quality.to_dict()
        else:
            quality = self.quality

        image_urls: Union[None, Unset, list[str]]
        if isinstance(self.image_urls, Unset):
            image_urls = UNSET
        elif isinstance(self.image_urls, list):
            image_urls = self.image_urls

        else:
            image_urls = self.image_urls

        documents: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.documents, Unset):
            documents = []
            for documents_item_data in self.documents:
                documents_item = documents_item_data.to_dict()
                documents.append(documents_item)

        composite_image_url: Union[None, Unset, str]
        if isinstance(self.composite_image_url, Unset):
            composite_image_url = UNSET
        else:
            composite_image_url = self.composite_image_url

        request_id: Union[Unset, str] = UNSET
        if not isinstance(self.request_id, Unset):
            request_id = str(self.request_id)

        extractions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.extractions, Unset):
            extractions = []
            for extractions_item_data in self.extractions:
                extractions_item = extractions_item_data.to_dict()
                extractions.append(extractions_item)

        matches: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.matches, Unset):
            matches = []
            for matches_item_data in self.matches:
                matches_item = matches_item_data.to_dict()
                matches.append(matches_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if created_date is not UNSET:
            field_dict["createdDate"] = created_date
        if results is not UNSET:
            field_dict["results"] = results
        if document_type is not UNSET:
            field_dict["documentType"] = document_type
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if fraud_blocked is not UNSET:
            field_dict["fraudBlocked"] = fraud_blocked
        if fraud_request_id is not UNSET:
            field_dict["fraudRequestId"] = fraud_request_id
        if quality is not UNSET:
            field_dict["quality"] = quality
        if image_urls is not UNSET:
            field_dict["imageUrls"] = image_urls
        if documents is not UNSET:
            field_dict["documents"] = documents
        if composite_image_url is not UNSET:
            field_dict["compositeImageUrl"] = composite_image_url
        if request_id is not UNSET:
            field_dict["requestId"] = request_id
        if extractions is not UNSET:
            field_dict["extractions"] = extractions
        if matches is not UNSET:
            field_dict["matches"] = matches

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.classification_result import ClassificationResult
        from ..models.crop_document import CropDocument
        from ..models.envelope_data_metadata import EnvelopeDataMetadata
        from ..models.face_extraction import FaceExtraction
        from ..models.face_match import FaceMatch
        from ..models.quality_assessment import QualityAssessment

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

        results = []
        _results = d.pop("results", UNSET)
        for results_item_data in _results or []:
            results_item = ClassificationResult.from_dict(results_item_data)

            results.append(results_item)

        document_type = d.pop("documentType", UNSET)

        confidence = d.pop("confidence", UNSET)

        fraud_blocked = d.pop("fraudBlocked", UNSET)

        def _parse_fraud_request_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                fraud_request_id_type_0 = UUID(data)

                return fraud_request_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        fraud_request_id = _parse_fraud_request_id(d.pop("fraudRequestId", UNSET))

        def _parse_quality(data: object) -> Union["QualityAssessment", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                quality_type_0 = QualityAssessment.from_dict(data)

                return quality_type_0
            except:  # noqa: E722
                pass
            return cast(Union["QualityAssessment", None, Unset], data)

        quality = _parse_quality(d.pop("quality", UNSET))

        def _parse_image_urls(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                image_urls_type_0 = cast(list[str], data)

                return image_urls_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        image_urls = _parse_image_urls(d.pop("imageUrls", UNSET))

        documents = []
        _documents = d.pop("documents", UNSET)
        for documents_item_data in _documents or []:
            documents_item = CropDocument.from_dict(documents_item_data)

            documents.append(documents_item)

        def _parse_composite_image_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        composite_image_url = _parse_composite_image_url(d.pop("compositeImageUrl", UNSET))

        _request_id = d.pop("requestId", UNSET)
        request_id: Union[Unset, UUID]
        if isinstance(_request_id, Unset):
            request_id = UNSET
        else:
            request_id = UUID(_request_id)

        extractions = []
        _extractions = d.pop("extractions", UNSET)
        for extractions_item_data in _extractions or []:
            extractions_item = FaceExtraction.from_dict(extractions_item_data)

            extractions.append(extractions_item)

        matches = []
        _matches = d.pop("matches", UNSET)
        for matches_item_data in _matches or []:
            matches_item = FaceMatch.from_dict(matches_item_data)

            matches.append(matches_item)

        envelope_data = cls(
            id=id,
            metadata=metadata,
            created_date=created_date,
            results=results,
            document_type=document_type,
            confidence=confidence,
            fraud_blocked=fraud_blocked,
            fraud_request_id=fraud_request_id,
            quality=quality,
            image_urls=image_urls,
            documents=documents,
            composite_image_url=composite_image_url,
            request_id=request_id,
            extractions=extractions,
            matches=matches,
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
