from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fraud_verification_policy_action import FraudVerificationPolicyAction
from ..models.fraud_verification_verdict import FraudVerificationVerdict
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fraud_check import FraudCheck
    from ..models.fraud_signal import FraudSignal


T = TypeVar("T", bound="FraudVerification")


@_attrs_define
class FraudVerification:
    """
    Attributes:
        request_id (UUID): Id of the analysis. Read it back with `GET /api/v1/fraud-verify/{requestId}`.
        verdict (FraudVerificationVerdict):
        risk_score (float): The aggregated risk the verdict was taken from.
        policy_action (FraudVerificationPolicyAction): Your tenant's enforcement policy applied to the verdict. `block`
            means "do not
            proceed without a person"; it is a routing decision, not a rejection.
        reused (bool): True when an earlier analysis of the same file was returned, free of charge.
        signals (list['FraudSignal']):
        checks (list['FraudCheck']): Every check that ran, in order.
        failed_coverage (list[str]): Checks that could not run on this document.
        ai_generated_likelihood (Union[Unset, float]): How likely the text was machine-generated. Never decisive on its
            own.
        pipeline_version (Union[Unset, str]): Version of the checks that produced this analysis.
    """

    request_id: UUID
    verdict: FraudVerificationVerdict
    risk_score: float
    policy_action: FraudVerificationPolicyAction
    reused: bool
    signals: list["FraudSignal"]
    checks: list["FraudCheck"]
    failed_coverage: list[str]
    ai_generated_likelihood: Union[Unset, float] = UNSET
    pipeline_version: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        request_id = str(self.request_id)

        verdict = self.verdict.value

        risk_score = self.risk_score

        policy_action = self.policy_action.value

        reused = self.reused

        signals = []
        for signals_item_data in self.signals:
            signals_item = signals_item_data.to_dict()
            signals.append(signals_item)

        checks = []
        for checks_item_data in self.checks:
            checks_item = checks_item_data.to_dict()
            checks.append(checks_item)

        failed_coverage = self.failed_coverage

        ai_generated_likelihood = self.ai_generated_likelihood

        pipeline_version = self.pipeline_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "requestId": request_id,
                "verdict": verdict,
                "riskScore": risk_score,
                "policyAction": policy_action,
                "reused": reused,
                "signals": signals,
                "checks": checks,
                "failedCoverage": failed_coverage,
            }
        )
        if ai_generated_likelihood is not UNSET:
            field_dict["aiGeneratedLikelihood"] = ai_generated_likelihood
        if pipeline_version is not UNSET:
            field_dict["pipelineVersion"] = pipeline_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fraud_check import FraudCheck
        from ..models.fraud_signal import FraudSignal

        d = dict(src_dict)
        request_id = UUID(d.pop("requestId"))

        verdict = FraudVerificationVerdict(d.pop("verdict"))

        risk_score = d.pop("riskScore")

        policy_action = FraudVerificationPolicyAction(d.pop("policyAction"))

        reused = d.pop("reused")

        signals = []
        _signals = d.pop("signals")
        for signals_item_data in _signals:
            signals_item = FraudSignal.from_dict(signals_item_data)

            signals.append(signals_item)

        checks = []
        _checks = d.pop("checks")
        for checks_item_data in _checks:
            checks_item = FraudCheck.from_dict(checks_item_data)

            checks.append(checks_item)

        failed_coverage = cast(list[str], d.pop("failedCoverage"))

        ai_generated_likelihood = d.pop("aiGeneratedLikelihood", UNSET)

        pipeline_version = d.pop("pipelineVersion", UNSET)

        fraud_verification = cls(
            request_id=request_id,
            verdict=verdict,
            risk_score=risk_score,
            policy_action=policy_action,
            reused=reused,
            signals=signals,
            checks=checks,
            failed_coverage=failed_coverage,
            ai_generated_likelihood=ai_generated_likelihood,
            pipeline_version=pipeline_version,
        )

        fraud_verification.additional_properties = d
        return fraud_verification

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
