import requests

from pylon.core.tools import log
from tools import constants as c

from ..utils.charts_utils import timeframe


class LokiConnector():
    
    def __init__(self, **args) -> None:
        self.test_name = args['test_name']
        self.query_range_url = f"{c.LOKI_HOST}/loki/api/v1/query_range"
        self.start_time, self.end_time = timeframe(args, time_as_ts=True)


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
