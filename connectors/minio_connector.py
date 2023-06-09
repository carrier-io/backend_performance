#   Copyright 2022 getcarrier.io
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

from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from pylon.core.tools import log
from tools import constants as c
from tools import MinioClient, rpc_tools

from ..models.reports import Report
from ..connectors.base_connector import BaseConnector


class MinioConnector(BaseConnector):
    
    def __init__(self, **args) -> None:
        super().__init__(**args)
        self.client = self.get_client(self.project_id)
        self.bucket_name = f'p--{self.project_id}.{self.test_name}'.replace("_", "").lower()
        if self.aggregation == 'auto':
            self.aggregation = self.calculate_auto_aggregation()
        self.time_addon = f" where time>='{self.start_time}' and time<='{self.end_time}'"
        self.sampler_addon = f" and method{'=' if self.sampler == 'TRANSACTION' else '!='}'TRANSACTION'"
        # self.timestamps = self._calculate_timestamps(
        #     datetime.fromisoformat(self.start_time.strip('Z')),
        #     datetime.fromisoformat(self.end_time.strip('Z'))
        # )


    def _get_project_id(self, build_id: str) -> int:
        resp = Report.query.with_entities(Report.project_id).filter(Report.build_id == build_id).first()
        return resp[0]
    
    
    @staticmethod
    def get_client(project_id: int) -> MinioClient:
        rpc = rpc_tools.RpcMixin().rpc
        return MinioClient(rpc.call.project_get_or_404(project_id))


    @staticmethod
    def _calculate_timestamps(start_time: datetime, end_time: datetime) -> list:
        timestamps = []
        while start_time <= end_time:
            timestamps.append(start_time.isoformat(timespec='seconds'))
            start_time += timedelta(seconds=1)
        timestamps.append(start_time.isoformat(timespec='seconds'))
        return timestamps


    def calculate_auto_aggregation(self) -> str:
        aggregation = "1s"
        aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
        for i in range(len(aggr_list)):
            aggr = aggr_list[i]
            file_name = f'{self.build_id}_{aggr}.csv.gz'
            response = self.client.select_object_content(self.bucket_name, file_name)
            if len(response) > c.MAX_DOTS_ON_CHART and aggregation != "10m":
                aggregation = aggr_list[i + 1]
            if len(response) == 0 and aggregation != "1s":
                aggregation = "30s"
                break
        return aggregation
    
    
    def get_backend_users(self, aggregation: str) -> Tuple[list, dict]:
        file_name = f'users_{self.build_id}_1s.csv.gz'
        response = self.client.select_object_content(self.bucket_name, file_name, self.time_addon)
        timestamps = []
        results = {"users": {}}
        # aggregation of users
        _tmp = []
        if 'm' in aggregation:
            aggregation = f"{str(int(aggregation.replace('m', '')) * 60)}s"
        for line in response:
            _tmp.append(int(line['sum']) if line['sum'] != 'None' else 0)
            results["users"][line['time']] = None
            if line['time'] not in timestamps:
                timestamps.append(line['time'])
            if (len(_tmp) % int(aggregation.replace('s', ''))) == 0:
                results["users"][line['time']] = max(_tmp)
                _tmp = []
        return timestamps, results
    
    
    def get_requests_summary_data(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr='pct95', 
        ) -> Tuple[list, dict, dict]:
        
        group_by = False
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        aggr = aggr.lower()
        
        scope_addon = ""
        status_addon = ""
        
        if scope and scope != 'All':
            scope_addon = f" and request_name='{scope}'"
        if scope != 'All':
            group_by = True
        if self.status != 'all':
            # status_addon = f" {'and' if scope_addon else 'where'} status='{self.status.upper()}'"
            status_addon = f" and status='{self.status.upper()}'"
        
        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)
        # log.info('get_requests_summary_data resp %s', response)

        results = {}
        
        if group_by:
            for line in response:
                if not line.get('request_name'):
                    continue
                if line['request_name'] not in results:
                    results[line['request_name']] = {}
                results[line['request_name']][line['time']] = int(line[aggr])
        else:
            results['response'] = {}
            for line in response:
                results['response'][line['time']] = int(line[aggr])

        # log.info('get_requests_summary_data results %s', results)
        
        return timestamps, results, users


    def get_average_responses(self) -> Tuple[list, dict, dict]:
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        timestamps, users = self.get_backend_users(self.aggregation)
        status_addon = ""
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
        expression_addon = self.time_addon + status_addon + self.sampler_addon

        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)
        
        results = {"responses": {}}
        for line in response:
            results["responses"][line['time']] = int(line['pct95'])
        
        return timestamps, results, users


    def get_tps(self, timestamps=None, users=None, scope=None) -> Tuple[list, dict, dict]:
        scope_addon = ""
        status_addon = ""
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        if scope and scope != 'All':
            scope_addon = f" and request_name='{scope}'"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
            
        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        log.info(expression_addon)
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)    

        results = {'throughput': {}}
        for line in response:
            results['throughput'][line['time']] = results['throughput'].get(line['time'], 0) + int(line['total'])
        
        return timestamps, results, users


    def calculate_analytics(self) -> Tuple[dict, str, list]:
        data = None
        axe = 'count'
        if self.metric == "Users":
            timestamps, data = self.get_backend_users(self.aggregation)        
        elif self.metric == "Throughput":
            timestamps, data, _ = self.get_tps_analytics(scope=self.scope)
        elif self.metric == "Errors":
            timestamps, data, _ = self.get_errors_analytics(scope=self.scope)
        elif self.metric in ["Min", "Median", "Max", "pct90", "pct95", "pct99"]:
            timestamps, data, _ = self.get_backend_requests_analytics(scope=self.scope, aggr=self.metric)
            axe = 'time'
        elif "xx" in self.metric:
            timestamps, data, _ = self.get_response_codes_analytics(scope=self.scope, aggr=self.metric)
        return data, axe, timestamps


    def get_tps_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
        ) -> Tuple[list, dict, dict]:
        
        scope_addon = ""
        status_addon = ""
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        if scope and 'All' not in scope:
            scope_addon = " and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
            
        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon) 
            
        data = {}
        for line in response:
            if not line.get('request_name'):
                continue
            if line['request_name'] not in data:
                data[line['request_name']] = {}
            timepoint = line['time']
            data[line['request_name']][timepoint] = data[line['request_name']].get(timepoint, 0) + int(line['total'])

        return timestamps, data, users


    def get_errors_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None
        ) -> Tuple[list, dict, dict]:
        
        scope_addon = ""
        status_addon = ""
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        if scope and 'All' not in scope:
            scope_addon = " and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        status_addon = f" and status='KO'"
        
        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)
        
        data = {}
        for line in response:
            if not line.get('request_name'):
                continue
            if line['request_name'] not in data:
                data[line['request_name']] = {}
            data[line['request_name']][line['time']] = data[line['request_name']].get(line['time'], 0) + 1
        
        return timestamps, data, users


    def get_backend_requests_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr='pct95', 
        ) -> Tuple[list, dict, dict]:
        
        scope_addon = ""
        status_addon = ""
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        aggr = aggr.lower()
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)

        if scope and 'All' not in scope:
            scope_addon = " and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"

        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)     
        
        data = {}
        for line in response:
            if not line.get('request_name'):
                continue
            if line['request_name'] not in data:
                data[line['request_name']] = {}
            data[line['request_name']][line['time']] = int(line[aggr])   

        return timestamps, data, users


    def get_response_codes_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr="2xx", 
        ) -> Tuple[list, dict, dict]:
        
        scope_addon = ""
        status_addon = ""
        file_name = f'{self.build_id}_{self.aggregation}.csv.gz'
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        
        if scope and 'All' not in scope:
            scope_addon = " and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
            
        expression_addon = self.time_addon + scope_addon + status_addon + self.sampler_addon
        
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)
        
        data = {}
        for line in response:
            if not line.get('request_name'):
                continue
            if line['request_name'] not in data:
                data[line['request_name']] = {}
            data[line['request_name']][line['time']] = \
                data[line['request_name']].get(line['time'], 0) + int(line[aggr])
        return timestamps, data, users


    def get_issues(self) -> list:
        file_name = f'errors_{self.build_id}.csv.gz'
        response = self.client.select_object_content(self.bucket_name, file_name, self.time_addon)
        issues = {}
        for line in response:
            line.pop('time')
            if line['Error key'] in issues:
                issues[line['Error key']]["count"] += 1
            else: 
                issues[line['Error key']] = line
                issues[line['Error key']]["count"] = 1
        return list(issues.values())


    def _get_engine_health(self, file_name) -> dict:
        response = self.client.select_object_content(self.bucket_name, file_name, self.time_addon)
        data = dict()
        for line in response:
            host_name = line.pop('host')
            for k, v in line.items():
                if v == '': line[k] = None
            data.setdefault(host_name, []).append(line)
        return data


    def get_engine_health_cpu(self) -> dict:
        file_name = f'health_cpu_{self.build_id}_{self.aggregation}.csv.gz'
        return self._get_engine_health(file_name)


    def get_engine_health_memory(self) -> dict:
        file_name = f'health_memory_{self.build_id}.csv.gz'
        return self._get_engine_health(file_name)


    def get_engine_health_load(self) -> dict:
        file_name = f'health_load_{self.build_id}_{self.aggregation}.csv.gz'
        return self._get_engine_health(file_name)


    def get_build_data(self) -> list:
        file_name = f'summary_table_{self.build_id}.csv.gz'
        return self.client.select_object_content(self.bucket_name, file_name)


    @staticmethod
    def _str_to_digits(data: List[Dict]) -> List[Dict]:
        summary = []
        for line in data:
            for k, v in line.items():
                try:
                    line[k] = float(v)
                    if line[k].is_integer():
                        line[k] = int(v)
                except ValueError:
                    pass
            summary.append(line)
        return summary


    def get_aggregated_test_results(self) -> list:
        file_name = f'summary_table_{self.build_id}.csv.gz'
        expression_addon = f" where simulation='{self.test_name}'"
        response = self.client.select_object_content(self.bucket_name, file_name, expression_addon)
        return self._str_to_digits(response)
    
    
    def get_sampler_types(self) -> list:
        aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
        for aggr in aggr_list:
            file_name = f'{self.build_id}_{aggr}.csv.gz'
            if self.client.is_file_exist(self.bucket_name, file_name):
                response = self.client.select_object_content(self.bucket_name, file_name)
                sampler_types = set()
                for line in response:
                    sampler_types.add(line['method'] if line['method'] == 'TRANSACTION' else 'REQUEST')
                return sorted(sampler_types)
        return []

    def get_aggregations_list(self) -> list:
        aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
        existing_aggr = []
        for aggr in aggr_list:
            file_name = f'{self.build_id}_{aggr}.csv.gz'
            if self.client.is_file_exist(self.bucket_name, file_name):
                existing_aggr.append(aggr)
        return existing_aggr
