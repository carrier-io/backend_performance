from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ..utils.charts_utils import timeframe


class BaseConnector(ABC):
    def __init__(self, **args):
        self.build_id = args['build_id']
        self.test_name = args['test_name']
        self.lg_type = args.get('lg_type')
        self.project_id = self._get_project_id(self.build_id)
        self.start_time, self.end_time = timeframe(args)
        self.aggregation = args.get('aggregator')
        self.sampler=args.get('sampler')
        self.status=args.get("status", 'all')
    
    @abstractmethod
    def _get_project_id(self, build_id: str) -> int:
        raise NotImplementedError
    
    @abstractmethod
    def _get_client(self, project_id: int):
        raise NotImplementedError

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
    def calculate_analytics(
            self, 
            scope: str, 
            metric: str, 
    ) -> Tuple[dict, str, list]:
        raise NotImplementedError
    
    @abstractmethod
    def get_tps_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
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
            aggr='pct95', 
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError
    
    @abstractmethod
    def get_response_codes_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr="2xx", 
        ) -> Tuple[list, dict, dict]:
        raise NotImplementedError
