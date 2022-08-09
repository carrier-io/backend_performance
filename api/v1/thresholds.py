from sqlalchemy import and_
from flask import request
from flask_restful import Resource

from ...models.api_thresholds import APIThresholds

from tools import api_tools
from pydantic import ValidationError
from ...models.pd.thresholds import ThresholdPD


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        if request.args.get("test") and request.args.get("env"):
            res = APIThresholds.query.filter(and_(
                APIThresholds.project_id == project.id,
                APIThresholds.test == request.args.get("test"),
                APIThresholds.environment == request.args.get("env")
            )).all()
            return [th.to_json() for th in res], 200
        total, res = api_tools.get(project_id, request.args, APIThresholds)
        return {'total': total, 'rows': [i.to_json() for i in res]}, 200

    def post(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            pd_obj = ThresholdPD(project_id=project_id, **request.json)
        except ValidationError as e:
            return e.errors(), 400
        th = APIThresholds(**pd_obj.dict()).insert()
        # APIThresholds(project_id=project.id,
        #               test=args["test"],
        #               scope=args["scope"],
        #               environment=args["env"],
        #               target=args["target"],
        #               value=args["value"],
        #               aggregation=args["aggregation"],
        #               comparison=args["comparison"]).insert()
        return th.to_json(), 201

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400

        filter_ = and_(
            APIThresholds.project_id == project.id,
            APIThresholds.id.in_(delete_ids)
        )
        APIThresholds.query.filter(
            filter_
        ).delete()
        APIThresholds.commit()
        return {'ids': delete_ids}, 204
