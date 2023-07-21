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
from typing import Optional

import requests

from pylon.core.tools import log
from tools import LokiLogFetcher

from ..utils.report_utils import timeframe


class LokiConnector:
    
    def __init__(self, *, test_name: str, project_id: Optional[int] = None, **kwargs) -> None:
        self.test_name = test_name
        self.query_range_url = LokiLogFetcher.make_url(project_id)  # todo: here we should consider making url from project
        kwargs['test_name'] = self.test_name
        self.start_time, self.end_time = timeframe(kwargs, time_as_ts=True)

    def get_issues(self) -> list:
        data = {
            "direction": "BACKWARD",
            "limit": 5000,
            "query": '{filename="/tmp/' + self.test_name + '.log"}',
            "start": self.start_time,
            "end": self.end_time
        }

        resp = requests.get(url=self.query_range_url,
                            params=data, 
                            headers={"Content-Type": "application/json"}
                            ).json()

        issues = {}
        for result in resp["data"]["result"]:
            for value in result['values']:
                _values = value[1].strip().split("\t")
                _issue = {"count": 1}
                for each in _values:
                    if ":" in each:
                        key, value = each[:each.index(':')], each[each.index(':')+1:].strip()
                        if key == 'Error key' and value in issues:
                            issues[value]["count"] += 1
                            continue
                        _issue[key] = value
                if 'Error key' in _issue and _issue['Error key'] not in issues.keys():
                    issues[_issue['Error key']] = _issue
                    
        return list(issues.values())
