#     Copyright 2021 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import string
from os import path
from queue import Empty
from typing import List, Union
from uuid import uuid4
from json import dumps

from pylon.core.tools import log
from sqlalchemy import Column, Integer, String, JSON, ARRAY, and_

from tools import db_tools, db, rpc_tools, secrets_tools
from tools import constants as c
# from ...shared.tools.constants import CURRENT_RELEASE

from ..constants import JOB_CONTAINER_MAPPING


class PerformanceApiTest(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    __tablename__ = "performance_tests_api"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)

    parallel_runnes = Column(Integer, nullable=False)  #- runners
    location = Column(String(128), nullable=False)  #- engine location

    bucket = Column(String(128), nullable=False)
    file = Column(String(128), nullable=False)
    entrypoint = Column(String(128), nullable=False)
    runner = Column(String(128), nullable=False)

    # reporting = Column(ARRAY(JSON), nullable=False)  #- integrations?

    test_parameters = Column(ARRAY(JSON), nullable=True)

    integrations = Column(JSON, nullable=True)

    schedules = Column(ARRAY(Integer), nullable=True, default=[])

    env_vars = Column(JSON)  #-?
    customization = Column(JSON)   #-?
    cc_env_vars = Column(JSON)   #-?

    # git = Column(JSON)   #-? source?
    # local_path = Column(String(128))  # - source local
    sources = Column(ARRAY)

    last_run = Column(Integer)  #-? why not date?
    job_type = Column(String(20))

    def add_schedule(self, schedule_data: dict, commit_immediately: bool = True):
        schedule_data['test_id'] = self.id  # todo: change to uid
        schedule_data['project_id'] = self.project_id
        try:
            schedule_id = self.rpc.timeout(2).scheduling_security_create_schedule(data=schedule_data)  # todo: handle for backend performance
            log.info(f'schedule_id {schedule_id}')
            updated_schedules = set(self.schedules)
            updated_schedules.add(schedule_id)
            self.schedules = list(updated_schedules)
            if commit_immediately:
                self.commit()
            log.info(f'self.schedules {self.schedules}')
        except Empty:
            log.warning('No scheduling rpc found')

    def handle_change_schedules(self, schedules_data: List[dict]):
        new_schedules_ids = set(i['id'] for i in schedules_data if i['id'])
        ids_to_delete = set(self.schedules).difference(new_schedules_ids)
        self.schedules = []
        for s in schedules_data:
            log.warning('!!!adding schedule')
            log.warning(s)
            self.add_schedule(s, commit_immediately=False)
        try:
            self.rpc.timeout(2).scheduling_delete_schedules(ids_to_delete)
        except Empty:
            ...
        self.commit()

    @classmethod
    def get_api_filter(cls, project_id: int, test_id: Union[int, str]):
        log.info(f'getting filter int? {isinstance(test_id, int)}  {test_id}')
        if isinstance(test_id, int):
            return and_(
                cls.project_id == project_id,
                cls.id == test_id
            )
        return and_(
            cls.project_id == project_id,
            cls.test_uid == test_id
        )







    def set_last_run(self, ts):
        self.last_run = ts
        self.commit()

    @staticmethod
    def sanitize(val):
        valid_chars = "_%s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in val if c in valid_chars)

    def insert(self):
        if self.runner not in JOB_CONTAINER_MAPPING.keys():
            return False
        self.name = self.sanitize(self.name)
        if not self.test_uid:
            self.test_uid = str(uuid4())
        test_params_list = []
        for each in self.params:
            test_params_list.append(each["name"])
        if "influx.port" not in test_params_list:
            self.params.append({"name": "influx.port", "default": "{{secret.influx_port}}", "description": "",
                                "type": "", "action": ""})
        if "influx.host" not in test_params_list:
            self.params.append({"name": "influx.host", "default": "{{secret.influx_ip}}", "description": "",
                                "type": "", "action": ""})
        if "influx_user" not in test_params_list:
            self.params.append({"name": "influx.username", "default": "{{secret.influx_user}}", "description": "",
                                "type": "", "action": ""})
        if "influx_password" not in test_params_list:
            self.params.append({"name": "influx.password", "default": "{{secret.influx_password}}", "description": "",
                                "type": "", "action": ""})
        if "galloper_url" not in test_params_list:
            self.params.append({"name": "galloper_url", "default": "{{secret.galloper_url}}", "description": "",
                                "type": "", "action": ""})
        if "influx.db" not in test_params_list:
            self.params.append({"name": "influx.db", "default": JOB_CONTAINER_MAPPING[self.runner]['influx_db'],
                                "description": "", "type": "", "action": ""})
        if "test_name" not in test_params_list:
            self.params.append({"name": "test_name", "default": self.name, "description": "", "type": "",
                                "action": ""})
        if "comparison_db" not in test_params_list:
            self.params.append({"name": "comparison_db", "default": "{{secret.comparison_db}}", "description": "",
                                "type": "", "action": ""})
        if "telegraf_db" not in test_params_list:
            self.params.append({"name": "telegraf_db", "default": "{{secret.telegraf_db}}", "description": "",
                                "type": "", "action": ""})
        if "loki_host" not in test_params_list:
            self.params.append({"name": "loki_host", "default": "{{secret.loki_host}}", "description": "",
                                "type": "", "action": ""})
        if "loki_port" not in test_params_list:
            self.params.append({"name": "loki_port", "default": "{{secret.loki_port}}", "description": "",
                                "type": "", "action": ""})
        self.job_type = JOB_CONTAINER_MAPPING[self.runner]['job_type']
        if "test_type" not in test_params_list:
            self.params.append({"name": "test_type", "default": "default", "description": "", "type": "", "action": ""})
        if "env_type" not in test_params_list:
            self.params.append({"name": "env_type", "default": "not_specified", "description": "", "type": "",
                                "action": ""})
        if self.region == "":
            self.region = "default"
        self.runner = JOB_CONTAINER_MAPPING[self.runner]['container']  # here because influx_db

        super().insert()

    def configure_execution_json(self, output='cc', test_type=None, env_vars=None, reporting=None,
                                 customization=None, cc_env_vars=None, parallel=None, region=None, execution=False,
                                 emails=None):

        # param_names = [param["name"] for param in params]
        # for param in self.params:
        #     if param["name"] not in param_names:
        #         params.append(param)
        pairs = {
            "customization": [customization, self.customization],
            # "params": [params, self.params],
            "env_vars": [env_vars, self.env_vars],
            "cc_env_vars": [cc_env_vars, self.cc_env_vars],
            "reporting": [reporting, self.reporting]
        }
        for pair in pairs.keys():
            if not pairs[pair][0]:
                pairs[pair][0] = pairs[pair][1]
            else:
                for each in list(pairs[pair][0].keys()) + list(set(pairs[pair][1].keys()) - set(pairs[pair][0].keys())):
                    pairs[pair][0][each] = pairs[pair][0][each] if each in list(pairs[pair][0].keys()) \
                        else pairs[pair][1][each]
        cmd = ''
        # if not params:
        #     params = self.params
        if self.job_type == 'perfmeter':
            entrypoint = self.entrypoint if path.exists(self.entrypoint) else path.join('/mnt/jmeter', self.entrypoint)
            cmd = f"-n -t {entrypoint}"
            for each in self.test_parameters:
                cmd += f" -J{each['name']}={each['default']}"

        execution_json = {
            "container": self.runner,
            "execution_params": {
                "cmd": cmd
            },
            "cc_env_vars": {},
            "bucket": self.bucket,
            "job_name": self.name,
            "artifact": self.file,
            "job_type": self.job_type,
            "concurrency": self.parallel if not parallel else parallel,
            "channel": region if region else self.region
        }
        if self.reporting:
            if "junit" in self.reporting:
                execution_json["junit"] = "True"
            if "quality" in self.reporting:
                execution_json["quality_gate"] = "True"
            if "perfreports" in self.reporting:
                execution_json["save_reports"] = "True"
            if "jira" in self.reporting:
                execution_json["jira"] = "True"
            if "email" in self.reporting:
                execution_json["email"] = "True"
            if "rp" in self.reporting:
                execution_json["report_portal"] = "True"
            if "ado" in self.reporting:
                execution_json["azure_devops"] = "True"
        # if emails:
        #     _emails = self.emails
        #     for each in emails.split(","):
        #         if each not in _emails:
        #             _emails += f",{each}"
        #     execution_json["email_recipients"] = _emails
        # else:
        #     execution_json["email_recipients"] = self.emails

        if pairs["env_vars"][0]:
            for key, value in pairs["env_vars"][0].items():
                execution_json["execution_params"][key] = value
        if "influxdb_host" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_host"] = "{{secret.influx_ip}}"
        if "influxdb_user" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_user"] = "{{secret.influx_user}}"
        if "influxdb_password" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_password"] = "{{secret.influx_password}}"
        if "influxdb_database" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_database"] = "{{secret.gatling_db}}"
        if "influxdb_comparison" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_comparison"] = "{{secret.comparison_db}}"
        if "influxdb_telegraf" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_telegraf"] = "{{secret.telegraf_db}}"
        if "loki_host" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["loki_host"] = "{{secret.loki_host}}"
        if "loki_port" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["loki_port"] = "3100"
        if pairs["cc_env_vars"][0]:
            for key, value in pairs["cc_env_vars"][0].items():
                execution_json["cc_env_vars"][key] = value
        if "RABBIT_HOST" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["RABBIT_HOST"] = "{{secret.rabbit_host}}"
        if "RABBIT_USER" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["RABBIT_USER"] = "{{secret.rabbit_user}}"
        if "RABBIT_PASSWORD" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["RABBIT_PASSWORD"] = "{{secret.rabbit_password}}"
        if "GALLOPER_WEB_HOOK" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["GALLOPER_WEB_HOOK"] = "{{secret.post_processor}}"
        if pairs["customization"][0]:
            for key, value in pairs["customization"][0].items():
                if "additional_files" not in execution_json["execution_params"]:
                    execution_json["execution_params"]["additional_files"] = dict()
                execution_json["execution_params"]["additional_files"][key] = value
        if self.git:
            execution_json["git"] = self.git
        if self.local_path:
            execution_json["local_path"] = self.local_path
        if self.job_type == "perfgun":
            execution_json["execution_params"]['test'] = self.entrypoint
            execution_json["execution_params"]["GATLING_TEST_PARAMS"] = ""
            for key, value in self.test_parameters.items():
                execution_json["execution_params"]["GATLING_TEST_PARAMS"] += f"-D{key}={value} "
        execution_json["execution_params"] = dumps(execution_json["execution_params"])
        if execution:
            execution_json = secrets_tools.unsecret(execution_json, project_id=self.project_id)
        if output == 'cc':
            return execution_json
        else:
            return "docker run -e project_id=%s -e galloper_url=%s -e token=%s" \
                   " getcarrier/control_tower:%s --test_id=%s" \
                   "" % (self.project_id, secrets_tools.unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                         secrets_tools.unsecret("{{secret.auth_token}}", project_id=self.project_id),
                         c.CURRENT_RELEASE, self.test_uid)

    # def to_json(self, exclude_fields: tuple = ()) -> dict:
    #     test_param = super().to_json()
    #     test_param['params'] = [d for d in test_param['params'] if d["name"] not in exclude_fields]
    #     for key in exclude_fields:
    #         if key in test_param.keys():
    #             del test_param[key]
    #     return test_param
