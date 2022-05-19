from sqlalchemy import and_
from uuid import uuid4
from json import loads

from flask_restful import Resource
from flask import request, make_response

from tools import api_tools
from ...models.api_tests import ApiTests
from ...utils.utils import compile_tests


class API(Resource):

    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        reports = []
        total, res = api_tools.get(project_id, request.args, ApiTests)
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

        query_result = ApiTests.query.filter(
            and_(ApiTests.project_id == project.id, ApiTests.id.in_(delete_ids))
        ).all()
        for each in query_result:
            each.delete()
        return make_response({'ids': delete_ids}, 200)

    def post(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        from pylon.core.tools import log
        args = request.form
        log.info("******************************************")
        log.info(args)
        log.info("******************************************")

        if args.get("git"):
            file_name = ""
            bucket = ""
            git_settings = loads(args["git"])
        else:
            git_settings = {}
            file_name = args["file"].filename
            bucket = "tests"
            api_tools.upload_file(bucket, args["file"], project, create_if_not_exists=True)
        if args["compile"] and args["runner"] in ["v3.1", "v2.3"]:
            compile_tests(project.id, file_name, args["runner"])

        test = ApiTests(project_id=project.id,
                        test_uid=str(uuid4()),
                        name=args["name"],
                        parallel=args["parallel"],
                        region=args["region"],
                        bucket=bucket,
                        file=file_name,
                        git=git_settings,
                        local_path='',
                        entrypoint=args["entrypoint"],
                        runner=args["runner"],
                        reporting=loads(args["reporting"]),
                        params=loads(args["params"]),
                        env_vars=loads(args["env_vars"]),
                        customization=loads(args["customization"]),
                        cc_env_vars=loads(args["cc_env_vars"]))
        test.insert()
        return test.to_json(exclude_fields=("id",))
