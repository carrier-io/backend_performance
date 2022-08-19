from pylon.core.tools import log
from typing import List, Iterable
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator, constr
import re

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
