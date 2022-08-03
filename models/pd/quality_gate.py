from pydantic import BaseModel, conint
from pylon.core.tools import log


class QualityGate(BaseModel):
    failed_thresholds_rate: conint(ge=1, le=100)
