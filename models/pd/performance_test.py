import json
import string
from typing import Optional, List, Iterable
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr
from pylon.core.tools import log
import re

from ...constants import JOB_CONTAINER_MAPPING
from ...utils.utils import parse_source
from ....shared.models.pd.test_parameters import TestParamsBase, TestParameter  # todo: workaround for this import

special_params = {'test_name', 'test_type', 'env_type'}


class PerformanceTestParam(TestParameter):
    ...


class PerformanceTestParamCreate(PerformanceTestParam):
    _reserved_names = special_params

    @validator('name')
    def reserved_names(cls, value):
        assert value not in cls._reserved_names, f'Name {value} is reserved. Please choose another name'
        return value


class PerformanceTestParamRun(PerformanceTestParam):
    _required_params = special_params


class PerformanceTestParams(TestParamsBase):
    test_parameters: List[PerformanceTestParam]

    @validator('test_parameters')
    def unique_names(cls, value: list):
        import collections
        duplicates = [item for item, count in collections.Counter(i.name for i in value).items() if count > 1]
        assert not duplicates, f'Duplicated names not allowed: {duplicates}'
        return value

    def exclude_params(self, exclude: Iterable):
        self.test_parameters = [
            p for p in self.test_parameters
            if p.name not in exclude
        ]
        return self

    @classmethod
    def from_control_tower(cls, data: dict):
        return cls(test_parameters=[
            {'name': k, 'default': v, 'description': 'Param from control tower'}
            for k, v in data.items()
        ])

    @classmethod
    def from_control_tower_cmd(cls, data: str):
        patt = re.compile(r'-J((\S+)=(\S+))')
        parsed = list(
            {'name': name, 'default': default, 'description': 'Param from control tower'}
            for _, name, default in
            re.findall(patt, data)
        )
        return cls(test_parameters=parsed)


class PerformanceTestParamsCreate(PerformanceTestParams):
    test_parameters: List[PerformanceTestParamCreate]


class PerformanceTestParamsRun(PerformanceTestParamsCreate):
    _required_params = special_params
    test_parameters: List[PerformanceTestParamRun]


class TestOverrideable(BaseModel):
    parallel_runners: Optional[int]
    location: str = 'default'
    env_vars: dict = {}
    customization: dict = {}
    cc_env_vars: dict = {}

    @validator('customization')
    def validate_customization(cls, value: dict):
        for k, v in list(value.items()):
            if any((k, v)):
                assert all((k, v)), 'All fields must be filled'
            else:
                del value[k]
        return value


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
