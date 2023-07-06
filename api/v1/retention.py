from flask import request
from pylon.core.tools import log

from ...models.reports import Report
from ...utils.retention_utils import RetentionModel

from tools import api_tools, auth, VaultClient


class API(api_tools.APIBase):
    url_params = [
        '<int:project_id>/<string:uid>',
        '<string:mode>/<int:project_id>/<string:uid>',
    ]

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
            "administration": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int, uid: str, **kwargs):
        retention, start_time, end_time = Report.query.with_entities(
            Report.retention,
            Report.start_time,
            Report.end_time
        ).filter(
            Report.project_id == project_id,
            Report.uid == uid
        ).first()

        default_project_retention = RetentionModel(days=int(
            VaultClient(project_id).get_all_secrets().get(
                'backend_performance_results_retention', 30
            )
        ))

        if retention is None:
            return {
                'ttl': None,
                'retention': None,
                'default_retention': default_project_retention.dict(exclude_unset=True)
            }, 200

        retention = RetentionModel.parse_obj(retention)
        ttl = retention.compute_ttl(start_time, end_time)

        return {
            'ttl': ttl.date().isoformat(),
            # 'ts': ttl.timestamp() - datetime.utcnow().timestamp(),
            'retention': retention.dict(exclude_unset=True),
            'default_retention': default_project_retention.dict(exclude_unset=True)
        }

    @auth.decorators.check_api({
        "permissions": ["performance.backend.reports.edit"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
            "administration": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def put(self, project_id: int, uid: str, **kwargs):
        '''
        request.json
            set_default: Optional[bool] = False,
            timedelta: None for infinite or {years: 111, months: 111, weeks: 111, days: 111}
        '''
        default_flag = request.json.pop('set_default', False)
        if default_flag:
            try:
                retention = RetentionModel(days=int(
                    VaultClient(project_id).get_all_secrets().get(
                        'backend_performance_results_retention', 30
                    ))
                )
            except ValueError:
                retention = None
        else:
            retention = request.json['timedelta']
            if retention is not None:
                retention = RetentionModel.parse_obj(retention)

        report = Report.query.filter(
            Report.project_id == project_id,
            Report.uid == uid
        ).first()
        report.retention = None if not retention else retention.dict(exclude_unset=True)
        report.commit()

        if retention is None:
            return {
                'ttl': None,
                'retention': None
            }, 200

        ttl = retention.compute_ttl(report.start_time, report.end_time)
        return {
            'ttl': ttl.date().isoformat(),
            # 'ts': ttl.timestamp() - datetime.utcnow().timestamp(),
            'retention': retention.dict(exclude_unset=True)
        }, 200
