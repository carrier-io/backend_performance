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

from pylon.core.tools import log
from sqlalchemy import Column, Integer, String, Boolean, JSON, ARRAY

from tools import db_tools, db, rpc_tools


class Runner(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    __tablename__ = "backend_runners"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    container_type = Column(String(128), unique=False)
    config = Column(JSON, nullable=False, unique=False)
    is_active = Column(Boolean, nullable=False, unique=False, default=True)
    is_default = Column(Boolean, nullable=False, unique=False)
