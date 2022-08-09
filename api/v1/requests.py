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
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        requests_data = set()
        query_result = APIReport.query.with_entities(APIReport.requests).filter(
            and_(
                APIReport.name == args.get("name"),
                APIReport.environment == args.get("env"),
                APIReport.project_id == project.id
            )
        ).order_by(APIReport.id.asc()).all()
        for i in query_result:
            requests_data.update(set(i[0].split(";")))
        try:
            requests_data.remove('All')
        except KeyError:
            ...
        return list(requests_data), 200
