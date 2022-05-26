from sqlalchemy import and_
from flask import request, make_response
from flask_restful import Resource
from ...models.api_thresholds import APIThresholds


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        args = request.args
        if args.get("test") and args.get("env"):
            res = APIThresholds.query.filter().filter(
                and_(APIThresholds.project_id == project.id,
                     APIThresholds.test == args.get("test"),
                     APIThresholds.environment == args.get("env"))).all()
        else:
            res = APIThresholds.query.filter().filter(APIThresholds.project_id == project.id).all()
        return [th.to_json() for th in res]

    def post(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        args = request.json
        APIThresholds(project_id=project.id,
                      test=args["test"],
                      scope=args["scope"],
                      environment=args["env"],
                      target=args["target"],
                      value=args["value"],
                      aggregation=args["aggregation"],
                      comparison=args["comparison"]).insert()
        return {"message": "OK"}

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        args = request.args
        APIThresholds.query.filter().filter(
            and_(APIThresholds.project_id == project.id,
                 APIThresholds.test == args.get("test"),
                 APIThresholds.scope == args.get("scope"),
                 APIThresholds.target == args.get("target"),
                 APIThresholds.environment == args.get("env"),
                 APIThresholds.aggregation == args.get("aggregation"),
                 APIThresholds.comparison == args.get("comparison"))).first().delete()
        return {"message": "OK"}
