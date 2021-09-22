from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..utils.charts_utils import (requests_summary, requests_hits, avg_responses, summary_table, get_issues,
                                  get_data_from_influx)


class ReportChartsAPI(RestResource):
    get_rules = (
        dict(name="low_value", type=float, default=0, location="args"),
        dict(name="high_value", type=float, default=100, location="args"),
        dict(name="start_time", type=str, default="", location="args"),
        dict(name="end_time", type=str, default="", location="args"),
        dict(name="aggregator", type=str, default="auto", location="args"),
        dict(name="sampler", type=str, default="REQUEST", location="args"),
        dict(name="metric", type=str, default="", location="args"),
        dict(name="scope", type=str, default="", location="args"),
        dict(name="build_id", type=str, location="args"),
        dict(name="test_name", type=str, location="args"),
        dict(name="lg_type", type=str, location="args"),
        dict(name='status', type=str, default='all', location="args")
    )
    mapping = {
        "requests": {
            "summary": requests_summary,
            "hits": requests_hits,
            "average": avg_responses,
            "table": summary_table,
            "data": get_data_from_influx
        },
        "errors": {
            "table": get_issues
        }
    }

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, source: str, target: str):
        args = self._parser_get.parse_args(strict=False)
        return self.mapping[source][target](args)
