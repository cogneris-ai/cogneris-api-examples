"""Contains all the data models used in inputs/outputs"""

from .api_error import ApiError
from .api_error_details_type_0 import ApiErrorDetailsType0
from .artifact import Artifact
from .artifact_upload_envelope import ArtifactUploadEnvelope
from .classification_result import ClassificationResult
from .classify_documents_body import ClassifyDocumentsBody
from .crop_document import CropDocument
from .crop_document_body import CropDocumentBody
from .document_job import DocumentJob
from .document_job_cancellation import DocumentJobCancellation
from .document_job_cancellation_envelope import DocumentJobCancellationEnvelope
from .document_job_envelope import DocumentJobEnvelope
from .document_job_list import DocumentJobList
from .document_job_list_envelope import DocumentJobListEnvelope
from .document_job_operation import DocumentJobOperation
from .document_job_status import DocumentJobStatus
from .document_job_submission import DocumentJobSubmission
from .document_job_submission_envelope import DocumentJobSubmissionEnvelope
from .document_job_submit_operation import DocumentJobSubmitOperation
from .document_job_submit_status import DocumentJobSubmitStatus
from .envelope import Envelope
from .envelope_data import EnvelopeData
from .envelope_data_metadata import EnvelopeDataMetadata
from .extract_document_body import ExtractDocumentBody
from .extracted_field import ExtractedField
from .face_extraction import FaceExtraction
from .face_match import FaceMatch
from .face_match_document_body import FaceMatchDocumentBody
from .portal_channels import PortalChannels
from .portal_form import PortalForm
from .portal_magic_link import PortalMagicLink
from .portal_magic_link_opt_in import PortalMagicLinkOptIn
from .portal_magic_link_opt_in_source import PortalMagicLinkOptInSource
from .portal_magic_link_request import PortalMagicLinkRequest
from .portal_send_channel import PortalSendChannel
from .problem_details import ProblemDetails
from .problem_details_errors_item import ProblemDetailsErrorsItem
from .problem_details_errors_item_details_type_0 import ProblemDetailsErrorsItemDetailsType0
from .quality_assessment import QualityAssessment
from .quality_finding import QualityFinding
from .quality_verdict import QualityVerdict
from .service_error_envelope import ServiceErrorEnvelope
from .service_error_envelope_data_type_0 import ServiceErrorEnvelopeDataType0
from .service_response_meta import ServiceResponseMeta
from .split_document_body import SplitDocumentBody
from .submit_document_job_body import SubmitDocumentJobBody
from .upload_artifact_body import UploadArtifactBody
from .zero_shot_document_body import ZeroShotDocumentBody

__all__ = (
    "ApiError",
    "ApiErrorDetailsType0",
    "Artifact",
    "ArtifactUploadEnvelope",
    "ClassificationResult",
    "ClassifyDocumentsBody",
    "CropDocument",
    "CropDocumentBody",
    "DocumentJob",
    "DocumentJobCancellation",
    "DocumentJobCancellationEnvelope",
    "DocumentJobEnvelope",
    "DocumentJobList",
    "DocumentJobListEnvelope",
    "DocumentJobOperation",
    "DocumentJobStatus",
    "DocumentJobSubmission",
    "DocumentJobSubmissionEnvelope",
    "DocumentJobSubmitOperation",
    "DocumentJobSubmitStatus",
    "Envelope",
    "EnvelopeData",
    "EnvelopeDataMetadata",
    "ExtractDocumentBody",
    "ExtractedField",
    "FaceExtraction",
    "FaceMatch",
    "FaceMatchDocumentBody",
    "PortalChannels",
    "PortalForm",
    "PortalMagicLink",
    "PortalMagicLinkOptIn",
    "PortalMagicLinkOptInSource",
    "PortalMagicLinkRequest",
    "PortalSendChannel",
    "ProblemDetails",
    "ProblemDetailsErrorsItem",
    "ProblemDetailsErrorsItemDetailsType0",
    "QualityAssessment",
    "QualityFinding",
    "QualityVerdict",
    "ServiceErrorEnvelope",
    "ServiceErrorEnvelopeDataType0",
    "ServiceResponseMeta",
    "SplitDocumentBody",
    "SubmitDocumentJobBody",
    "UploadArtifactBody",
    "ZeroShotDocumentBody",
)
