#   Copyright 2021 getcarrier.io
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

from typing import Optional, Tuple

from tools import influx_tools
from tools import constants as c
from ..models.reports import Report
from pylon.core.tools import log

from ..connectors.base_connector import BaseConnector


class InfluxConnector(BaseConnector):
    
    def __init__(self, **args) -> None:
        super().__init__(**args)
        self.db_name = args.get('db_name')
        self.client = self._get_client(self.project_id, self.db_name)
        if self.aggregation == 'auto':
            self.aggregation = self.calculate_auto_aggregation()
        
        
    def _get_project_id(self, build_id: str) -> int:
        resp = Report.query.with_entities(Report.project_id).filter(Report.build_id == build_id).first()
        return resp[0]


    def _get_client(self, project_id: int, db_name: str=None):
        return influx_tools.get_client(project_id, db_name)


    def calculate_auto_aggregation(self):
        aggregation = "1s"
        aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
        for i in range(len(aggr_list)):
            aggr = aggr_list[i]
            query = f"select sum(\"count\") from (select count(pct95) from {self.lg_type}_{self.project_id}..{self.test_name}_{aggr} " \
                    f"where time>='{self.start_time}' and time<='{self.end_time}' and build_id='{self.build_id}' group by time({aggr}))"
            result = list(self.client.query(query)[f"{self.test_name}_{aggr}"])
            if result:
                if int(result[0]["sum"]) > c.MAX_DOTS_ON_CHART and aggregation != "10m":
                    aggregation = aggr_list[i + 1]
                if int(result[0]["sum"]) == 0 and aggregation != "1s":
                    aggregation = "30s"
                    break
        return aggregation


    def get_backend_users(self, aggregation):
        query = f"select sum(\"max\") from (select max(\"active\") from {self.lg_type}_{self.project_id}..\"users_{aggregation}\" " \
                f"where build_id='{self.build_id}' group by lg_id) " \
                f"WHERE time>='{self.start_time}' and time<='{self.end_time}' GROUP BY time(1s)"
        res = self.client.query(query)[f'users_{aggregation}']
        timestamps = []
        results = {"users": {}}
        # aggregation of users
        _tmp = []
        if 'm' in aggregation:
            aggregation = f"{str(int(aggregation.replace('m', '')) * 60)}s"
        for _ in res:
            _tmp.append(_['sum'] if _['sum'] else 0)
            results["users"][_['time']] = None
            if _['time'] not in timestamps:
                timestamps.append(_['time'])
            if (len(_tmp) % int(aggregation.replace('s', ''))) == 0:
                results["users"][_['time']] = max(_tmp)
                _tmp = []
        return timestamps, results


    def get_requests_summary_data(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr='pct95'
        ) -> Tuple[list, dict, dict]:

        scope_addon = ""
        status_addon = ""
        group_by = ""
        aggr = aggr.lower()

        if scope and scope != 'All':
            scope_addon = f"and request_name='{scope}'"
        elif scope != 'All':
            group_by = "request_name, "

        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"

        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        query = f"select time, {group_by}percentile(\"{aggr}\", 95) as rt " \
                f"from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation} " \
                f"where time>='{self.start_time}' and time<='{self.end_time}' {status_addon} and sampler_type='{self.sampler}' and " \
                f"build_id='{self.build_id}' {scope_addon} group by {group_by}time({self.aggregation})"
        res = self.client.query(query)[f"{self.test_name}_{self.aggregation}"]
        results = {}
        if group_by:
            for _ in res:
                if not _.get('request_name'):
                    continue
                if _['request_name'] not in results:
                    results[_['request_name']] = {}
                    for ts in timestamps:
                        results[_['request_name']][ts] = None
                results[_['request_name']][_['time']] = _['rt']
        else:
            results['response'] = {}
            # for ts in timestamps:
            #     results['response'][ts] = None
            for _ in res:
                results['response'][_['time']] = _['rt']
        return timestamps, results, users


    def get_average_responses(self) -> Tuple[list, dict, dict]:
        timestamps, users = self.get_backend_users(self.aggregation)
        status_addon = ""
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
        responses_query = f"select time, percentile(\"pct95\", 95) from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation} "\
                        f"where time>='{self.start_time}' " \
                        f"and time<='{self.end_time}' and sampler_type='{self.sampler}'{status_addon} and " \
                        f"build_id='{self.build_id}' group by time({self.aggregation})"
        res = self.client.query(responses_query)[f"{self.test_name}_{self.aggregation}"]
        results = {"responses": {}}
        # for _ in timestamps:
        #     results['responses'][_] = None
        for _ in res:
            results["responses"][_['time']] = _['percentile']
        return timestamps, results, users


    def get_tps(self, timestamps=None, users=None, scope=None) -> Tuple[list, dict, dict]:
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        scope_addon = ""
        status_addon = ""
        if scope and scope != 'All':
            scope_addon = f"and request_name='{scope}'"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
        responses_query = f"select time, sum(total) from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation}" \
                        f" where time>='{self.start_time}' " \
                        f"and time<='{self.end_time}' and sampler_type='{self.sampler}' {status_addon} and build_id='{self.build_id}' " \
                        f"{scope_addon} group by time({self.aggregation})"
        res = self.client.query(responses_query)[f"{self.test_name}_{self.aggregation}"]
        results = {"throughput": {}}
        # for _ in timestamps:
        #     results['throughput'][_] = None
        for _ in res:
            results['throughput'][_['time']] = _['sum']
        return timestamps, results, users


    def calculate_analytics(self, scope: str, metric: str):
        data = None
        axe = 'count'
        if metric == "Users":
            timestamps, data = self.get_backend_users(self.aggregation)        
        elif metric == "Throughput":
            timestamps, data, _ = self.get_tps_analytics(scope=scope)
        elif metric == "Errors":
            timestamps, data, _ = self.get_errors_analytics(scope=scope)
        elif metric in ["Min", "Median", "Max", "pct90", "pct95", "pct99"]:
            timestamps, data, _ = self.get_backend_requests_analytics(scope=scope, aggr=metric)
            axe = 'time'
        elif "xx" in metric:
            timestamps, data, _ = self.get_response_codes_analytics(scope=scope, aggr=metric)
        return data, axe, timestamps


    def get_tps_analytics(self, timestamps=None, users=None, scope=None, status='all') -> Tuple[list, dict, dict]:
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        scope_addon = ""
        status_addon = ""
        if scope and 'All' not in scope:
            scope_addon = "and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        if status != 'all':
            status_addon = f" and status='{status.upper()}'"
        responses_query = f"select time, sum(total) from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation}" \
                        f" where time>='{self.start_time}' " \
                        f"and time<='{self.end_time}' and sampler_type='{self.sampler}' {status_addon} and build_id='{self.build_id}' " \
                        f"{scope_addon} group by request_name, time({self.aggregation})"
        res = self.client.query(responses_query)
        res = res.items()
        data = {}
        for each in res:
            req_name = each[0][1]["request_name"]
            data[req_name] = {}
            for _ in each[1]:
                data[req_name][_['time']] = _['sum']
        return timestamps, data, users


    def get_errors_analytics(self, timestamps=None, users=None, scope=None) -> Tuple[list, dict, dict]:
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        scope_addon = ""
        if scope and 'All' not in scope:
            scope_addon = "and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        error_query = f"select time, count(status) from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation} " \
                    f"where time>='{self.start_time}' and time<='{self.end_time}' and sampler_type='{self.sampler}' and" \
                    f" build_id='{self.build_id}' and status='KO' {scope_addon} group by request_name, time({self.aggregation})"
        res = self.client.query(error_query)
        res = res.items()
        data = {}

        for each in res:
            req_name = each[0][1]["request_name"]
            data[req_name] = {}
            for _ in each[1]:
                data[req_name][_['time']] = _['count']

        return timestamps, data, users


    def get_backend_requests_analytics(
        self,
        timestamps=None, 
        users=None, 
        scope=None, 
        aggr='pct95'
    ) -> Tuple[list, dict, dict]:

        scope_addon = ""
        status_addon = ""
        group_by = "request_name, "
        aggr = aggr.lower()

        if scope and 'All' not in scope:
            scope_addon = "and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"

        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"

        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        query = f"select time, percentile(\"{aggr}\", 95) as rt from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation} " \
                f"where time>='{self.start_time}' and time<='{self.end_time}' {status_addon} and sampler_type='{self.sampler}' and " \
                f"build_id='{self.build_id}' {scope_addon} group by {group_by}time({self.aggregation})"
        res = self.client.query(query)
        res = res.items()
        data = {}

        for each in res:
            req_name = each[0][1]["request_name"]
            data[req_name] = {}
            for _ in each[1]:
                data[req_name][_['time']] = _['rt']

        return timestamps, data, users


    def get_response_codes_analytics(
            self, 
            timestamps=None, 
            users=None, 
            scope=None, 
            aggr="2xx"
        ) -> Tuple[list, dict, dict]:
        if not (timestamps and users):
            timestamps, users = self.get_backend_users(self.aggregation)
        scope_addon = ""
        status_addon = " "
        if scope and 'All' not in scope:
            scope_addon = "and ("
            for each in scope:
                scope_addon += f"request_name='{each}' OR "
            scope_addon = scope_addon[0: -4] + ")"
        if self.status != 'all':
            status_addon = f" and status='{self.status.upper()}'"
        rcode_query = f"select time, sum(\"{aggr}\") from {self.lg_type}_{self.project_id}..{self.test_name}_{self.aggregation}" \
                    f" where build_id='{self.build_id}' " \
                    f"and sampler_type='{self.sampler}' and time>='{self.start_time}' and time<='{self.end_time}'{status_addon} " \
                    f"{scope_addon} group by request_name, time({self.aggregation})"
        res = self.client.query(rcode_query)
        res = res.items()
        data = {}

        for each in res:
            req_name = each[0][1]["request_name"]
            data[req_name] = {}
            for _ in each[1]:
                data[req_name][_['time']] = _['sum']

        return timestamps, data, users


    def _get_engine_health(self, query: str):
        result = self.client.query(query)
        log.info(f'health result {result}')
        data = dict()
        for (_, groups), series in result.items():
            data[groups['host']] = list(series)
        log.info(f'health data {data}')
        return data


    def get_engine_health_cpu(self):
        query = f'''
            SELECT 
                mean(usage_system) as "system",
                mean(usage_user) as "user",
                mean(usage_softirq) as "softirq",
                mean(usage_iowait) as "iowait"
            FROM "cpu" 
            WHERE "build_id" = '{self.build_id}'
            AND cpu = 'cpu-total' 
            AND time >= '{self.start_time}'
            AND time <= '{self.end_time}'
            GROUP BY time({self.aggregation}), host
        '''
        return self._get_engine_health(query)


    def get_engine_health_memory(self):
        query = f'''
            SELECT 
                HeapMemoryUsage.used as "heap memory", 
                NonHeapMemoryUsage.used as "non-heap memory"
            FROM "java_memory" 
            WHERE "build_id" = '{self.build_id}'
            AND time >= '{self.start_time}'
            AND time <= '{self.end_time}'
            GROUP BY host
        '''
        return self._get_engine_health(query)


    def get_engine_health_load(self):
        query = f'''
            SELECT 
                mean(load1) as "load1",
                mean(load5) as "load5",
                mean(load15) as "load15"
            FROM "system" 
            WHERE "build_id" = '{self.build_id}'
            AND time >= '{self.start_time}'
            AND time <= '{self.end_time}'
            GROUP BY time({self.aggregation}), host
        '''
        return self._get_engine_health(query)
