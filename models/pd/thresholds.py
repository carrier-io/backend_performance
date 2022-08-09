from typing import Optional
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr

from ..api_tests import PerformanceApiTest
from ..api_reports import APIReport


class ThresholdPD(BaseModel):
    project_id: int
    test: Optional[str]
    test_id: int
    environment: str
    scope: str
    target: str
    aggregation: str
    comparison: str
    value: float

    @validator('test_id')
    def validate_test_exists(cls, value, values):
        test_id, test_name = PerformanceApiTest.query.with_entities(
            PerformanceApiTest.id,
            PerformanceApiTest.name
        ).filter(
            PerformanceApiTest.id == value
        ).first()
        assert test_name == values.get('test'), 'Test name is corrupted'
        return test_id

    @validator('environment')
    def validate_env_exists(cls, value, values):
        assert APIReport.query.filter(
            APIReport.environment == value,
            APIReport.project_id == values['project_id']
        ).first(), 'Result with this environment does not exist'
        return value

    @validator('scope')
    def validate_scope_exists(cls, value, values):
        if value in ['all', 'every']:
            return value

        assert APIReport.query.filter(
            APIReport.project_id == values['project_id'],
            APIReport.requests.contains(value)
        ).first(), 'Such scope does not exist'
        return value

    @validator('target')
    def validate_target(cls, value):
        assert value in {'throughput', 'error_rate', 'response_time'}, f'Target {value} is not supported'
        return value

    @validator('aggregation')
    def validate_aggregation(cls, value):
        assert value in {'max', 'min', 'avg', 'pct95', 'pct50'}, f'Aggregation {value} is not supported'
        return value

    @validator('comparison')
    def validate_comparison(cls, value):
        assert value in {'gte', 'lte', 'lt', 'gt', 'eq'}, f'Comparison {value} is not supported'
        return value
