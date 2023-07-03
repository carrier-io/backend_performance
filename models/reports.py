#     Copyright 2020 getcarrier.io
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
from uuid import uuid4

from pydantic import ValidationError
from ..utils.retention_utils import RetentionModel
from sqlalchemy import String, Column, Integer, Float, Text, JSON, DateTime, Interval
from sqlalchemy.dialects.postgresql import ARRAY

from tools import db_tools, db, VaultClient


class Report(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "backend_reports"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=False, nullable=False)
    uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), unique=False)
    environment = Column(String(128), unique=False)
    type = Column(String(128), unique=False)
    end_time = Column(String(128), unique=False, nullable=True, default=None)
    start_time = Column(String(128), unique=False)
    failures = Column(Integer, unique=False, default=0)
    total = Column(Integer, unique=False, default=0)
    thresholds_missed = Column(Integer, unique=False, nullable=True, default=0)
    throughput = Column(Float, unique=False, default=0)
    vusers = Column(Integer, unique=False)
    pct50 = Column(Float, unique=False, default=0)
    pct75 = Column(Float, unique=False, default=0)
    pct90 = Column(Float, unique=False, default=0)
    pct95 = Column(Float, unique=False, default=0)
    pct99 = Column(Float, unique=False, default=0)
    _max = Column(Float, unique=False, default=0)
    _min = Column(Float, unique=False, default=0)
    mean = Column(Float, unique=False, default=0)
    duration = Column(Integer, unique=False, default=0)
    build_id = Column(String(128), unique=True)
    lg_type = Column(String(16), unique=False)
    onexx = Column(Integer, unique=False, default=0)
    twoxx = Column(Integer, unique=False, default=0)
    threexx = Column(Integer, unique=False, default=0)
    fourxx = Column(Integer, unique=False, default=0)
    fivexx = Column(Integer, unique=False, default=0)
    requests = Column(ARRAY(String), default=[])
    tags = Column(JSON, unique=False, default=[])
    test_status = Column(
        JSON,
        default={
            "status": "Pending...",
            "percentage": 0,
            "description": "Check if there are enough workers to perform the test"
        }
    )
    test_config = Column(JSON, nullable=False, unique=False)
    # engagement id
    engagement = Column(String(64), nullable=True, default=None)
    retention = Column(JSON, nullable=True, default=None)

    @property
    def serialized(self):
        from .pd.report import ReportGetSerializer
        return ReportGetSerializer.from_orm(self)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        return self.serialized.dict(exclude=set(exclude_fields))

    def insert(self):
        if not self.uid:
            self.uid = str(uuid4())
        if not self.test_config:
            from .tests import Test
            self.test_config = Test.query.filter(
                Test.uid == self.test_uid
            ).first().api_json()

        if not self.id and not self.retention:
            try:
                self.retention = RetentionModel(days=int(
                    VaultClient(self.project_id).get_all_secrets().get(
                        'backend_performance_results_retention', 30
                    )
                )).dict(exclude_unset=True)
            except ValidationError:
                ...
        super().insert()

    def add_tags(self, tags_to_add: list) -> list:
        tags = list(self.tags)
        tag_titles = [tag['title'].lower() for tag in tags]
        added_tags = []
        for new_tag in tags_to_add:
            if new_tag['title'].lower() not in tag_titles:
                tags.append(new_tag)
                added_tags.append(new_tag['title'])
        self.tags = tags
        self.commit()
        return added_tags

    def delete_tags(self, tags_to_delete: list) -> set:
        common_tags = set(tag.lower() for tag in tags_to_delete) & \
                      set(tag['title'].lower() for tag in self.tags)
        self.tags = [tag for tag in self.tags if tag['title'].lower() not in common_tags]
        self.commit()
        return common_tags

    def replace_tags(self, tags: list):
        self.tags = tags
        self.commit()

    @property
    def is_baseline_report(self):
        return 'Baseline' in [tag.get('title') for tag in self.tags]
