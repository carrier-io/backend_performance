from typing import Optional, List, ForwardRef
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator

from ..api_tests import PerformanceApiTest
from ....shared.models.pd.test_parameters import TestParameter  # todo: workaround for this import


class TestParamsBase(BaseModel):
    """
    Base case class for performance test.
    Used as a parent class for actual security tet model
    """
    _test_params_mapping = {}
    _required_params = set()

    # the following fields are optional as they are set in test_parameters validator using _test_params_mapping

    test_parameters: List[TestParameter]

    @classmethod
    def from_orm(cls, db_obj: PerformanceApiTest):
        raise NotImplementedError
        instance = cls(
            test_parameters=db_obj.test_parameters,
            urls_to_scan=db_obj.urls_to_scan,
            urls_exclusions=[] if db_obj.urls_exclusions == [''] else db_obj.urls_exclusions,
            scan_location=db_obj.scan_location
        )
        return instance

    def update(self, other: ForwardRef('TestParamsBase')):
        test_params_names = set(map(lambda tp: tp.name, other.test_parameters))
        modified_params = other.test_parameters
        for tp in self.test_parameters:
            if tp.name not in test_params_names:
                modified_params.append(tp)
        self.test_parameters = modified_params


TestParamsBase.update_forward_refs()


class TestCommon(BaseModel):
    """
    Model of test itself without test_params or other plugin module's data
    """
    project_id: int
    project_name: str
    test_uid: Optional[str]
    name: str
    description: Optional[str] = ''

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
