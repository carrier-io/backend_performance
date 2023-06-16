from functools import partial

from flask import request
from flask_restful import Resource

from pylon.core.tools import log
from tools import auth
from ...models.reports import Report
from ...connectors.minio_connector import MinioConnector
from ...connectors.influx_connector import InfluxConnector
from ...connectors.loki_connector import LokiConnector
from ...utils.charts_utils import requests_summary, requests_hits, avg_responses, \
    summary_table, get_data_for_analytics, get_issues, engine_health


class API(Resource):
    url_params = [
        '<string:source>/<string:target>',
    ]

    statuses = ('finished', 'error', 'failed', 'success')

    mapping = {
        "requests": {
            "summary": requests_summary,
            "hits": requests_hits,
            "average": avg_responses,
            "table": summary_table,
            "data": get_data_for_analytics
        },
        "errors": {
            "table": get_issues
        },
        "engine_health": {
            "cpu": partial(engine_health, part='cpu'),
            "memory": partial(engine_health, part='memory'),
            "load": partial(engine_health, part='load'),
            "all": engine_health,
        }
    }

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api(["performance.backend.reports.view"])
    def get(self, source: str, target: str):
        connector = None
        args = request.args.to_dict(flat=True)
        # args['source'] = 'minio'
        for i in request.args.keys():
            if i.endswith('[]'):
                args[i] = request.args.getlist(i)
        connector = self._get_connector(args, source)
        return self.mapping[source][target](connector)

    def _get_connector(self, args, source):
        report = Report.query.with_entities(Report.test_status, Report.test_config).filter(
            Report.build_id == args['build_id']
        ).first()
        test_status = report[0]['status'].lower()
        s3_config = {
            's3_config': report[1].get('integrations', {}).get('system', {}).get('s3_integration', {})
            }
        if test_status in self.statuses:
            args.update(s3_config)
            return MinioConnector(**args)
        else:
            if source == "errors":
                log.info('Using LokiConnector')
                return LokiConnector(**args)
            elif source == "engine_health":
                project_id = Report.query.with_entities(Report.project_id).filter(
                    Report.build_id == args['build_id']
                ).first()[0]
                args['db_name'] = f'telegraf_{project_id}'
                log.info(f'Using InfluxConnector with DB telegraf_{project_id}')
                return InfluxConnector(**args)
            else:
                log.info('Using InfluxConnector')
                return InfluxConnector(**args)
