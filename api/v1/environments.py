from flask import request, make_response
from flask_restful import Resource
from ...models.api_reports import APIReport
from sqlalchemy import and_


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = APIReport.query.with_entities(APIReport.environment).filter(
            and_(
                APIReport.name == request.args.get("name"),
                APIReport.project_id == project.id
            )
        ).distinct(APIReport.environment).all()
        return [i[0] for i in query_result], 200
