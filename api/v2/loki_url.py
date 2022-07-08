import json
import gzip
from ...models.api_reports import APIReport
import flask
from flask import make_response
from flask_restful import Resource
from pylon.core.tools import log
from pylon.core.seeds.minio import MinIOHelper


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):

        report_id = flask.request.args.get("report_id", None)

        if not report_id:
            return make_response({"message": ""}, 404)

        build_id = APIReport.query.get_or_404(report_id).to_json()["build_id"]

        websocket_base_url = self.module.context.settings['loki']['url']
        websocket_base_url = websocket_base_url.replace("http://", "ws://")
        websocket_base_url = websocket_base_url.replace("api/v1/push", "api/v1/tail")

        logs_query = "{" + f'report_id="{report_id}",project="{project_id}",build_id="{build_id}"' + "}"

        logs_start = 0
        logs_limit = 10000000000

        return make_response(
            {"websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"},
            200
        )
