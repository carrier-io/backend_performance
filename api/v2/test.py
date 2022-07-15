from json import loads
from copy import deepcopy
from typing import Union

from flask import request
from flask_restful import Resource

from ...models.api_tests import PerformanceApiTest
from ...models.pd.performance_test import PerformanceTestParams
from ...utils.utils import run_test, parse_test_data


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
        if request.args.get("raw"):
            return test.to_json((
                "influx.port", "influx.host", "galloper_url",
                "influx.db", "comparison_db", "telegraf_db",
                "loki_host", "loki_port", "influx.username", "influx.password"
            ))
        if request.args.get("type") == "docker":
            message = test.configure_execution_json('docker', execution=request.args.get("exec", False))
        else:
            message = [{"test_id": test.test_uid}]
        return {"config": message}  # this is cc format

    def put(self, project_id: int, test_id: Union[int, str]):
        """ Update test data and run on demand """
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={'exclude': {'test_uid', }}
        )

        if errors:
            return errors, 400

        test_query = PerformanceApiTest.query.filter(PerformanceApiTest.get_api_filter(project_id, test_id))

        schedules = test_data.pop('scheduling', [])

        test_query.update(test_data)
        PerformanceApiTest.commit()
        test = test_query.one()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)

        return test.to_json(("influx.port", "influx.host", "galloper_url",
                             "influx.db", "comparison_db", "telegraf_db",
                             "loki_host", "loki_port", "influx.username", "influx.password")), 200

        default_params = ["influx.port", "influx.host", "galloper_url", "influx.db", "comparison_db", "telegraf_db",
                          "loki_host", "loki_port", "test.type", "test_type", "influx.username", "influx.password"]
        # test = PerformanceApiTest.query.filter(
        #     PerformanceApiTest.get_api_filter(project_id, test_id)
        # ).first()

        # update params:
        # params = deepcopy(getattr(test, "params"))
        # new_params = loads(request.json.get("params"))
        # param_names = [each["name"] for each in params]
        # for param in new_params:
        #     if param["name"] not in param_names:
        #         params.append(param)
        # new_param_names = [each["name"] for each in new_params]
        # params = [param for param in params if (param["name"] in new_param_names or param["name"] in default_params)]
        # for param in params:
        #     for _param in new_params:
        #         if param["name"] == _param["name"]:
        #             param["default"] = _param["default"]
        #             param["description"] = _param["description"]
        # setattr(test, "params", params)

        for each in ["env_vars", "customization", "cc_env_vars"]:
            params = deepcopy(getattr(test, each))
            for key in list(params.keys()):
                if key not in loads(request.json.get(each)).keys() and key not in default_params:
                    del params[key]
            for key, value in loads(request.json.get(each)).items():
                if key not in params or params[key] != value:
                    params[key] = value
            setattr(test, each, params)

        # if request.json.get("reporter"):
        #     test.reporting = request.json["reporter"]
        # else:
        #     test.reporting = []

        # if request.json.get("emails"):
        #     test.emails = request.json["emails"]
        # else:
        #     test.emails = ""

        if request.json.get("parallel"):
            test.parallel = request.json.get("parallel")
        if request.json.get("region"):
            test.region = request.json.get("region")
        # if request.json.get("git"):
        #     test.git = loads(request.json.get("git"))
        test.commit()
        return test.to_json(["influx.port", "influx.host", "galloper_url",
                             "influx.db", "comparison_db", "telegraf_db",
                             "loki_host", "loki_port", "influx.username", "influx.password"])

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test with possible overridden params
            {
        """

        config_only_flag = request.json.pop('type', False)
        execution_flag = request.json.pop('execution', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={
                'overrideable_only': True,
                'exclude_defaults': True,
                'exclude_unset': True,
            },
        )

        if errors:
            return errors, 400

        # from pylon.core.tools import log
        # log.info('Test_data %s', test_data)

        test = PerformanceApiTest.query.filter(
            PerformanceApiTest.get_api_filter(project_id, test_id)
        ).first()
        test_params_overridden = PerformanceTestParams(test_parameters=test_data.pop('test_parameters', []))
        # log.info('test_params_overridden %s', test_params_overridden.dict())
        test_params_existing = PerformanceTestParams.from_orm(test)
        # log.info('test_params_existing %s', test_params_existing.dict())
        test_params_existing.update(test_params_overridden)
        # log.info('test_params_ updated %s', test_params_existing.dict())
        test_data.update(test_params_existing.dict())
        # log.info('test_data updated %s', test_data)
        test.__dict__.update(test_data)
        return {
                   'test': test.to_json(),
                   'config': run_test(test, config_only=True, execution=execution_flag)
               }, 200
        resp = run_test(test, config_only=config_only_flag, execution=execution_flag)
        return resp, resp.get('code', 200)

    # def post(self, project_id, test_id):
    # project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
    # if isinstance(test_id, int):
    #     _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
    # else:
    #     _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
    # task = ApiTests.query.filter(_filter).first()
