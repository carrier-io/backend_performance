from flask import request, make_response
from flask_restful import Resource
from ...models.api_baseline import APIBaseline
from ...models.api_reports import APIReport
from ...connectors.influx import get_aggregated_test_results


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        baseline = APIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                               environment=args.get("env")).first()
        test = baseline.summary if baseline else []
        report_id = baseline.report_id if baseline else 0
        return {"baseline": test, "report_id": report_id}

    def post(self, project_id: int):
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
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