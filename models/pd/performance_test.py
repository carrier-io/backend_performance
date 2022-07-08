from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr

from ..api_tests import PerformanceApiTest
from ....shared.models.pd.test_parameters import TestParamsBase, TestParameter  # todo: workaround for this import


class PerformanceTestParam(TestParameter):
    ...


class PerformanceTestParams(TestParamsBase):
    test_parameters: List[PerformanceTestParam]

    @validator('test_parameters')
    def validate_default_params(cls, value, values, field):
        return value


class TestCommon(BaseModel):
    """
    Model of test itself without test_params or other plugin module's data
    """
    project_id: int
    test_uid: Optional[str]
    name: str
    parallel_runners: int
    location: str
    bucket: str
    file: str
    entrypoint: str
    runner: str
    env_vars: dict = {}
    customization: dict = {}
    cc_env_vars: dict = {}
    sources: list = []
    last_run: int
    job_type: constr(max_length=20)

    @root_validator
    def set_uuid(cls, values):
        if not values.get('test_uid'):
            values['test_uid'] = str(uuid4())
        return values

    @root_validator(pre=True, allow_reuse=True)
    def empty_str_to_none(cls, values):
        removed = []
        for k in list(values.keys()):
            if values[k] == '':
                removed.append(k)
                del values[k]
        return values


