from typing import Optional
from flask import request
from flask_restful import Resource

from ...models.reports import Report
from pylon.core.tools import log


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<int:report_id>',
    ]
    SERVICE_TAGS = ('baseline',)

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, report_id: Optional[int] = None):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        if not report_id:
            query_result = Report.query.with_entities(Report.tags).filter(
                Report.project_id == project.id,
                Report.tags != '{}'
            ).all()
            all_tags = set()
            for tags in query_result:
                all_tags.update(*tags)
            return {"tags": list(all_tags)}, 200
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        return {"tags": report.tags}, 200

    def post(self, project_id: int, report_id: int):
        new_tag = request.json["tag"]
        if new_tag in self.SERVICE_TAGS:
            return {"message": f"provided name {new_tag} cannot be used as a tag name"}, 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        added_tag = report.add_tag(new_tag)
        if not added_tag:
            return {"message": f"provided tag {new_tag} is already exist"}, 400
        return {"message": f"tag {added_tag} was added"}, 200

    def delete(self, project_id: int, report_id: int):
        tag_to_delete = request.args["tag"]
        if tag_to_delete in self.SERVICE_TAGS:
            return {"message": f"provided tag {tag_to_delete} cannot be deleted"}, 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        deleted_tag = report.delete_tag(tag_to_delete)
        if not deleted_tag:
            return {"message": f"provided tag {tag_to_delete} is not exist"}, 400
        return {"message": f"tag {deleted_tag} was deleted"}, 204
