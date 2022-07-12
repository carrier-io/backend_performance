import string
from typing import Optional, List, Iterable
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr
from pylon.core.tools import log

from ..api_tests import PerformanceApiTest
from ...constants import JOB_CONTAINER_MAPPING
from ....shared.models.pd.test_parameters import TestParamsBase, TestParameter  # todo: workaround for this import

_default_params = {
        "influx.port": "{{secret.influx_port}}",
        "influx.host": "{{secret.influx_ip}}",
        "influx.username": "{{secret.influx_user}}",
        "influx.password": "{{secret.influx_password}}",
        "galloper_url": "{{secret.galloper_url}}",
        # "influx.db":
        # "test_name":
        "comparison_db": "{{secret.comparison_db}}",
        "telegraf_db": "{{secret.telegraf_db}}",
        "loki_host": "{{secret.loki_host}}",
        "loki_port": "{{secret.loki_port}}",
        "test_type": "default",
        "env_type": "not_specified"
    }


class PerformanceTestParam(TestParameter):
    @root_validator
    def _default_params(cls, values: dict):
        if values['name'] in _default_params and not values.get('default'):
            values['default'] = _default_params[values['name']]
        return values


class PerformanceTestParams(TestParamsBase):
    test_parameters: List[PerformanceTestParam]

    @validator('test_parameters', pre=True)
    def validate_default_params(cls, value: list, field):
        log.warning('Validating default params %s', value)
        missing_params = set(
            _default_params.keys()
        ).difference(
            set(i.get('name') for i in value)
        )
        for i in missing_params:
            value.append(PerformanceTestParam(name=i).dict())

        return value

    def exclude_params(self, exclude: Iterable):
        self.test_parameters = [p for p in self.test_parameters if p.name not in exclude]
        return self




class TestCommon(BaseModel):
    """
    Model of test itself without test_params or other plugin module's data
    """
    project_id: int
    test_uid: Optional[str]
    name: str
    parallel_runners: int
    location: str = 'default'
    bucket: str
    file: str
    entrypoint: str
    runner: str
    env_vars: dict = {}
    customization: dict = {}
    cc_env_vars: dict = {}
    sources: list = []
    job_type: Optional[constr(max_length=20)]

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

    ## check if this is needed
    # @validator('name')
    # def sanitize(cls, value):
    #     valid_chars = "_%s%s" % (string.ascii_letters, string.digits)
    #     return ''.join(c for c in value if c in valid_chars)

    @validator('runner')
    def validate_runner(cls, value):
        assert value in JOB_CONTAINER_MAPPING.keys(), \
            "Runner version is not supported. Available versions: {}".format(
                list(JOB_CONTAINER_MAPPING.keys())
            )
        return value

    @validator('job_type')
    def validate_job_type(cls, value, values):
        if not value:
            # return JOB_CONTAINER_MAPPING[values['runner']]['job_type']
            return JOB_CONTAINER_MAPPING[values['runner']]['job_type']
        return value
