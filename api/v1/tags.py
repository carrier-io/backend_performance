from typing import Optional
from flask import request
from flask_restful import Resource

from ...models.reports import Report
from pylon.core.tools import log


class API(Resource):
    url_params = [
        '<int:project_id>/<int:report_id>',
    ]
    SERVICE_TAGS = ('baseline',)

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, report_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        get_all_tags = request.args.get("global")
        if get_all_tags:
            current_report = Report.query.filter_by(project_id=project.id, id=report_id).first()
            current_tag_titles = [tag['title'] for tag in current_report.tags]
            reporters = Report.query.with_entities(Report.tags).filter(
                Report.project_id == project.id,
            ).all()
            all_tags, titles = [], []
            for tags in reporters:
                for tag in tags[0]:
                    if tag['title'] not in titles:
                        tag['is_selected'] = tag['title'] in current_tag_titles
                        titles.append(tag['title'])
                        all_tags.append(tag)
            return {"tags": all_tags}, 200
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        return {"tags": report.tags}, 200

    def post(self, project_id: int, report_id: int):
        new_tag_title = request.json["title"]
        new_tag_color = request.json["hex"]
        if new_tag_title in self.SERVICE_TAGS:
            return {"message": f"provided name {new_tag_title} cannot be used as a tag name"}, 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        added_tag_title = report.add_tag(new_tag_title, new_tag_color)
        if not added_tag_title:
            return {"message": f"provided tag {new_tag_title} is already exist"}, 400
        return {"message": f"tag {added_tag_title} was added"}, 200

    def delete(self, project_id: int, report_id: int):
        tag_to_delete = request.args["title"]
        if tag_to_delete in self.SERVICE_TAGS:
            return {"message": f"provided tag {tag_to_delete} cannot be deleted"}, 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        report = Report.query.filter_by(project_id=project.id, id=report_id).first()
        deleted_tag = report.delete_tag(tag_to_delete)
        if not deleted_tag:
            return {"message": f"provided tag {tag_to_delete} is not exist"}, 400
        return {"message": f"tag {deleted_tag} was deleted"}, 204
