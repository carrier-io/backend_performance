from flask import request
from flask_restful import Resource
from pylon.core.tools import log
from tools import auth
from ...models.reports import Report


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["performance.backend.thresholds.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def get(self, project_id: int):
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        requests_data = set()
        query_result = Report.query.with_entities(Report.requests).filter(
            Report.name == args.get('name'),
            Report.environment == args.get('environment'),
            Report.project_id == project.id
        ).all()
        for i in query_result:
            requests_data.update(set(i[0]))
        try:
            requests_data.remove('All')
        except KeyError:
            ...
        return list(requests_data), 200
