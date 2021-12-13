from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.api_reports import APIReport
from sqlalchemy import and_


class RequestsAPI(RestResource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="env", type=str, location="args"),
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
        requests_data = set()
        query_result = APIReport.query.filter(
            and_(APIReport.name == args.get("name"), APIReport.environment == args.get("env"),
                 APIReport.project_id == project.id)
        ).order_by(APIReport.id.asc()).all()
        for each in query_result:
            requests_data.update(set(each.requests.split(";")))
        if "All" in requests_data:
            requests_data.remove("All")
        return list(requests_data)
