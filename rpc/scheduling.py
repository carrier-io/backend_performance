from collections import defaultdict
from datetime import datetime
from pylon.core.tools import web, log

from tools import rpc_tools

from sqlalchemy import text, String
from ..models.pd.test_parameters import PerformanceTestParams
from ..models.reports import Report
from ..models.tests import Test
from ..utils.report_utils import delete_project_reports
from ..utils.retention_utils import RetentionModel
from ..utils.utils import run_test


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
            'cron': '0 0 * * *',
            'rpc_func': 'backend_performance_run_retention_check'
        }

    @web.rpc('backend_performance_run_retention_check', 'run_retention_check')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def run_retention_check(self) -> None:
        log.info('Running backend_performance_run_retention_check...')
        query = Report.query.with_entities(
            Report.id,
            Report.project_id,
            Report.retention,
            Report.start_time,
            Report.end_time
        ).filter(
            # func.lower(Report.test_status['status'].cast(String)).in_(('"finished"', '"failed"', '"success"'))
            Report.end_time.isnot(None),
            # Report.retention.isnot(None),
            Report.retention.cast(String) != text("'null'"),
        )
        reports_to_delete = defaultdict(set)
        for report_id, project_id, retention, start_time, end_time in query.all():
            # log.info("DELETE RPC %s", (report_id, retention, start_time, end_time))
            retention = RetentionModel.parse_obj(retention)
            ttl = retention.compute_ttl(start_time, end_time)
            if ttl < datetime.utcnow():
                log.critical('Report %s will be deleted by retention. Retention: %s', report_id, retention)
                reports_to_delete[project_id].add(report_id)
            else:
                log.info('Report %s is ok. TTL: %s', report_id, ttl)

        for project_id, delete_ids in reports_to_delete.items():
            delete_project_reports(project_id, list(delete_ids))
