from queue import Empty
from typing import Union

from flask import request
from flask_restful import Resource

from ...models.api_tests import PerformanceApiTest
from ...models.pd.performance_test import PerformanceTestParam
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
            test = test.to_json((
                "influx.port", "influx.host", "galloper_url",
                "influx.db", "comparison_db", "telegraf_db",
                "loki_host", "loki_port", "influx.username", "influx.password"
            ))
            # test = test.to_json()
            schedules = test.pop('schedules', [])
            if schedules:
                try:
                    test['scheduling'] = self.module.context.rpc_manager.timeout(
                        2).scheduling_backend_performance_load_from_db_by_ids(schedules)
                except Empty:
                    test['scheduling'] = []
            return test
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

        test_type = test_data.pop('test_type')
        env_type = test_data.pop('env_type')

        test_data['test_parameters'].append(
            PerformanceTestParam(
                name="test_name",
                default=test_data['name']
            ).dict()
        )
        test_data['test_parameters'].append(
            PerformanceTestParam(
                name="test_type",
                default=test_type
            ).dict()
        )
        test_data['test_parameters'].append(
            PerformanceTestParam(
                name="env_type",
                default=env_type
            ).dict()
        )
        # test_params_list = [i.get('name') for i in test_data['test_parameters']]
        # from ...constants import JOB_CONTAINER_MAPPING
        # if "influx.db" not in test_params_list:
        #     test_data['test_parameters'].append(
        #         PerformanceTestParam(
        #             name="influx.db",
        #             default=JOB_CONTAINER_MAPPING.get(test_data['runner'], {}).get('influx_db')
        #         ).dict()
        #     )

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

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test with possible overridden params
        """

        config_only_flag = request.json.pop('type', False)
        execution_flag = request.json.pop('execution', True)
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

        test = PerformanceApiTest.query.filter(
            PerformanceApiTest.get_api_filter(project_id, test_id)
        ).first()

        # rewrite test params, not merge
        # test_params_overridden = PerformanceTestParams(test_parameters=test_data.pop('test_parameters', []))
        # test_params_existing = PerformanceTestParams.from_orm(test)
        # test_params_existing.update(test_params_overridden)
        # test_data.update(test_params_existing.dict())

        test.__dict__.update(test_data)
        # return {
        #    'test': test.to_json(),
        #    'config': run_test(test, config_only=True, execution=execution_flag)
        # }, 200
        resp = run_test(test, config_only=config_only_flag, execution=execution_flag)
        return resp, resp.get('code', 200)
