from flask import request
from flask_restful import Resource
from ...models.runners import Runner
from sqlalchemy import and_


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<int:runner_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = Runner.query.with_entities(
            Runner.id, Runner.container_type, Runner.config, Runner.is_active, Runner.is_default
            ).filter(
                and_(Runner.project_id == project.id)
        ).all()
        runners = []
        for id, container_type, config, is_active, is_default in query_result:
            for key, values in config.items():
                runners.append({
                    'id': id,
                    'container_type': container_type,
                    'name': key,
                    **values,
                    'is_active': is_active, 
                    'is_default': is_default
                })
        return {'total': len(runners), 'rows': runners}, 200

    def post(self, project_id: int):
        try:
            container_type = request.json['container_type']
            name = request.json['name']
            container = request.json['container']
            is_active = request.json['is_active']
        except KeyError:
            return 'container_type, name, container and is_active must be provided', 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        config = {
            name: {
                "container": container,
                "job_type": 'perfmeter' if container_type == 'jmeter' else 'perfgun',
                "influx_db": '{{secret.jmeter_db}}' if container_type == 'jmeter' else '{{secret.gatling_db}}',
            }
        }
        runner = Runner(
            project_id=project.id,
            container_type=container_type,
            config=config,
            is_active=is_active,
            is_default=False
        )
        runner.insert()
        return runner.to_json(), 200

    def put(self, project_id: int, runner_id: int):
        try:
            is_active = request.json['is_active']
        except KeyError:
            return 'is_active must be provided', 400
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        runner = Runner.query.filter_by(project_id=project.id, id=runner_id).first()
        runner.is_active = is_active
        runner.commit()
        return {"message": f"status changed to {runner.is_active}"}, 200

    def delete(self, project_id: int, runner_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        runner = Runner.query.filter_by(project_id=project.id, id=runner_id).first()
        if runner.is_default:
            return {"message": "Cannot delete a default runner"}, 400
        runner.delete()
        Runner.commit()
        return {"message": "deleted"}, 204
