from json import loads
from copy import deepcopy
from typing import Union

from flask import request
from flask_restful import Resource

from ...models.api_tests import PerformanceApiTest
from ...utils.utils import run_test


class API(Resource):
    url_params = [
        '<int:project_id>/<int:test_id>',
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, test_id: Union[int, str]):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        test = PerformanceApiTest.query.filter(
            PerformanceApiTest.get_api_filter(project_id, test_id)
        ).first()
        if request.args["raw"]:
            return test.to_json(["influx.port", "influx.host", "galloper_url",
                                 "influx.db", "comparison_db", "telegraf_db",
                                 "loki_host", "loki_port", "influx.username", "influx.password"])
        if request.args["type"] == "docker":
            message = test.configure_execution_json(request.args.get("type"), execution=request.args.get("exec"))
        else:
            message = [{"test_id": test.test_uid}]
        return {"config": message}  # this is cc format

    def put(self, project_id: int, test_id: Union[int, str]):
        default_params = ["influx.port", "influx.host", "galloper_url", "influx.db", "comparison_db", "telegraf_db",
                          "loki_host", "loki_port", "test.type", "test_type", "influx.username", "influx.password"]
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        task = PerformanceApiTest.query.filter(
            PerformanceApiTest.get_api_filter(project_id, test_id)
        ).first()

        params = deepcopy(getattr(task, "params"))
        new_params = loads(request.json.get("params"))
        param_names = [each["name"] for each in params]
        for param in new_params:
            if param["name"] not in param_names:
                params.append(param)
        new_param_names = [each["name"] for each in new_params]
        params = [param for param in params if (param["name"] in new_param_names or param["name"] in default_params)]
        for param in params:
            for _param in new_params:
                if param["name"] == _param["name"]:
                    param["default"] = _param["default"]
                    param["description"] = _param["description"]
        setattr(task, "params", params)
        for each in ["env_vars", "customization", "cc_env_vars"]:
            params = deepcopy(getattr(task, each))
            for key in list(params.keys()):
                if key not in loads(request.json.get(each)).keys() and key not in default_params:
                    del params[key]
            for key, value in loads(request.json.get(each)).items():
                if key not in params or params[key] != value:
                    params[key] = value
            setattr(task, each, params)

        if request.json.get("reporter"):
            task.reporting = request.json["reporter"]
        else:
            task.reporting = []

        if request.json.get("emails"):
            task.emails = request.json["emails"]
        else:
            task.emails = ""

        if request.json.get("parallel"):
            task.parallel = request.json.get("parallel")
        if request.json.get("region"):
            task.region = request.json.get("region")
        if request.json.get("git"):
            task.git = loads(request.json.get("git"))
        task.commit()
        return task.to_json(["influx.port", "influx.host", "galloper_url",
                             "influx.db", "comparison_db", "telegraf_db",
                             "loki_host", "loki_port", "influx.username", "influx.password"])


    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = PerformanceApiTest.query.filter(
            PerformanceApiTest.get_api_filter(project_id, test_id)
        ).first()
        resp = run_test(test, config_only=request.json.get('type', False))
        return resp, resp.get('code', 200)

    # def post(self, project_id, test_id):
        # project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        # if isinstance(test_id, int):
        #     _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        # else:
        #     _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        # task = ApiTests.query.filter(_filter).first()




