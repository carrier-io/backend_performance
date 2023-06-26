from datetime import datetime
from typing import Optional, Union

from pydantic import ValidationError
from pylon.core.tools import web, log
from sqlalchemy import desc

from tools import rpc_tools, db_tools
from ..models.pd.performance_test import TestCommon, TestOverrideable
from ..models.pd.quality_gate import QualityGate
from ..models.pd.test_parameters import PerformanceTestParams, PerformanceTestParamsCreate, \
    PerformanceTestParamsRun
from ..models.reports import Report
from ..models.tests import Test
from ..models.runners import Runner
from ..utils.utils import run_test
from ..constants import JMETER_MAPPING, GATLING_MAPPING, EXECUTABLE_MAPPING


class RPC:
    @web.rpc('backend_performance_run_scheduled_test', 'run_scheduled_test')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def run_scheduled_test(self, test_id: int, test_params: list) -> dict:
        test = Test.query.filter(Test.id == test_id).one()
        test_params_schedule_pd = PerformanceTestParams(test_parameters=test_params)
        test_params_existing_pd = PerformanceTestParams.from_orm(test)
        test_params_existing_pd.update(test_params_schedule_pd)
        test.__dict__.update(test_params_existing_pd.dict())
        return run_test(test)

    @web.rpc('backend_performance_get_retention_schedule_data')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_retention_schedule_data(self) -> dict:
        return {
            'name': 'backend_performance_run_retention_check',
            'cron': '*/1 * * * *',
            'rpc_func': 'backend_performance_run_retention_check'
        }

    @web.rpc('backend_performance_run_retention_check', 'run_retention_check')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def run_retention_check(self) -> None:
        log.info('Running backend_performance_run_retention_check...')
