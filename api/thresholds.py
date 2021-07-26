from sqlalchemy import and_

from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.api_thresholds import APIThresholds


class BackendThresholdsAPI(RestResource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="environment", type=str, location="args")
    )
    delete_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="test", type=str, location=("args", "json")),
        dict(name="scope", type=str, location=("args", "json")),
        dict(name="target", type=str, location=("args", "json")),
        dict(name="aggregation", type=str, location=("args", "json")),
        dict(name="comparison", type=str, location=("args", "json")),
        dict(name="env", type=str, location=("args", "json"))
    )
    post_rules = delete_rules + (
        dict(name="yellow", type=float, location="json"),
        dict(name="red", type=float, location="json")
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id: int):
        project = self.rpc.project_get_or_404(project_id=project_id)
        args = self._parser_get.parse_args(strict=False)
        res = APIThresholds.query.filter().filter(
            and_(APIThresholds.project_id == project.id,
                 APIThresholds.test == args.get("name"),
                 APIThresholds.environment == args.get("environment"))).all()
        return [th.to_json() for th in res]

    def post(self, project_id: int):
        project = self.rpc.project_get_or_404(project_id=project_id)
        args = self._parser_post.parse_args(strict=False)
        APIThresholds(project_id=project.id,
                      test=args["test"],
                      scope=args["scope"],
                      environment=args["env"],
                      target=args["target"],
                      yellow=args["yellow"],
                      red=args["red"],
                      aggregation=args["aggregation"],
                      comparison=args["comparison"]).insert()
        return {"message": "OK"}

    def delete(self, project_id: int):
        project = self.rpc.project_get_or_404(project_id=project_id)
        args = self._parser_delete.parse_args(strict=False)
        APIThresholds.query.filter().filter(
            and_(APIThresholds.project_id == project.id,
                 APIThresholds.test == args.get("test"),
                 APIThresholds.scope == args.get("scope"),
                 APIThresholds.target == args.get("target"),
                 APIThresholds.environment == args.get("env"),
                 APIThresholds.aggregation == args.get("aggregation"),
                 APIThresholds.comparison == args.get("comparison"))).first().delete()
        return {"message": "OK"}
