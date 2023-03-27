from pydantic import BaseModel, conint, PositiveInt
from pylon.core.tools import log


class QualityGate(BaseModel):   
    SLA: bool
    baseline: bool
    request_check: bool
    summary_check: bool
    summary_check_response_time: bool
    summary_check_error_rate: bool
    summary_check_throughput: bool
    request_check_response_time: bool
    request_check_error_rate: bool
    request_check_throughput: bool
    summary_response_time_deviation: PositiveInt
    summary_error_rate_deviation: conint(ge=0, le=100)
    summary_throughput_deviation: PositiveInt
    request_response_time_deviation: PositiveInt
    request_error_rate_deviation: conint(ge=0, le=100)
    request_throughput_deviation: PositiveInt
    percentage_of_failed_requests: conint(ge=0, le=100)
    rt_baseline_comparison_mecric: str
