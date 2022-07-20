import string
from typing import Optional, List, Iterable
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr
from pylon.core.tools import log

from ...constants import JOB_CONTAINER_MAPPING
from ...utils.utils import parse_source
from ....shared.models.pd.test_parameters import TestParamsBase, TestParameter  # todo: workaround for this import

_default_params = {
        # "influx.db":
        # "test_name":
        "influx.port": "{{secret.influx_port}}",
        "influx.host": "{{secret.influx_ip}}",
        "influx.username": "{{secret.influx_user}}",
        "influx.password": "{{secret.influx_password}}",
        "galloper_url": "{{secret.galloper_url}}",
        "comparison_db": "{{secret.comparison_db}}",
        "telegraf_db": "{{secret.telegraf_db}}",
        "loki_host": "{{secret.loki_host}}",
        "loki_port": "{{secret.loki_port}}",
        # "test_type": "default",
        # "env_type": "not_specified"
    }


class PerformanceTestParam(TestParameter):
    @root_validator
    def _default_params(cls, values: dict):
        if values['name'] in _default_params and not values.get('default'):
            values['default'] = _default_params[values['name']]
        return values

    # @validator('name', pre=True, allow_reuse=True)
    # def empty_str_to_none(cls, value):
    #     if value == '':
    #         return None
    #     return value


class PerformanceTestParams(TestParamsBase):
    test_parameters: List[PerformanceTestParam]

    @validator('test_parameters', pre=True)
    def validate_default_params(cls, value: list):
        missing_params = set(
            _default_params.keys()
        ).difference(
            set(i.get('name') for i in value)
        )
        for i in missing_params:
            value.append(PerformanceTestParam(name=i).dict())

        return value

    def exclude_params(self, exclude: Iterable, leave_manually_set=True):
        self.test_parameters = [
            p for p in self.test_parameters
            if p.name not in exclude and p.default != _default_params.get(p.name)
        ]
        return self


class TestOverrideable(BaseModel):
    parallel_runners: Optional[int]
    location: str = 'default'
    env_vars: dict = {}
    customization: dict = {}
    cc_env_vars: dict = {}


class TestCommon(TestOverrideable):
    """
    Model of test itself without test_params or other plugin module's data
    """
    project_id: int
    test_uid: Optional[str]
    name: str
    test_type: str
    env_type: str
    parallel_runners: int
    entrypoint: str
    runner: str
    source: dict

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

    @validator('name', 'test_type', 'env_type')
    def check_allowed_chars(cls, value):
        try:
            int(value[0])
            assert False, 'Can not start with a number'
        except ValueError:
            ...

        valid_chars = f'{string.ascii_letters}{string.digits}_'
        assert all(c in valid_chars for c in value), 'Only letters, numbers and "_" allowed'
        return value

    @validator('runner')
    def validate_runner(cls, value):
        assert value in JOB_CONTAINER_MAPPING.keys(), \
            "Runner version is not supported. Available versions: {}".format(
                list(JOB_CONTAINER_MAPPING.keys())
            )
        return value

    @validator('source')
    def validate_sources(cls, value: dict, values):
        validated = parse_source(value)
        return {
            'name': value['name'],
            **validated.dict()
        }
