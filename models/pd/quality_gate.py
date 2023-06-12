from pydantic import BaseModel, conint, PositiveInt


class QualityGateSLA(BaseModel):
    checked: bool


class QualityGateBaseline(BaseModel):
    checked: bool
    rt_baseline_comparison_mecric: str


class QualityGateSettingsSummary(BaseModel):
    check_response_time: bool
    response_time_deviation: PositiveInt
    check_error_rate: bool
    error_rate_deviation: conint(ge=0, le=100)
    check_throughput: bool
    throughput_deviation: PositiveInt


class QualityGateSettingsRequests(BaseModel):
    check_response_time: bool
    response_time_deviation: PositiveInt
    check_error_rate: bool
    error_rate_deviation: conint(ge=0, le=100)
    check_throughput: bool
    throughput_deviation: PositiveInt
    percentage_of_failed_requests: conint(ge=0, le=100)


class QualityGateSettings(BaseModel):
    summary_results: QualityGateSettingsSummary
    per_request_results: QualityGateSettingsRequests


class QualityGate(BaseModel):
    SLA: QualityGateSLA
    baseline: QualityGateBaseline
    settings: QualityGateSettings
