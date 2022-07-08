from typing import Optional

from tools import rpc_tools
from ..models.api_reports import APIReport
from pylon.core.tools import web
from pydantic import ValidationError

from ..models.api_tests import PerformanceApiTest
from ..models.pd.performance_test import TestCommon


class RPC:
    @web.rpc('backend_results_or_404')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def backend_results_or_404(self, run_id):
        return APIReport.query.get_or_404(run_id)

    @web.rpc('backend_test_create_common_parameters', 'parse_common_test_parameters')
    # @rpc_tools.wrap_exceptions(RuntimeError)
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_common_test_parameters(self, project_id: int, name: str, description: str, **kwargs) -> dict:
        project = self.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        pd_object = TestCommon(
            project_id=project.id,
            project_name=project.name,
            name=name,
            description=description
        )
        return pd_object.dict(**kwargs)

    @web.rpc('backend_performance_job_type_by_uid')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def job_type_by_uid(self, project_id: int, test_uid: str) -> Optional[str]:
        test = PerformanceApiTest.query.filter(
                PerformanceApiTest.get_api_filter(project_id, test_uid)
        ).first()
        if test:
            return test.job_type
