import json
from queue import Empty

from sqlalchemy import and_

from flask_restful import Resource
from flask import request

from tools import api_tools, auth
from ...models.tests import Test
from ...models.pd.test_parameters import PerformanceTestParam
from ...utils.utils import run_test, parse_test_data, handle_artifact_source


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.view"],
    })
    def get(self, project_id: int):
        total, res = api_tools.get(project_id, request.args, Test)
        rows = []
        for i in res:
            test = i.api_json()
            schedules = test.pop('schedules', [])
            if schedules:
                try:
                    test['scheduling'] = self.module.context.rpc_manager.timeout(
                        2).scheduling_backend_performance_load_from_db_by_ids(schedules)
                except Empty:
                    test['scheduling'] = []
            rows.append(test)
        return {'total': total, 'rows': rows}, 200

    @staticmethod
    def get_schedules_ids(filter_) -> set:
        r = set()
        for i in Test.query.with_entities(Test.schedules).filter(
                filter_
        ).all():
            r.update(set(*i))
        return r

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.delete"],
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

        filter_ = and_(
            Test.project_id == project.id,
            Test.id.in_(delete_ids)
        )

        try:
            self.module.context.rpc_manager.timeout(3).scheduling_delete_schedules(
                self.get_schedules_ids(filter_)
            )
        except Empty:
            ...

        Test.query.filter(
            filter_
        ).delete()
        Test.commit()

        return {'ids': delete_ids}, 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int):
        """
        Create test and run on demand
        """
        data = json.loads(request.form.get('data'))
        run_test_ = data.pop('run_test', False)
        compile_tests_flag = data.pop('compile_tests', False)
        engagement_id = data.get('integrations', {}).get('reporters', {}) \
            .get('reporter_engagement', {}).get('id')

        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=data,
            rpc=self.module.context.rpc_manager,
        )

        if errors:
            return errors, 400

        schedules = test_data.pop('scheduling', [])

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

        if test_data['source']['name'] == 'artifact':
            project = self.module.context.rpc_manager.call.project_get_or_404(
                project_id=project_id)
            handle_artifact_source(project, request.files['file'],
                                   compile_tests_flag=compile_tests_flag,
                                   runner=test_data["runner"])

        test = Test(**test_data)
        test.insert()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test, engagement_id=engagement_id)
            return resp, resp.get('code', 200)
        return test.api_json(), 200
