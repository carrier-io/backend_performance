import docker
import operator
from sqlalchemy import and_
from json import loads
import re
from datetime import datetime
from uuid import uuid4

from ..constants import JOB_CONTAINER_MAPPING, JOB_TYPE_MAPPING
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


def get_backend_test_data(event):
    users_count = 0
    duration = 0
    vusers_var_names = ["vusers", "users", "users_count", "ramp_users", "user_count"]
    lg_type = JOB_TYPE_MAPPING.get(event["job_type"], "other")
    tests_count = 1
    if lg_type == 'jmeter':
        for i in range(tests_count):
            exec_params = loads(event["execution_params"])["cmd"] + " "
            test_type = re.findall('-Jtest_type=(.+?) ', exec_params)
            test_type = test_type[0] if len(test_type) else 'demo'
            environment = re.findall("-Jenv_type=(.+?) ", exec_params)
            environment = environment[0] if len(environment) else 'demo'
            test_name = re.findall("-Jtest_name=(.+?) ", exec_params)
            test_name = test_name[0] if len(test_name) else 'test'
            duration = re.findall("-JDURATION=(.+?) ", exec_params)
            duration = float(duration[0]) if len(duration) else 0
            for each in vusers_var_names:
                if f'-j{each}' in exec_params.lower():
                    pattern = f'-j{each}=(.+?) '
                    vusers = re.findall(pattern, exec_params.lower())
                    users_count += int(vusers[0]) * event["concurrency"]
                    break
    elif lg_type == 'gatling':
        for i in range(tests_count):
            exec_params = loads(event["execution_params"])
            test_type = exec_params['test_type'] if exec_params.get('test_type') else 'demo'
            test_name = exec_params['test'].split(".")[1].lower() if exec_params.get('test') else 'test'
            environment = exec_params['env'] if exec_params.get('env') else 'demo'
            if exec_params.get('GATLING_TEST_PARAMS'):
                if '-dduration' in exec_params['GATLING_TEST_PARAMS'].lower():
                    duration = re.findall("-dduration=(.+?) ", exec_params['GATLING_TEST_PARAMS'].lower())[0]
                for each in vusers_var_names:
                    if f'-d{each}' in exec_params['GATLING_TEST_PARAMS'].lower():
                        pattern = f'-d{each}=(.+?) '
                        vusers = re.findall(pattern, exec_params['GATLING_TEST_PARAMS'].lower())
                        users_count += int(vusers[0]) * event["concurrency"]
                        break
    else:
        return {}
    start_time = datetime.utcnow().isoformat("T") + "Z"

    data = {'build_id': f'build_{uuid4()}', 'test_name': test_name, 'lg_type': lg_type, 'type': test_type,
            'duration': duration, 'vusers': users_count, 'environment': environment, 'start_time': start_time,
            'missed': 0, 'status': 'In progress'}
    return data


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
