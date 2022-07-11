import json
from queue import Empty

from pylon.core.tools import log
from sqlalchemy import and_

from flask_restful import Resource
from flask import request, make_response

from tools import api_tools
from ...models.api_tests import PerformanceApiTest
from ...utils.utils import run_test, parse_test_data


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        total, res = api_tools.get(project_id, request.args, PerformanceApiTest)
        rows = []
        for i in res:
            test = i.to_json((
                "influx.port", "influx.host", "galloper_url",
                 "influx.db", "comparison_db", "telegraf_db",
                 "loki_host", "loki_port", "influx.username", "influx.password"
            ))
            schedules = test.pop('schedules', [])
            if schedules:
                try:
                    test['scheduling'] = self.module.context.rpc_manager.timeout(
                        2).scheduling_performance_load_from_db_by_ids(schedules)
                except Empty:
                    ...
            rows.append(test)
        return {'total': total, 'rows': rows}, 200

    @staticmethod
    def get_schedules_ids(filter_) -> set:
        r = set()
        for i in PerformanceApiTest.query.with_entities(PerformanceApiTest.schedules).filter(
                filter_
        ).all():
            r.update(set(*i))
        return r

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400

        filter_ = and_(
            PerformanceApiTest.project_id == project.id,
            PerformanceApiTest.id.in_(delete_ids)
        )

        try:
            self.module.context.rpc_manager.timeout(3).scheduling_delete_schedules(
                self.get_schedules_ids(filter_)
            )
        except Empty:
            ...

        PerformanceApiTest.query.filter(
            filter_
        ).delete()
        PerformanceApiTest.commit()

        return {'ids': delete_ids}, 200

    def post(self, project_id: int):
        """
        Create test and run if indicated
        """
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
        )

        if errors:
            return errors, 400

        log.warning('TEST DATA %s', test_data)

        schedules = test_data.pop('scheduling', [])
        log.warning('schedules %s', schedules)

        test = PerformanceApiTest(**test_data)
        test.insert()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)
        return test.to_json(), 200
