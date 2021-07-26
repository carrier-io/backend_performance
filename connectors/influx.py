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


from ...projects.connectors.influx import get_client
from ...shared.constants import str_to_timestamp
from ..models.api_reports import APIReport


def get_project_id(build_id):
    return APIReport.query.filter_by(build_id=build_id).first().to_json()["project_id"]


def get_aggregated_test_results(test, build_id):
    project_id = get_project_id(build_id)
    query = f"SELECT * from api_comparison where simulation='{test}' and build_id='{build_id}'"
    return list(get_client(project_id, f'comparison_{project_id}').query(query))


def delete_test_data(build_id, test_name, lg_type):
    project_id = get_project_id(build_id)
    query_one = f"DELETE from {test_name} where build_id='{build_id}'"
    query_two = f"DELETE from api_comparison where build_id='{build_id}'"
    client = get_client(project_id, f"{lg_type}_{project_id}")
    client.query(query_one)
    client.close()
    client = get_client(project_id, f'comparison_{project_id}')
    client.query(query_two)
    client.close()
    return True


def get_test_details(project_id, build_id, test_name, lg_type):
    test = {
        "start_time": 0,
        "name": test_name,
        "environment": "",
        "type": "",
        "end_time": 0,
        "failures": 0,
        "total": 0,
        "thresholds_missed": 0,
        "throughput": 0,
        "vusers": 0,
        "duration": 0,
        "1xx": 0,
        "2xx": 0,
        "3xx": 0,
        "4xx": 0,
        "5xx": 0,
        "build_id": build_id,
        "lg_type": lg_type,
        "requests": []
    }
    q_start_time = f"select time, active from {lg_type}_{project_id}..\"users\" " \
                   f"where build_id='{build_id}' order by time asc limit 1"
    q_end_time = f"select time, active from {lg_type}_{project_id}..\"users\" " \
                 f"where build_id='{build_id}' order by time desc limit 1"
    q_response_codes = f"select \"1xx\", \"2xx\", \"3xx\", \"4xx\", \"5xx\", \"ko\" as KO, " \
                       f"\"total\" as Total, \"throughput\" from comparison_{project_id}..api_comparison " \
                       f"where build_id='{build_id}' and request_name='All'"
    q_total_users = f"show tag values on comparison_{project_id} with key=\"users\" where build_id='{build_id}'"
    q_env = f"show tag values on comparison_{project_id} with key=\"env\" where build_id='{build_id}'"
    q_type = f"show tag values on comparison_{project_id} with key=\"test_type\" where build_id='{build_id}'"
    q_requests_name = f"show tag values on comparison_{project_id} with key=\"request_name\" " \
                      f"where build_id='{build_id}'"
    client = get_client(project_id)
    test["start_time"] = list(client.query(q_start_time)["users"])[0]["time"]
    test["end_time"] = list(client.query(q_end_time)["users"])[0]["time"]
    test["duration"] = round(str_to_timestamp(test["end_time"]) - str_to_timestamp(test["start_time"]), 1)
    test["vusers"] = list(client.query(q_total_users)["api_comparison"])[0]["value"]
    test["environment"] = list(client.query(q_env)["api_comparison"])[0]["value"]
    test["type"] = list(client.query(q_type)["api_comparison"])[0]["value"]
    test["requests"] = [name["value"] for name in client.query(q_requests_name)["api_comparison"]]
    response_data = list(client.query(q_response_codes)['api_comparison'])[0]
    test['total'] = response_data['Total']
    test['failures'] = response_data['KO']
    test['throughput'] = round(response_data['throughput'], 1)
    test['1xx'] = response_data['1xx']
    test['2xx'] = response_data['2xx']
    test['3xx'] = response_data['3xx']
    test['4xx'] = response_data['4xx']
    test['5xx'] = response_data['5xx']
    return test


