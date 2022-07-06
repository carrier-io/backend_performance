import json

from pylon.core.tools import log
from sqlalchemy import and_
from uuid import uuid4
from json import loads

from flask_restful import Resource
from flask import request, make_response

from tools import api_tools
from ...models.api_tests import PerformanceApiTest
from ...utils.utils import compile_tests, run_test


class API(Resource):

    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        reports = []
        total, res = api_tools.get(project_id, request.args, PerformanceApiTest)
        for each in res:
            reports.append(each.to_json(["influx.port", "influx.host", "galloper_url",
                                         "influx.db", "comparison_db", "telegraf_db",
                                         "loki_host", "loki_port", "influx.username", "influx.password"]))
        return make_response(
            {"total": total, "rows": reports},
            200
        )

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)

        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return make_response('IDs must be integers', 400)

        query_result = PerformanceApiTest.query.filter(
            and_(PerformanceApiTest.project_id == project.id, PerformanceApiTest.id.in_(delete_ids))
        ).all()
        for each in query_result:
            each.delete()
        return make_response({'ids': delete_ids}, 200)

    # def post(self, project_id: int):
    #     """
    #     Post method for creating and running test
    #     """
    #
    #     run_test_ = request.json.pop('run_test', False)
    #     test_data, errors = parse_test_data(
    #         project_id=project_id,
    #         request_data=request.json,
    #         rpc=self.module.context.rpc_manager,
    #     )
    #
    #     if errors:
    #         return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)
    #
    #     # log.warning('TEST DATA')
    #     # log.warning(test_data)
    #
    #     schedules = test_data.pop('scheduling', [])
    #     # log.warning('schedules')
    #     # log.warning(schedules)
    #
    #     test = SecurityTestsDAST(**test_data)
    #     test.insert()
    #
    #     # for s in schedules:
    #     #     log.warning('!!!adding schedule')
    #     #     log.warning(s)
    #     #     test.add_schedule(s, commit_immediately=False)
    #     # test.commit()
    #     test.handle_change_schedules(schedules)
    #
    #     threshold = SecurityThresholds(
    #         project_id=test.project_id,
    #         test_name=test.name,
    #         test_uid=test.test_uid,
    #         critical=-1,
    #         high=-1,
    #         medium=-1,
    #         low=-1,
    #         info=-1,
    #         critical_life=-1,
    #         high_life=-1,
    #         medium_life=-1,
    #         low_life=-1,
    #         info_life=-1
    #     )
    #     threshold.insert()
    #
    #     if run_test_:
    #         resp = run_test(test)
    #         return resp, resp.get('code', 200)
    #     return test.to_json()
    def post(self, project_id: int):
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
        )

        if errors:
            return json.dumps(errors, default=lambda o: o.dict()), 400

        log.warning('TEST DATA %s', test_data)

        schedules = test_data.pop('scheduling', [])
        log.warning('schedules %s', schedules)

        test = PerformanceApiTest(**test_data)
        test.insert()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)
        return test.to_json()


        # project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        # from pylon.core.tools import log
        # args = request.form
        # log.info("******************************************")
        # log.info(args)
        # log.info("******************************************")


        ### SOURCES ###
        # if args.get("git"):
        #     file_name = ""
        #     bucket = ""
        #     git_settings = loads(args["git"])
        # else:
        #     git_settings = {}
        #     file_name = args["file"].filename
        #     bucket = "tests"
        #     api_tools.upload_file(bucket, args["file"], project, create_if_not_exists=True)


        ### COMPILE TESTS ###
        # if args["compile"] and args["runner"] in ["v3.1", "v2.3"]:
        #     compile_tests(project.id, file_name, args["runner"])

        # test = ApiTests(project_id=project.id,
        #                 test_uid=str(uuid4()),
        #                 name=args["name"],
        #                 parallel=args["parallel"],
        #                 region=args["region"],
        #                 bucket=bucket,
        #                 file=file_name,
        #                 git=git_settings,
        #                 local_path='',
        #                 entrypoint=args["entrypoint"],
        #                 runner=args["runner"],
        #                 reporting=loads(args["reporting"]),
        #                 params=loads(args["params"]),
        #                 env_vars=loads(args["env_vars"]),
        #                 customization=loads(args["customization"]),
        #                 cc_env_vars=loads(args["cc_env_vars"]))
        # test.insert()
        # return test.to_json(exclude_fields=("id",))
