from tools import api_tools, auth, PostProcessingManager

from ...constants import JOB_CONTAINER_MAPPING
from ...models.reports import Report


class API(api_tools.APIBase):
    url_params = [
        '<int:project_id>/<int:report_id>',
        '<string:mode>/<int:project_id>/<int:report_id>',
    ]

    @auth.decorators.check_api({
        "permissions": ["performance.backend.tests.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int, report_id: int, **kwargs):
        manager = PostProcessingManager(project_id)
        report = Report.query.filter(Report.id == report_id).first_or_404()
        influx_db = JOB_CONTAINER_MAPPING.get(report.test_config['runner']).get('influx_db')
        manager.run_task(
            report=report.to_json(),
            influx_db=influx_db,
            #queue_name=report.test_config['location']
            queue_name="default"
        )
