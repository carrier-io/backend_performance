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
from typing import Optional, Tuple

from pylon.core.tools import log
from tools import constants as c
from tools import MinioClient, rpc_tools

from ..models.reports import Report


def get_project_id(build_id: str) -> int:
    resp = Report.query.with_entities(Report.project_id).filter(Report.build_id == build_id).first()
    return resp[0]


def get_client(project_id) -> MinioClient:
    rpc = rpc_tools.RpcMixin().rpc
    return MinioClient(rpc.call.project_get_or_404(project_id))


def calculate_auto_aggregation(build_id: str, test_name: str, *args, **kwargs) -> str:
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    aggregation = "1s"
    aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
    for i in range(len(aggr_list)):
        aggr = aggr_list[i]
        file_name = f'{build_id}_{aggr}.csv.gz'
        response = client.select_object_content(bucket_name, file_name)
        if len(response) > c.MAX_DOTS_ON_CHART and aggregation != "10m":
            aggregation = aggr_list[i + 1]
        if len(response) == 0 and aggregation != "1s":
            aggregation = "30s"
            break
    return aggregation


def _calculate_timestamps(start_time: datetime, end_time: datetime) -> list:
    timestamps = []
    while start_time <= end_time:
        timestamps.append(start_time.isoformat(timespec='seconds'))
        start_time += timedelta(seconds=1)
    timestamps.append(start_time.isoformat(timespec='seconds'))
    return timestamps


def get_backend_users(build_id: str, test_name: str, aggregation: str) -> Tuple[list, dict]:
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'users_{build_id}_{aggregation}.csv.gz'
    response = client.select_object_content(bucket_name, file_name)
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


def get_requests_summary_data(build_id: str, test_name: str, lg_type: str,
                              start_time: str, end_time: str, aggregation: str, sampler: Optional[str] = None,
                              timestamps=None, users=None, scope=None, aggr='pct95', status='all'):
    scope_addon = ""
    status_addon = ""
    group_by = False
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    aggr = aggr.lower()
    
    if scope and scope != 'All':
        scope_addon = f" where request_name='{scope}'"
    if scope != 'All':
        group_by = True
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    
    expression_addon = scope_addon + status_addon
    
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    # dumb fixes
    timestamps = _calculate_timestamps(
        datetime.fromisoformat(start_time.strip('Z')),
        datetime.fromisoformat(end_time.strip('Z'))
    )
    
    response = client.select_object_content(bucket_name, file_name, expression_addon)
    log.info('get_requests_summary_data resp %s', response)

    results = {}
    
    if group_by:
        for line in response:
            if not line.get('request_name'):
                continue
            if line['request_name'] not in results:
                results[line['request_name']] = {}
                # for ts in timestamps:
                #     results[line['request_name']][ts] = None
            results[line['request_name']][line['time']] = int(line[aggr])
    else:
        results['response'] = {}
        # for ts in timestamps:
        #     results['response'][ts] = None
        for line in response:
            results['response'][line['time']] = int(line[aggr])

    log.info('get_requests_summary_data results %s', results)
    
    return timestamps, results, users


def get_average_responses(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler, status='all'):
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    timestamps, users = get_backend_users(build_id, test_name, aggregation)
    timestamps = _calculate_timestamps(
        datetime.fromisoformat(start_time.strip('Z')),
        datetime.fromisoformat(end_time.strip('Z'))
    )
    status_addon = ""
    if status != 'all':
        status_addon = f" where status='{status.upper()}'"
        
    response = client.select_object_content(bucket_name, file_name, status_addon)
    results = {"responses": {}}
    # for ts in timestamps:
    #     results['responses'][ts] = None
    for line in response:
        results["responses"][line['time']] = int(line['pct95'])
    return timestamps, results, users


def get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
            timestamps=None, users=None, scope=None, status='all'):
    scope_addon = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    timestamps = _calculate_timestamps(
        datetime.fromisoformat(start_time.strip('Z')),
        datetime.fromisoformat(end_time.strip('Z'))
    )
    if scope and scope != 'All':
        scope_addon = f" where request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
        
    expression_addon = scope_addon + status_addon
    
    response = client.select_object_content(bucket_name, file_name, expression_addon)    

    results = {'throughput': {}}
    # for ts in timestamps:
    #     results['throughput'][ts] = None
    for line in response:
        results['throughput'][line['time']] = results['throughput'].get(line['time'], 0) + int(line['total'])
    return timestamps, results, users


def get_tps_analytics(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                          timestamps=None, users=None, scope=None, status='all'):
    scope_addon = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    # timestamps = _calculate_timestamps(
    #     datetime.fromisoformat(start_time.strip('Z')),
    #     datetime.fromisoformat(end_time.strip('Z'))
    # )
    if scope and 'All' not in scope:
        scope_addon = " where ("
        for each in scope:
            scope_addon += f"request_name='{each}' OR "
        scope_addon = scope_addon[0: -4] + ")"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
        
    expression_addon = scope_addon + status_addon
    
    response = client.select_object_content(bucket_name, file_name, expression_addon) 
        
    data = {}
    for line in response:
        if not line.get('request_name'):
            continue
        if line['request_name'] not in data:
            data[line['request_name']] = {}
        timepoint = line['time']
        data[line['request_name']][timepoint] = data[line['request_name']].get(timepoint, 0) + int(line['total'])

    return timestamps, data, users


def get_errors_analytics(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                             timestamps=None, users=None, scope=None):
    scope_addon = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    # timestamps = _calculate_timestamps(
    #     datetime.fromisoformat(start_time.strip('Z')),
    #     datetime.fromisoformat(end_time.strip('Z'))
    # )
    if scope and 'All' not in scope:
        scope_addon = " where ("
        for each in scope:
            scope_addon += f"request_name='{each}' OR "
        scope_addon = scope_addon[0: -4] + ")"

    expression_addon = scope_addon + " and status='KO'"
    
    response = client.select_object_content(bucket_name, file_name, expression_addon)
    
    data = {}
    for line in response:
        if not line.get('request_name'):
            continue
        if line['request_name'] not in data:
            data[line['request_name']] = {}
        # for _ in timestamps:
        #     results[req_name][_] = None
        data[line['request_name']][line['time']] = data[line['request_name']].get(line['time'], 0) + 1
    log.info('=====get_errors_analytics')
    
    return timestamps, data, users


def get_backend_requests_analytics(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                         timestamps=None, users=None, scope=None, aggr='pct95', status='all'):
    scope_addon = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    aggr = aggr.lower()
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    # timestamps = _calculate_timestamps(
    #     datetime.fromisoformat(start_time.strip('Z')),
    #     datetime.fromisoformat(end_time.strip('Z'))
    # )

    if scope and 'All' not in scope:
        scope_addon = " where ("
        for each in scope:
            scope_addon += f"request_name='{each}' OR "
        scope_addon = scope_addon[0: -4] + ")"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"

    expression_addon = scope_addon + status_addon
    
    response = client.select_object_content(bucket_name, file_name, expression_addon)     
    
    data = {}
    for line in response:
        if not line.get('request_name'):
            continue
        if line['request_name'] not in data:
            data[line['request_name']] = {}
        # for _ in timestamps:
        #     results[req_name][_] = None
        data[line['request_name']][line['time']] = int(line[aggr])   

    return timestamps, data, users


def get_response_codes_analytics(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                     timestamps=None, users=None, scope=None, aggr="2xx", status='all'):
    scope_addon = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    bucket_name = f'p--{project_id}.{test_name}'.replace("_", "").lower()
    file_name = f'{build_id}_{aggregation}.csv.gz'
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, test_name, aggregation)
    # timestamps = _calculate_timestamps(
    #     datetime.fromisoformat(start_time.strip('Z')),
    #     datetime.fromisoformat(end_time.strip('Z'))
    # )
    
    if scope and 'All' not in scope:
        scope_addon = " where ("
        for each in scope:
            scope_addon += f"request_name='{each}' OR "
        scope_addon = scope_addon[0: -4] + ")"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
        
    expression_addon = scope_addon + status_addon
    
    response = client.select_object_content(bucket_name, file_name, expression_addon)
    
    data = {}
    for line in response:
        if not line.get('request_name'):
            continue
        if line['request_name'] not in data:
            data[line['request_name']] = {}
        # for _ in timestamps:
        #     results[req_name][_] = None
        data[line['request_name']][line['time']] = data[line['request_name']].get(line['time'], 0) + int(line[aggr])
    log.info('=====get_response_codes_analytics')

    return timestamps, data, users
