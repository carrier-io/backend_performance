from datetime import datetime
from typing import Optional, Union

from pydantic import ValidationError, parse_obj_as, List
from sqlalchemy import desc

from pylon.core.tools import web, log

from tools import rpc_tools, db_tools

from ..models.pd.performance_test import TestCommon, TestOverrideable
from ..models.pd.quality_gate import QualityGate
from ..models.pd.test_parameters import PerformanceTestParamsCreate, PerformanceTestParamsRun
from ..models.reports import Report
from ..models.summary_table_presets import BackendPerformanceSummaryTablePreset
from ..models.pd.summary_presets import SummaryPresetsPD
from ..models.tests import Test
from ..models.runners import Runner
from ..constants import JMETER_MAPPING, GATLING_MAPPING, EXECUTABLE_MAPPING
from ..utils.charts_utils import requests_summary, summary_table
from ..connectors.minio_connector import MinioConnector


class RPC:
    @web.rpc('backend_results_or_404', 'results_or_404')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def backend_results_or_404(self, run_id):
        return Report.query.get_or_404(run_id)

    @web.rpc('backend_performance_test_create_common_parameters',
             'parse_common_test_parameters')
    # @rpc_tools.wrap_exceptions(RuntimeError)
    # @rpc_tools.wrap_exceptions(ValidationError)
    def parse_common_test_parameters(
            self, project_id: int, test_params: dict, **kwargs
    ) -> dict:
        overrideable_only = kwargs.pop('overrideable_only', False)
        if overrideable_only:
            pd_object = TestOverrideable(
                **test_params
            )
        else:
            pd_object = TestCommon(
                project_id=project_id,
                **test_params
            )
        return pd_object.dict(**kwargs)

    @web.rpc('backend_performance_test_create_test_parameters', 'parse_test_parameters')
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_test_parameters(self, data: Union[list, dict], **kwargs) -> dict:
        purpose = kwargs.pop('purpose', None)
        if purpose == 'run':
            pd_object = PerformanceTestParamsRun(test_parameters=data)
        elif purpose == 'control_tower':
            pd_object = PerformanceTestParamsCreate.from_control_tower(data)
        else:
            pd_object = PerformanceTestParamsCreate(test_parameters=data)
        return pd_object.dict(**kwargs)

    @web.rpc('backend_performance_job_type_by_uid')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def job_type_by_uid(self, project_id: int, test_uid: str) -> Optional[str]:
        test = Test.query.filter(
            Test.get_api_filter(project_id, test_uid)
        ).first()
        if test:
            return test.job_type

    @web.rpc(f'backend_performance_test_create_integration_validate_quality_gate')
    @rpc_tools.wrap_exceptions(ValidationError)
    def backend_performance_test_create_integration_validate(self, data: dict,
            pd_kwargs: Optional[dict] = None, **kwargs
    ) -> dict:
        if not pd_kwargs:
            pd_kwargs = {}
        pd_object = QualityGate(**data)
        return pd_object.dict(**pd_kwargs)

    @web.rpc('backend_performance_execution_json_config_quality_gate')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def make_execution_json_config(self, integration_data: dict) -> dict:
        """ Prepare execution_json for this integration """
        return integration_data

    @web.rpc('backend_performance_get_tests')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_tests(self, project_id: int) -> list[Test]:
        """ Gets all created tests """
        return Test.query.filter_by(project_id=project_id).all()

    @web.rpc('backend_performance_get_reports')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_reports(
            self, project_id: int,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            unique: bool = False,
    ) -> list[Report]:
        """ Gets all reports filtered by time"""

        def _get_unique_reports(objects: list[Report]) -> list[Report]:
            unique_combinations = {}
            for obj in objects:
                combination = (obj.test_uid, obj.environment, obj.type)
                stored_obj = unique_combinations.get(combination)
                if stored_obj is None or obj.start_time > stored_obj.start_time:
                    unique_combinations[combination] = obj

            return list(unique_combinations.values())

        query = Report.query.filter(
            Report.project_id == project_id,
        ).order_by(
            desc(Report.start_time)
        )

        if start_time:
            query = query.filter(Report.start_time >= start_time.isoformat())

        if end_time:
            query = query.filter(Report.end_time <= end_time.isoformat())

        reports = query.all()
        if unique:
            reports = _get_unique_reports(reports)

        return reports

    @web.rpc('populate_backend_runners_table')
    def populate_runners_table(self, project_id):
        runners = []

        def _create_runner_objects(mapping, container_type):
            for runner in mapping:
                runners.append(Runner(
                    project_id=project_id,
                    container_type=container_type,
                    config={runner: mapping[runner]},
                    is_active=True,
                    is_default=True
                ))

        _create_runner_objects(JMETER_MAPPING, 'jmeter')
        _create_runner_objects(GATLING_MAPPING, 'gatling')
        _create_runner_objects(EXECUTABLE_MAPPING, 'executable_jar')
        db_tools.bulk_save(runners)

    @web.rpc('get_requests_summary')
    def get_requests_summary(self, args):
        connector = MinioConnector(**args)
        return requests_summary(connector)

    @web.rpc('get_table_summary')
    def get_table_summary(self, args):
        connector = MinioConnector(**args)
        return summary_table(connector)

    @web.rpc('backend_performance_get_summary_table_presets', 'get_summary_table_presets')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_summary_table_presets(self, project_id: int):
        query = BackendPerformanceSummaryTablePreset.query.filter(
            BackendPerformanceSummaryTablePreset.project_id == project_id,
            ).all()
        return parse_obj_as(List[SummaryPresetsPD], query)

    @web.rpc('backend_performance_create_summary_table_presets', 'create_summary_table_presets')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def create_summary_table_presets(self, project_id: int, preset: dict):
        preset = SummaryPresetsPD.validate(preset).dict()
        preset_db = BackendPerformanceSummaryTablePreset(project_id=project_id, **preset)
        preset_db.insert()
        return preset_db.to_json()

    @web.rpc('backend_performance_update_summary_table_presets', 'update_summary_table_presets')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def update_summary_table_presets(self, project_id: int, preset: dict):
        preset = SummaryPresetsPD.validate(preset).dict()
        preset_db = BackendPerformanceSummaryTablePreset.query.filter(
            BackendPerformanceSummaryTablePreset.project_id == project_id,
            BackendPerformanceSummaryTablePreset.name == preset['name'],
            ).first()
        preset_db.fields = preset['fields']
        preset_db.commit()
        return preset_db.to_json()

    @web.rpc('backend_performance_delete_summary_table_presets', 'delete_summary_table_presets')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def delete_summary_table_presets(self, project_id: int, preset_name: str):
        if preset_db := BackendPerformanceSummaryTablePreset.query.filter(
            BackendPerformanceSummaryTablePreset.project_id == project_id,
            BackendPerformanceSummaryTablePreset.name == preset_name
            ).one_or_none():
            preset_db.delete()
            preset_db.commit()
