from flask import request, make_response
from flask_restful import Resource
from ...utils.charts_utils import (requests_summary, requests_hits, avg_responses, summary_table, get_issues,
                                                                  get_data_from_influx)


class API(Resource):
    url_params = [
        '<string:source>/<string:target>',
    ]

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

    def __init__(self, module):
        self.module = module

    def get(self, source: str, target: str):
        args = request.args
        return self.mapping[source][target](args)
