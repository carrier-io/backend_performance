from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.api_baseline import APIBaseline
from ..models.api_reports import APIReport
from ..connectors.influx import get_aggregated_test_results


class BaselineAPI(RestResource):
    get_rules = (
        dict(name="test_name", type=str, location="args"),
        dict(name="env", type=str, location="args")
    )
    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="build_id", type=str, location="json"),
        dict(name="env", type=str, location="json")
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = self.rpc.project_get_or_404(project_id=project_id)
        baseline = APIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                               environment=args.get("env")).first()
        test = baseline.summary if baseline else []
        report_id = baseline.report_id if baseline else 0
        return {"baseline": test, "report_id": report_id}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = self.rpc.project_get_or_404(project_id=project_id)
        report_id = APIReport.query.filter_by(project_id=project_id, name=args['test_name'],
                                              build_id=args['build_id']).first().to_json()['id']
        baseline = APIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                               environment=args.get("env")).first()
        if baseline:
            baseline.delete()
        test = get_aggregated_test_results(args['test_name'], args['build_id'])
        summary = []
        for req in test[0]:
            summary.append(req)
        baseline = APIBaseline(test=args["test_name"],
                               environment=args["env"],
                               project_id=project.id,
                               report_id=report_id,
                               summary=summary)
        baseline.insert()
        return {"message": "baseline is set"}