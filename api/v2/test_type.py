from sqlalchemy import and_

from flask_restful import Resource

from ....security.models.tests import SecurityTestsDAST
from ...models.api_tests import ApiTests


class API(Resource):
    url_params = [
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id, test_uuid):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        job_type = "not_found"
        # check if APIPerformanceTests
        _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_uuid)
        test = ApiTests.query.filter(_filter).first()
        if test:
            job_type = test.job_type

        # _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.test_uid == test_uuid)
        # test = UIPerformanceTests.query.filter(_filter).first()
        # if test:
        #     job_type = test.job_type

        _filter = and_(
            SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_uuid
        )
        test = SecurityTestsDAST.query.filter(_filter).first()
        if test:
            job_type = "dast"

        # _filter = and_(
        #     SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_uuid
        # )
        # test = SecurityTestsSAST.query.filter(_filter).first()
        # if test:
        #     job_type = "sast"

        return {"job_type": job_type}
