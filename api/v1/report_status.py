from flask import request, make_response
from flask_restful import Resource
from datetime import datetime

from ...models.pd.report import StatusField
from ...models.reports import Report
from tools import auth


class API(Resource):
    url_params = [
        '<int:project_id>/<int:report_id>',
    ]

    def __init__(self, module):
        self.module = module
        self.sio = self.module.context.sio

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
            "administration": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int, report_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        return {"message": report.test_status["status"]}

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "editor": True, "viewer": True},
            "default": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def put(self, project_id: int, report_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        test_status = StatusField.parse_obj(request.json["test_status"])
        if test_status.description == "Failed update report":
            report.end_time = report.start_time
        if test_status.status == "Canceled":
            # check time zone
            report.end_time = datetime.utcnow().isoformat("T") + "Z"
        report.test_status = test_status.dict()
        report.commit()
        self.sio.emit("backend_test_status_updated", {"status": test_status.dict(), 'report_id': report_id})
        if test_status.percentage == 100:
            self.sio.emit('backend_test_finished', report.to_json())
        return {"message": test_status.status}, 200
