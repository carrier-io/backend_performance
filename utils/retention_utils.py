from datetime import timedelta, datetime

from pylon.core.tools import log
from typing import Optional

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, root_validator


class RetentionModel(BaseModel):
    years: Optional[int] = 0
    months: Optional[int] = 0
    weeks: Optional[int] = 0
    days: Optional[int] = 0

    @root_validator(pre=True)
    def check_at_least_one_set(cls, values: dict):
        assert any(values), 'At least 1 value must be set'
        rd = relativedelta(**values).normalized()
        for f in {'years', 'months', *values.keys()}:
            val = getattr(rd, f)
            if val:
                values[f] = val
        return values

    @property
    def delta(self) -> relativedelta:
        return relativedelta(**self.dict())

    def compute_ttl(self, start_time: str, end_time: Optional[str] = None) -> datetime:
        time_point = end_time or start_time
        time_point = datetime.fromisoformat(time_point.strip('Z'))
        ttl = time_point + self.delta
        return ttl


def serialize_timedelta(td: Optional[timedelta]) -> Optional[dict]:
    if not td:
        return
    d = datetime.min + td
    return {
        'years': d.year - 1,
        'month': d.month - 1,
        'days': d.day - 1
    }

