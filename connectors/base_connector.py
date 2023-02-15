#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from abc import ABC, abstractmethod
from typing import Tuple

from ..utils.report_utils import timeframe


class BaseConnector(ABC):
    def __init__(self, **args):
        self.build_id = args['build_id']
        self.test_name = args['test_name']
        self.lg_type = args.get('lg_type')
        self.project_id = args.get('project_id') or self._get_project_id(self.build_id)
        self.start_time, self.end_time = timeframe(args)
        self.aggregation = args.get('aggregator')
        self.sampler=args.get('sampler')
        self.status=args.get("status", 'all')
        self.scope = args.get("scope[]", [])
        self.metric = args.get('metric', '')

    @abstractmethod
    def calculate_auto_aggregation(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_backend_users(self, aggregation: str) -> Tuple[list, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_requests_summary_data(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr='pct95', 
    ) -> Tuple[list, dict, dict]:
        raise NotImplementedError
    
    @abstractmethod
    def get_average_responses(self) -> Tuple[list, dict, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_tps(self, timestamps=None, users=None, scope=None) -> Tuple[list, dict, dict]:
        raise NotImplementedError
    
    @abstractmethod
    def calculate_analytics(self, scope: str, metric: str) -> Tuple[dict, str, list]:
        raise NotImplementedError
    
    @abstractmethod
    def get_tps_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError
    
    @abstractmethod
    def get_errors_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_backend_requests_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr='pct95'
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError
    
    @abstractmethod
    def get_response_codes_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr="2xx"
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError

    @abstractmethod
    def get_engine_health_cpu(self) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    def get_engine_health_memory(self) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    def get_engine_health_load(self) -> dict:
        raise NotImplementedError
