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
from queue import Empty
from typing import List, Union

from pylon.core.tools import log
from sqlalchemy import Column, Integer, String, JSON, ARRAY, and_

from tools import db_tools, db, rpc_tools, secrets_tools
from tools import constants as c
from .pd.execution_json import ExecutionParams, CcEnvVars
from ..constants import JOB_CONTAINER_MAPPING
from ..utils.utils import parse_source


class PerformanceApiTest(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    __tablename__ = "performance_tests_api"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)

    parallel_runners = Column(Integer, nullable=False)  #- runners
    location = Column(String(128), nullable=False)  #- engine location
    # region = Column(String(128), nullable=False)

    # bucket = Column(String(128), nullable=False) # migrated to sources
    # file = Column(String(128), nullable=False) # migrated to sources

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
    source = Column(JSON, nullable=False)

    # job_type = Column(String(20))

    @property
    def container(self):
        return JOB_CONTAINER_MAPPING.get(self.runner, {}).get('container')

    @property
    def job_type(self):
        return JOB_CONTAINER_MAPPING.get(self.runner, {}).get('job_type')

    @property
    def influx_db(self):
        return JOB_CONTAINER_MAPPING.get(self.runner, {}).get('influx_db')


    def add_schedule(self, schedule_data: dict, commit_immediately: bool = True):
        schedule_data['test_id'] = self.id
        schedule_data['project_id'] = self.project_id
        try:
            schedule_id = self.rpc.timeout(2).scheduling_backend_performance_create_schedule(data=schedule_data)
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

    def insert(self):
        test_params_list = [i.get('name') for i in self.test_parameters]

        from .pd.performance_test import PerformanceTestParam
        if "influx.db" not in test_params_list:
            self.test_parameters.append(
                PerformanceTestParam(
                    name="influx.db",
                    default=self.influx_db
                ).dict()
            )
        if "test_name" not in test_params_list:
            self.test_parameters.append(
                PerformanceTestParam(
                    name="test_name",
                    default=self.name
                ).dict()
            )
        super().insert()

    def configure_execution_json(self, output: str = 'cc', execution: bool = False):
        execution_json = {
            'test_id': self.test_uid,
            "container": self.container,
            "execution_params": ExecutionParams.from_orm(self).json(exclude_none=True),
            "cc_env_vars": CcEnvVars.from_orm(self).dict(exclude_none=True),
            "job_name": self.name,
            "job_type": self.job_type,
            "concurrency": self.parallel_runners,
            "channel": self.location,
            **parse_source(self.source).execution_json
        }


        # if self.reporting:
        #     if "junit" in self.reporting:
        #         execution_json["junit"] = "True"
        #     if "quality" in self.reporting:
        #         execution_json["quality_gate"] = "True"
        #     if "perfreports" in self.reporting:
        #         execution_json["save_reports"] = "True"
        #     if "jira" in self.reporting:
        #         execution_json["jira"] = "True"
        #     if "email" in self.reporting:
        #         execution_json["email"] = "True"
        #     if "rp" in self.reporting:
        #         execution_json["report_portal"] = "True"
        #     if "ado" in self.reporting:
        #         execution_json["azure_devops"] = "True"


        # if emails:
        #     _emails = self.emails
        #     for each in emails.split(","):
        #         if each not in _emails:
        #             _emails += f",{each}"
        #     execution_json["email_recipients"] = _emails
        # else:
        #     execution_json["email_recipients"] = self.emails



        # todo: leave this? to json?
        # execution_json["execution_params"] = dumps(execution_json["execution_params"])


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

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test = super().to_json(exclude_fields=exclude_fields)
        if 'job_type' not in exclude_fields:
            test['job_type'] = self.job_type
        if test.get('test_parameters'):
            from .pd.performance_test import PerformanceTestParams
            test['test_parameters'] = PerformanceTestParams.from_orm(self).exclude_params(
                exclude_fields
            ).dict()['test_parameters']
        return test
