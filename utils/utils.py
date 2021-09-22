import docker
import operator
from sqlalchemy import and_
from json import loads

from ..constants import JOB_CONTAINER_MAPPING
from ...projects.models.statistics import Statistic
from ...tasks.api.utils import run_task


def compile_tests(project_id, file_name, runner):
    from flask import current_app
    client = docker.from_env()
    container_name = JOB_CONTAINER_MAPPING.get(runner)["container"]
    secrets = current_app.config["CONTEXT"].rpc_manager.call.get_secrets(project_id=project_id)
    env_vars = {"artifact": file_name, "bucket": "tests", "galloper_url": secrets["galloper_url"],
                "token": secrets["auth_token"], "project_id": project_id, "compile": "true"}
    client.containers.run(container_name, stderr=True, remove=True, environment=env_vars, tty=True, user='0:0')


def exec_test(project_id, event):
    response = run_task(project_id, event)
    response["redirect"] = f"/task/{response['task_id']}/results"

    statistic = Statistic.query.filter_by(project_id=project_id).first()
    statistic.performance_test_runs += 1
    statistic.commit()

    return response


def _calculate_limit(limit, total):
    return len(total) if limit == 'All' else limit


def get(project, args, data_model, additional_filter=None):
    limit_ = args.get("limit")
    offset_ = args.get("offset")
    if args.get("sort"):
        sort_rule = getattr(getattr(data_model, args["sort"]), args["order"])()
    else:
        sort_rule = data_model.id.desc()
    filter_ = list()
    filter_.append(operator.eq(data_model.project_id, project.id))
    if additional_filter:
        for key, value in additional_filter.items():
            filter_.append(operator.eq(getattr(data_model, key), value))
    if args.get('filter'):
        for key, value in loads(args.get("filter")).items():
            filter_.append(operator.eq(getattr(data_model, key), value))
    filter_ = and_(*tuple(filter_))
    total = data_model.query.order_by(sort_rule).filter(filter_).count()
    res = data_model.query.filter(filter_).order_by(sort_rule).limit(
        _calculate_limit(limit_, total)).offset(offset_).all()
    return total, res
