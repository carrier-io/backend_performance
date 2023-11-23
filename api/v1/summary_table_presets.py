import json
from typing import Optional, Tuple, List
from pydantic import ValidationError
from flask import request
from pylon.core.tools import log

from tools import auth, api_tools


class ProjectAPI(api_tools.APIModeHandler):
    def get(self, project_id: int):
        presets = [i.dict() for i in self.module.get_summary_table_presets(project_id)]
        return presets, 200

    def post(self, project_id: int):
        try:
            preset = self.module.create_summary_table_presets(project_id, request.json)
            return preset, 201
        except ValidationError as e:
            return e.errors(), 400

    def put(self, project_id: int):
        try:
            preset = self.module.update_summary_table_presets(project_id, request.json)
            return preset, 201
        except ValidationError as e:
            return e.errors(), 400

    def delete(self, project_id: int, preset_name: str):
        self.module.delete_summary_table_presets(project_id, preset_name)
        return '', 204


class AdminAPI(api_tools.APIModeHandler):
    pass


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        '<string:mode>/<int:project_id>',
        '<string:mode>/<int:project_id>/<string:preset_name>',
        '<int:project_id>',
        '<int:project_id>/<string:preset_name>',
    ]

    mode_handlers = {
        'administration': AdminAPI,
        'default': ProjectAPI,
    }
