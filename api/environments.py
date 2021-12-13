from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.api_reports import APIReport
from sqlalchemy import and_


class EnvironmentsAPI(RestResource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="type", type=str, default="backend", location="args")
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = self.rpc.project_get_or_404(project_id=project_id)
        query_result = APIReport.query.with_entities(APIReport.environment).distinct().filter(
            and_(APIReport.name == args.get("name"),
                 APIReport.project_id == project.id)
        ).order_by(APIReport.id.asc()).all()
        return list(set([each.environment for each in query_result]))