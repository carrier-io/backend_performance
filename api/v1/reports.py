from sqlalchemy import and_
from json import loads

from flask import request, make_response
from flask_restful import Resource

from ....projects.models.statistics import Statistic
from ...models.api_baseline import APIBaseline
from ...models.api_reports import APIReport
from ...utils.utils import get
from ...connectors.influx import get_test_details, delete_test_data


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        if args.get("report_id"):
            report = APIReport.query.filter_by(project_id=project_id, id=args.get("report_id")).first().to_json()
            return report
        reports = []
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        total, res = get(project, args, APIReport)
        for each in res:
            each_json = each.to_json()
            each_json["start_time"] = each_json["start_time"].replace("T", " ").split(".")[0]
            each_json["duration"] = int(each_json["duration"] if each_json["duration"] else 0)
            try:
                each_json["failure_rate"] = round((each_json["failures"] / each_json["total"]) * 100, 2)
            except ZeroDivisionError:
                each_json["failure_rate"] = 0
            reports.append(each_json)
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)

        # TODO: we need to check api performance tests quota here
        # if not ProjectQuota.check_quota(project_id=project_id, quota='performance_test_runs'):
        #     return {"Forbidden": "The number of performance test runs allowed in the project has been exceeded"}
        report = APIReport(name=args["test_name"],
                           test_status=args["test_status"],
                           project_id=project.id,
                           environment=args["environment"],
                           type=args["type"],
                           end_time="",
                           start_time=args["start_time"],
                           failures=0,
                           total=0,
                           thresholds_missed=0,
                           throughput=0,
                           vusers=args["vusers"],
                           pct50=0,
                           pct75=0,
                           pct90=0,
                           pct95=0,
                           pct99=0,
                           _max=0,
                           _min=0,
                           mean=0,
                           duration=args["duration"],
                           build_id=args["build_id"],
                           lg_type=args["lg_type"],
                           onexx=0,
                           twoxx=0,
                           threexx=0,
                           fourxx=0,
                           fivexx=0,
                           requests="",
                           release_id=args.get("release_id"),
                           test_uid=args.get("test_id"))
        report.insert()
        statistic = Statistic.query.filter_by(project_id=project_id).first()
        setattr(statistic, 'performance_test_runs', Statistic.performance_test_runs + 1)
        statistic.commit()
        return report.to_json()

    def put(self, project_id: int):
        args = request.json
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        test_data = get_test_details(project_id=project_id, build_id=args["build_id"], test_name=args["test_name"],
                                     lg_type=args["lg_type"])
        response_times = loads(args["response_times"])
        report = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.build_id == args["build_id"])
        ).first()
        report.end_time = test_data["end_time"]
        report.start_time = test_data["start_time"]
        report.failures = test_data["failures"]
        report.total = test_data["total"]
        report.thresholds_missed = args.get("missed", 0)
        report.throughput = test_data["throughput"]
        report.pct50 = response_times["pct50"]
        report.pct75 = response_times["pct75"]
        report.pct90 = response_times["pct90"]
        report.pct95 = response_times["pct95"]
        report.pct99 = response_times["pct99"]
        report._max = response_times["max"]
        report._min = response_times["min"]
        report.mean = response_times["mean"]
        report.onexx = test_data["1xx"]
        report.twoxx = test_data["2xx"]
        report.threexx = test_data["3xx"]
        report.fourxx = test_data["4xx"]
        report.fivexx = test_data["5xx"]
        report.requests = ";".join(test_data["requests"])
        print("***********************************")
        print(args["test_status"])
        print(type(args["test_status"]))
        print("***********************************")
        report.test_status = args["test_status"]
        report.vusers = args["vusers"]
        report.duration = args["duration"]
        report.commit()
        return {"message": "updated"}

    def delete(self, project_id: int):
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            delete_test_data(each.build_id, each.name, each.lg_type)
            baseline = APIBaseline.query.filter_by(project_id=project.id, report_id=each.id).first()
            if baseline:
                baseline.delete()
            each.delete()
        return {"message": "deleted"}
