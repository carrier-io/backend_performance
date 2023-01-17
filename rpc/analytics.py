from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator
from sqlalchemy import String, literal_column, asc, func
from collections import OrderedDict, defaultdict

from pylon.core.tools import web, log

from ..connectors.minio import get_client
from ..models.baselines import Baseline
from ..models.reports import Report

from tools import rpc_tools


class ReportBuilderReflection(BaseModel):
    project_id: int
    id: int
    build_id: str
    name: str
    bucket_name: Optional[str]
    # report_file_name: Optional[str]

    @validator('bucket_name', always=True)
    def set_bucket_name(cls, value: str, values: dict):
        name = values["name"].replace('_', '').lower()
        return f'p--{values["project_id"]}.{name}'

    class Config:
        orm_mode = True


class ReportResultsModel(BaseModel):
    time: str
    total: int
    min: int
    max: int
    median: int
    pct90: int
    pct95: int
    pct99: int
    onexx: int
    twoxx: int
    threexx: int
    fourxx: int
    fivexx: int

    @validator('time')
    def time_formatter(cls, value: str):
        return value.strip('Z')

    class Config:
        fields = {
            'onexx': '1xx',
            'twoxx': '2xx',
            'threexx': '3xx',
            'fourxx': '4xx',
            'fivexx': '5xx',
        }



columns = OrderedDict((
    ('id', Report.id),
    ('build_id', Report.build_id),
    ('group', literal_column("'backend_performance'").label('group')),
    ('name', Report.name),
    ('start_time', Report.start_time),
    ('test_type', Report.type),
    ('test_env', Report.environment),
    ('aggregation_min', Report._min),
    ('aggregation_max', Report._max),
    ('aggregation_mean', Report.mean),
    ('aggregation_pct50', Report.pct50),
    ('aggregation_pct75', Report.pct75),
    ('aggregation_pct90', Report.pct90),
    ('aggregation_pct95', Report.pct95),
    ('aggregation_pct99', Report.pct99),
    ('throughput', Report.throughput),
    ('status', Report.test_status['status']),
    ('duration', Report.duration),
    ('total', Report.total),
    ('failures', Report.failures),
    ('tags', Report.tags)
))


class RPC:
    @web.rpc('performance_analysis_test_runs_backend_performance')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def test_runs(self, project_id: int,
                  start_time, end_time=None) -> tuple:
        log.info('backend_performance rpc | %s | %s', project_id, [start_time, end_time, ])

        query = Report.query.with_entities(
            *columns.values()
        ).filter(
            Report.project_id == project_id,
            Report.start_time >= start_time,
            func.lower(Report.test_status['status'].cast(String)).in_(('"finished"', '"failed"', '"success"'))
        ).order_by(
            asc(Report.start_time)
        )

        if end_time:
            query.filter(Report.end_time <= end_time)

        return tuple(zip(columns.keys(), i) for i in query.all())

    @web.rpc('backend_performance_get_baseline_report_id')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_baseline_report_id(self, project_id: int, test_name: str, test_env: str) -> Optional[int]:
        result = Baseline.query.with_entities(Baseline.report_id).filter(
            Baseline.project_id == project_id,
            Baseline.test == test_name,
            Baseline.environment == test_env,
        ).first()
        try:
            return result[0]
        except (TypeError, IndexError):
            return

    @web.rpc('backend_performance_get_results_by_ids')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def get_results_by_ids(self, project_id: int, report_ids: list):
        query = Report.query.with_entities(
            *columns.values()
        ).filter(
            Report.project_id == project_id,
            Report.id.in_(report_ids),
            # func.lower(Report.test_status['status'].cast(String)).in_(('"finished"', '"failed"', '"success"'))
        )

        return tuple(zip(columns.keys(), i) for i in query.all())

    @web.rpc('get_backend_results', 'get_backend_results')
    def get_ui_results(self, bucket: str, file_name: str, project_id: int) -> list:
        client = get_client(project_id)
        return client.select_object_content(bucket, file_name)

    @web.rpc('backend_performance_compile_builder_data', 'compile_builder_data')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def compile_builder_data(self, project_id: int, reports: list):
        data = dict()
        all_requests = set()
        earliest_date = None
        for report in reports:
            if isinstance(report, dict):
                report_reflection = ReportBuilderReflection(**report, project_id=project_id)
            else:
                report_reflection = ReportBuilderReflection.from_orm(report)

            log.info(report_reflection.dict())

            data[report_reflection.id] = defaultdict(dict)

            for time_aggregation in ('1s', '5s', '30s', '1m', '5m', '10m'):
                report_file_name = f'{report_reflection.build_id}_{time_aggregation}.csv.gz'
                results = self.get_backend_results(
                    report_reflection.bucket_name,
                    report_file_name,
                    project_id
                )

                for r in results:
                    request_name = r.pop('request_name')
                    all_requests.add(request_name)
                    result_model = ReportResultsModel.parse_obj(r)

                    try:
                        data[report_reflection.id][time_aggregation][request_name].append(result_model.dict())
                    except KeyError:
                        data[report_reflection.id][time_aggregation][request_name] = [result_model.dict()]

                    current_date = datetime.fromisoformat(result_model.time)
                    if earliest_date is None or earliest_date > current_date:
                        earliest_date = current_date

        return {
            'datasets': data,
            'all_requests': list(all_requests),
            'earliest_date': earliest_date.isoformat()
        }
