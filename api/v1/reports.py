import re
from traceback import format_exc
from typing import List

from pydantic import parse_obj_as
from sqlalchemy import and_
from json import loads

from flask_restful import Resource
from io import BytesIO
from collections import defaultdict
from flask import request
from pylon.core.tools import log

from ...models.pd.report import ReportCreateSerializer, ReportGetSerializer
from ...models.pd.test_parameters import PerformanceTestParamsRun
from ...models.baselines import Baseline
from ...models.reports import Report
from ...models.tests import Test
from ...connectors.influx_connector import InfluxConnector
from tools import MinioClient, api_tools, auth, LokiLogFetcher
from influxdb.exceptions import InfluxDBClientError


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
            "administration": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int):
        args = request.args
        if args.get("report_id"):
            report = Report.query.filter(
                Report.project_id == project_id,
                Report.id == args.get("report_id")
            ).first_or_404()
            return ReportGetSerializer.from_orm(report).dict(), 200
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        total, res = api_tools.get(project.id, args, Report)
        reports = parse_obj_as(List[ReportGetSerializer], res)
        return {"total": total, "rows": [i.dict() for i in reports]}, 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int):
        '''
            create report from control tower?
        '''
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)

        # TODO: we need to check api performance tests quota here
        # if not ProjectQuota.check_quota(project_id=project_id, quota='performance_test_runs'):
        #     return {"Forbidden": "The number of performance test runs allowed in the project has been exceeded"}

        # test_config = None
        if 'test_params' in args:
            try:
                test = Test.query.filter(
                    Test.uid == args.get('test_id')
                ).first()
                # test._session.expunge(test) # maybe we'll need to detach object from orm
                test.__dict__['test_parameters'] = test.filtered_test_parameters_unsecret(
                    PerformanceTestParamsRun.from_control_tower_cmd(
                        args['test_params']
                    ).dict()['test_parameters']
                )
            except Exception as e:
                log.error('Error parsing params from control tower %s', format_exc())
                return f'Error parsing params from control tower: {e}', 400

        report = Report(
            name=args["test_name"],
            project_id=project.id,
            environment=args["environment"],
            type=args["type"],
            # end_time=None,
            start_time=args["start_time"],
            # failures=0,
            # total=0,
            # thresholds_missed=0,
            # throughput=0,
            vusers=args["vusers"],
            # pct50=0,
            # pct75=0,
            # pct90=0,
            # pct95=0,
            # pct99=0,
            # _max=0,
            # _min=0,
            # mean=0,
            duration=args["duration"],
            build_id=args["build_id"],
            lg_type=args["lg_type"],
            # onexx=0,
            # twoxx=0,
            # threexx=0,
            # fourxx=0,
            # fivexx=0,
            # requests=[],
            test_uid=args.get("test_id"),
        )

        # report_model = ReportCreateSerializer(**args, project_id=project.id, test_uid=args.get("test_id"), name=args['test_name'])
        # report2 = Report(**report_model.dict(by_alias=True))
        # d1 = report.to_json()
        # d2 = report2.to_json()
        # for k in d1.keys():
        #     log.info('comparing dicts %s', [k, d1[k], d2[k]])
        #     assert d1[k] == d2[k], 'DICTS NOT EQUAL IN %s' % k

        # if test_config:
        #     report.test_config = test_config
        report.insert()
        # statistic = Statistic.query.filter_by(project_id=project_id).first()
        # setattr(statistic, 'performance_test_runs', Statistic.performance_test_runs + 1)
        # statistic.commit()
        self.module.context.rpc_manager.call.increment_statistics(project_id,
                                                                  'performance_test_runs')
        return report.to_json(), 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.edit"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def put(self, project_id: int):
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        connector = InfluxConnector(project_id=project_id, build_id=args["build_id"],
                                    test_name=args["test_name"],
                                    lg_type=args["lg_type"])
        test_data = connector.get_test_details()
        response_times = loads(args["response_times"])
        report = Report.query.filter(
            Report.project_id == project.id,
            Report.build_id == args["build_id"]
        ).first()
        report.end_time = test_data["end_time"]
        report.start_time = test_data["start_time"]
        report.failures = test_data["failures"]
        report.total = test_data["total"]
        report.thresholds_missed = args.get("missed", 0)
        report.throughput = test_data["throughput"]
        report.pct50 = response_times["pct50"]
        report.pct75 = response_times["pct75"]
        report.pct90 = response_times["pct90"]
        report.pct95 = response_times["pct95"]
        report.pct99 = response_times["pct99"]
        report._max = response_times["max"]
        report._min = response_times["min"]
        report.mean = response_times["mean"]
        report.onexx = test_data["1xx"]
        report.twoxx = test_data["2xx"]
        report.threexx = test_data["3xx"]
        report.fourxx = test_data["4xx"]
        report.fivexx = test_data["5xx"]
        report.requests = test_data["requests"]
        report.test_status = args["test_status"]
        report.vusers = args["vusers"]
        report.duration = args["duration"]
        report.commit()
        # if report.test_status['status'].lower() in ['finished', 'error', 'failed', 'success']:
        #     write_test_run_logs_to_minio_bucket(report, project)
        return {"message": f"Report {report.build_id} updated"}, 201

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.delete"],
        "recommended_roles": {
            "default": {"admin": True, "editor": False, "viewer": False},
            "administration": {"admin": True, "editor": False, "viewer": False},
        }
    })
    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400
        # query only needed fields
        query_result = Report.query.with_entities(
            Report.build_id, Report.name, Report.lg_type, Report.test_config
        ).filter(
            and_(Report.project_id == project.id, Report.id.in_(delete_ids))
        ).all()

        minio_delete_build_ids = dict()
        for build_id, name, lg_type, test_config in query_result:
            # delete influx tables
            try:
                InfluxConnector(build_id=build_id, test_name=name, lg_type=lg_type).delete_test_data()
            except InfluxDBClientError as e:
                log.warning('InfluxDBClientError %s', e)

            # collect s3 data for deletion
            s3_settings = test_config.get(
                'integrations', {}).get('system', {}).get('s3_integration', {'integration_id': 1})
            if s3_settings:
                try:
                    minio_delete_build_ids[s3_settings['integration_id']]['names'][name].add(build_id)
                except KeyError:
                    minio_delete_build_ids[s3_settings['integration_id']] = {
                        'settings': s3_settings,
                        'names': defaultdict(set)
                    }
                    minio_delete_build_ids[s3_settings['integration_id']]['names'][name].add(build_id)

        log.info('DEELEETE  %s', minio_delete_build_ids)
        # delete files from s3
        tmp = []
        for i in minio_delete_build_ids.values():
            minio_client = MinioClient(project, **i['settings'])
            for test_name, build_ids in i['names'].items():
                bucket_name = str(test_name).replace("_", "").replace(" ", "").lower()
                patt = re.compile(r'|'.join(build_ids))
                minio_files = minio_client.list_files(bucket_name)
                files_to_delete = [
                    {'Key': f['name']}
                    for f in minio_files
                    if re.search(patt, f['name'])
                ]
                tmp.append(dict(
                    Bucket=minio_client.format_bucket_name(bucket_name),
                    Delete={'Objects': files_to_delete},
                ))
                minio_client.s3_client.delete_objects(
                    Bucket=minio_client.format_bucket_name(bucket_name),
                    Delete={'Objects': files_to_delete},
                )
        log.info('DELETE REPORT %s', tmp)

        # delete baselines
        Baseline.query.filter(
            Baseline.project_id == project.id,
            Baseline.report_id.in_(delete_ids)
        ).delete()
        Baseline.commit()

        # delete reports
        Report.query.filter(
            Report.project_id == project.id,
            Report.id.in_(delete_ids)
        ).delete()
        Report.commit()

        return None, 204

    def patch(self, project_id: int):
        # used as dump logs flag in control tower
        report = Report.query.filter(
            Report.project_id == project_id,
            Report.build_id == request.json["build_id"]
        ).first()
        created_file_name = write_test_run_logs_to_minio_bucket(report)
        if created_file_name:
            return {"message": "updated", "file_name": created_file_name}, 201
        return {"message": "Saving logs failed", "file_name": None}, 400


def write_test_run_logs_to_minio_bucket(report: Report) -> str:
    build_id = report.build_id
    report_id = report.id
    test_name = report.name
    logs_query = "{" + f'build_id="{build_id}"' + "}"

    enc = 'utf-8'
    file_output = BytesIO()
    file_output.write(f'Test {test_name} (id={report_id}) run log:\n'.encode(enc))

    llf = LokiLogFetcher.from_project(report.project_id)
    try:
        llf.fetch_logs(query=logs_query)
        llf.to_file(file_output, enc=enc)
        s3_settings = report.test_config.get(
            'integrations', {}).get('system', {}).get('s3_integration', {})
        minio_client = MinioClient.from_project_id(report.project_id, **s3_settings)
        bucket_name = str(test_name).replace("_", "").replace(" ", "").lower()
        if bucket_name not in minio_client.list_bucket():
            minio_client.create_bucket(bucket=bucket_name, bucket_type='autogenerated')
        file_name = f"{build_id}.log"
        minio_client.upload_file(bucket_name, file_output, file_name)
        return file_name
    except:
        log.warning('Request to loki failed with error %s', format_exc())
