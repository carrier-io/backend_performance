from json import loads
from sqlalchemy import and_
from copy import deepcopy
from typing import Union

from flask import request, make_response
from flask_restful import Resource

from tools import api_tools
from ...models.api_tests import ApiTests
from ...models.api_reports import APIReport
from ...utils.utils import exec_test, get_backend_test_data


class API(Resource):
    url_params = [
        '<int:project_id>/<int:test_id>',
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, test_id: Union[int, str]):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        test = ApiTests.query.filter(_filter).first()
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
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        task = ApiTests.query.filter(_filter).first()

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

    def post(self, project_id, test_id):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        task = ApiTests.query.filter(_filter).first()
        event = list()
        execution = True if request.json['type'] and request.json["type"] == "config" else False
        event.append(task.configure_execution_json(output='cc',
                                                   test_type=request.json.get("test_type"),
                                                   params=loads(request.json.get("params", None)),
                                                   env_vars=loads(request.json.get("env_vars", None)),
                                                   reporting=request.json.get("reporter", None),
                                                   customization=loads(request.json.get("customization", None)),
                                                   cc_env_vars=loads(request.json.get("cc_env_vars", None)),
                                                   parallel=request.json.get("parallel", None),
                                                   region=request.json.get("region", "default"),
                                                   execution=execution, emails=request.json.get("emails", None)))
        if request.json['type'] and request.json["type"] == "config":
            return event[0]
        for each in event:
            each["test_id"] = task.test_uid

        test_data = get_backend_test_data(event[0])
        report = APIReport(name=test_data["test_name"],
                           project_id=project.id,
                           environment=test_data["environment"],
                           type=test_data["type"],
                           end_time="",
                           start_time=test_data["start_time"],
                           failures=0,
                           total=0,
                           thresholds_missed=0,
                           throughput=0,
                           vusers=test_data["vusers"],
                           pct50=0,
                           pct75=0,
                           pct90=0,
                           pct95=0,
                           pct99=0,
                           _max=0,
                           _min=0,
                           mean=0,
                           duration=test_data["duration"],
                           build_id=test_data["build_id"],
                           lg_type=test_data["lg_type"],
                           onexx=0,
                           twoxx=0,
                           threexx=0,
                           fourxx=0,
                           fivexx=0,
                           requests="",
                           test_uid=task.test_uid)
        report.insert()
        event[0]["cc_env_vars"]["REPORT_ID"] = str(report.id)
        event[0]["cc_env_vars"]["build_id"] = test_data["build_id"]
        response = exec_test(project.id, event)
        response["redirect"] = f'/task/{response["task_id"]}/results'
        return response
