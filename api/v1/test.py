from queue import Empty
from typing import Union

from flask import request
from flask_restful import Resource
from pylon.core.tools import log

from tools import auth
from ...models.tests import Test
from ...models.pd.test_parameters import PerformanceTestParam, PerformanceTestParams
from ...utils.utils import run_test, parse_test_data, handle_artifact_source


class API(Resource):
    url_params = [
        '<int:project_id>/<int:test_id>',
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
            "administration": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int, test_id: Union[int, str]):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        test = Test.query.filter(
            Test.get_api_filter(project_id, test_id)
        ).first()
        output = request.args.get('output')

        if output == 'docker':
            return {'cmd': test.docker_command}, 200

        if output == 'test_uid' or output == 'uid':
            return {"config": [{"test_id": test.uid}]}, 200  # format is ok?

        test = test.api_json()
        schedules = test.pop('schedules', [])
        if schedules:
            try:
                test['scheduling'] = self.module.context.rpc_manager.timeout(
                    2).scheduling_backend_performance_load_from_db_by_ids(schedules)
            except Empty:
                test['scheduling'] = []
        return test

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.edit"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def put(self, project_id: int, test_id: Union[int, str]):
        """ Update test data and run on demand """
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        compile_tests_flag = request.json.pop('compile_tests', False)
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={'exclude': {'uid', }}
        )

        if errors:
            return errors, 400

        if test_data['source']['name'] == 'artifact':
            if request.files.get('file'):
                handle_artifact_source(project, request.files['file'],
                                       compile_tests_flag=compile_tests_flag,
                                       runner=test_data["runner"])
            else:
                log.warning('TODO: check if file exists in artifacts %s', test_data.get('source'))

        test_data['test_parameters'].append(
            PerformanceTestParam(
                name="test_type",
                default=test_data.pop('test_type'),
                description='auto-generated from test type'
            ).dict()
        )
        test_data['test_parameters'].append(
            PerformanceTestParam(
                name="env_type",
                default=test_data.pop('env_type'),
                description='auto-generated from environment'
            ).dict()
        )

        test_query = Test.query.filter(Test.get_api_filter(project_id, test_id))

        schedules = test_data.pop('scheduling', [])

        test_query.update(test_data)
        Test.commit()
        test = test_query.one()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)

        return test.api_json(), 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test with possible overridden params """
        config_only_flag = request.json.pop('type', False)
        execution_flag = request.json.pop('execution', True)
        engagement_id = request.json.get('integrations', {}).get('reporters', {}) \
            .get('reporter_engagement', {}).get('id')

        purpose = 'run'
        if 'params' in request.json:
            purpose = 'control_tower'
            request.json['test_parameters'] = request.json.pop('params')

        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={
                'overrideable_only': True,
                'exclude_defaults': True,
                'exclude_unset': True,
            },
            test_create_rpc_kwargs={
                'purpose': purpose
            }
        )

        if errors:
            return errors, 400

        test = Test.query.filter(
            Test.get_api_filter(project_id, test_id)
        ).first()

        if purpose == 'control_tower':
            merged_test_parameters = test.all_test_parameters
            merged_test_parameters.update(PerformanceTestParams(
                test_parameters=test_data.pop('test_parameters')
            ))
            test_data['test_parameters'] = merged_test_parameters.dict()['test_parameters']

        test.__dict__.update(test_data)

        if config_only_flag == '_test':
            return {
                'test': test.to_json(),
                'config': run_test(test, config_only=True, execution=execution_flag),
                'api_json': test.api_json(),
            }, 200
        resp = run_test(test, config_only=config_only_flag, execution=execution_flag,
                        engagement_id=engagement_id)
        return resp, resp.get('code', 200)
