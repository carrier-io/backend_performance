from typing import Optional
from flask import request
from flask_restful import Resource

from ...models.reports import Report
from pylon.core.tools import log
from tools import auth


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<int:report_id>',
    ]
    SERVICE_TAGS = ('baseline',)

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tags.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int):
        if request.args.get("report_id[]"):
            report_ids = list(map(int, request.args["report_id[]"].split(',')))
            selected_reports = Report.query.filter(Report.project_id == project_id,
                                                   Report.id.in_(report_ids)
                                                   ).all()
            selected_tag_titles = set()
            for report in selected_reports:
                selected_tag_titles.update(tag['title'] for tag in report.tags)
            all_reporters = Report.query.with_entities(Report.tags).filter(
                Report.project_id == project_id,
            ).all()
            all_tags, titles = [], []
            for tags in all_reporters:
                for tag in tags[0]:
                    if tag['title'] not in titles:
                        tag['is_selected'] = tag['title'] in selected_tag_titles
                        titles.append(tag['title'])
                        all_tags.append(tag)
            return {"tags": all_tags}, 200
        return {"service tags": self.SERVICE_TAGS}, 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tags.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int, report_id: int):
        new_tags = request.json.get("tags")
        if new_tags is None:
            return {"message": "Provided incorrect data"}, 400
        if new_tags:
            if {tag_key for tag in new_tags for tag_key in tag.keys()} != {'title', 'hex'}:
                return {
                    "message": "You should use 'title' and 'hex' as keys to describe tags"}, 400
            if {tag['title'].lower() for tag in new_tags} & set(self.SERVICE_TAGS):
                return {"message": "You cannot add this names to tags"}, 400
        report = Report.query.filter_by(project_id=project_id, id=report_id).first()
        report.replace_tags(new_tags)
        return {"message": f"Tags was updated"}, 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tags.edit"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def put(self, project_id: int):
        new_tags = request.json.get("tags")
        if not new_tags:
            return {"message": "Provided incorrect data"}, 400
        if not request.args.get("report_id[]"):
            return {"message": "You slould specify report ids"}, 400
        if {tag['title'].lower() for tag in new_tags} & set(self.SERVICE_TAGS):
            return {"message": "You cannot add this names to tags"}, 400
        report_ids = list(map(int, request.args["report_id[]"].split(',')))
        selected_reports = Report.query.filter(Report.project_id == project_id,
                                               Report.id.in_(report_ids)
                                               ).all()
        all_added_tags = []
        for report in selected_reports:
            added_tag_titles = report.add_tags(new_tags)
            all_added_tags.extend(added_tag_titles)
        if not all_added_tags:
            return {"message": "Provided tags are already exist"}, 400
        return {"message": f"Tags {set(all_added_tags)} were added"}, 200

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tags.delete"],
        "recommended_roles": {
            "default": {"admin": True, "editor": False, "viewer": False},
        }
    })
    def delete(self, project_id: int):
        if not (request.args.get("report_id[]") or request.args.get("tags[]")):
            return {"message": "You slould specify report ids and tags"}, 400
        tags_to_delete = [tag.lower() for tag in request.args["tags[]"].split(',')]
        if set(tags_to_delete) & set(self.SERVICE_TAGS):
            return {"message": "You cannot delete this names from tags"}, 400
        report_ids = list(map(int, request.args["report_id[]"].split(',')))
        selected_reports = Report.query.filter(Report.project_id == project_id,
                                               Report.id.in_(report_ids)
                                               ).all()
        all_deleted_tags = []
        for report in selected_reports:
            deleted_tags = report.delete_tags(tags_to_delete)
            all_deleted_tags.extend(deleted_tags)
        if not all_deleted_tags:
            return {"message": f"Provided tag {tags_to_delete} are not exist"}, 400
        return {"message": f"Tag {set(all_deleted_tags)} were deleted"}, 204
