from json import loads

from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.api_reports import APIReport


class ReportStatusAPI(RestResource):
    put_rules = (
        dict(name="test_status", type=dict, location="json"),
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_put = build_req_parser(rules=self.put_rules)

    def get(self, project_id: int, report_id: int):
        project = self.rpc.project_get_or_404(project_id=project_id)
        report = APIReport.query.filter_by(project_id=project.id, id=report_id).first().to_json()
        return {"message": report["test_status"]["status"]}

    def put(self, project_id: int, report_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = self.rpc.project_get_or_404(project_id=project_id)
        report = APIReport.query.filter_by(project_id=project.id, id=report_id).first()
        print("*****************************************")
        print(args["test_status"])
        print("*****************************************")
        test_status = args["test_status"]
        report.test_status = test_status
        report.commit()
        return {"message": f"status changed to {report.test_status['status']}"}
