from datetime import datetime, timezone
from typing import Callable, Optional, Generator, Union

from pydantic import BaseModel, validator
from .utils import str_to_timestamp
from ..models.reports import Report

from .report_utils import (
    calculate_proper_timeframe, chart_data, create_dataset, comparison_data
)
from pylon.core.tools import log

from tools import data_tools


class TimeframeArgs(BaseModel):
    start_time: datetime
    end_time: Optional[datetime]
    low_value: Union[int, float, str, None] = 0
    high_value: Union[int, float, str, None] = 100
    test_name: str
    build_id: Optional[str]
    lg_type: Optional[str]
    aggregation: Optional[str] = 'auto'
    source: Optional[str] = 'influx'

    @validator('end_time', pre=True)
    def clear_null(cls, value):
        if value == 'null':
            return
        return value

    @validator('end_time', always=True)
    def set_end_time(cls, value, values: dict):
        if not value:
            values['high_value'] = 100
            return datetime.utcnow()
        return value

    @validator('start_time', 'end_time')
    def ensure_tz(cls, value: datetime):
        if value.tzinfo:
            return value.astimezone(timezone.utc)
        return value.replace(tzinfo=timezone.utc)

    @validator('low_value', 'high_value')
    def convert(cls, value, values, field):
        try:
            return int(value)
        except TypeError:
            return field.default

    class Config:
        fields = {
            'aggregator': 'aggregation'
        }


def timeframe(args: dict, time_as_ts: bool = False) -> tuple:
    log.info(f"timeframe args {args}")
    _parsed_args = TimeframeArgs.parse_obj(args)
    # end_time = args.get('end_time')
    # high_value = args.get('high_value', 100)
    # if not end_time or end_time == 'null':
    #     end_time = datetime.utcnow()
    #     high_value = 100
    # return calculate_proper_timeframe(args.get('build_id', None), args['test_name'], args.get('lg_type', None),
    #                                   args.get('low_value', 0),
    #                                   high_value, args['start_time'], end_time, args.get('aggregator', 'auto'),
    #                                   time_as_ts=time_as_ts)
    return calculate_proper_timeframe(**_parsed_args.dict(), time_as_ts=time_as_ts)


# def _query_only(args: dict, query_func: Callable, connector) -> dict:
#     # start_time, end_time, aggregation = _timeframe(args, connector)
#     timeline, results, users = query_func(
#         # start_time, end_time, aggregation,
#         # sampler=args['sampler'], status=args["status"]
#     )
#     return chart_data(timeline, users, results, convert_time=args.get('convert_time', True))


def get_tests_metadata(tests):
    tests_meta = Report.query.filter(Report.id.in_(tests)).order_by(Report.id.asc()).all()
    users_data = {}
    responses_data = {}
    errors_data = {}
    rps_data = {}
    labels = []

    for each in tests_meta:
        ts = datetime.fromtimestamp(str_to_timestamp(each.start_time),
                                    tz=timezone.utc).strftime("%m-%d %H:%M:%S")
        labels.append(ts)
        users_data[ts] = each.vusers
        responses_data[ts] = each.pct95
        errors_data[ts] = each.failures
        rps_data[ts] = each.throughput
    return labels, rps_data, errors_data, users_data, responses_data


def requests_summary(args: dict, connector):
    # args['convert_time'] = False
    timeline, results, users = connector.get_requests_summary_data()
    return chart_data(timeline, users, results, convert_time=False)


def requests_hits(args: dict, connector):
    # args['convert_time'] = False
    timeline, results, users = connector.get_tps()
    return chart_data(timeline, users, results, convert_time=False)


def avg_responses(args: dict, connector):
    # args['convert_time'] = False
    timeline, results, users = connector.get_average_responses()
    return chart_data(timeline, users, results, convert_time=False)


def summary_table(args: dict, connector):
    return connector.get_build_data()
    # start_time, end_time = timeframe(args)
    # return get_build_data(args['build_id'], args['test_name'], args['lg_type'], start_time, end_time, args['sampler'])


def get_issues(args: dict, connector):
    return connector.get_issues()


def get_data_for_analytics(args, connector):
    metric = args.get('metric', '')
    scope = args.get("scope[]", [])
    axe = 'count'
    data, axe, timestamps = connector.calculate_analytics(scope, metric)      
    if data:
        return create_dataset(timestamps, data, scope, metric, axe)
    return {}
    


# def prepare_comparison_responses(args):
#     log.info('prepare_comparison_responses %s', args)
#     tests = args['id[]']
#     tests_meta = []
#     longest_test = 0
#     longest_time = 0
#     sampler = args.get('sampler', "REQUEST")
#     for i in range(len(tests)):
#         data = Report.query.filter_by(id=tests[i]).first().to_json()
#         if data['duration'] > longest_time:
#             longest_time = data['duration']
#             longest_test = i
#         tests_meta.append(data)
#     log.info(f"prepare_comparison_responses {tests_meta[longest_test]}")
#     _parsed_args = TimeframeArgs(**args, **tests_meta[longest_test])
#     start_time, end_time, aggregation = calculate_proper_timeframe(**_parsed_args.dict())
#     # start_time, end_time, aggregation = calculate_proper_timeframe(tests_meta[longest_test]['build_id'],
#     #                                                                tests_meta[longest_test]['name'],
#     #                                                                tests_meta[longest_test]['lg_type'],
#     #                                                                args.get('low_value', 0),
#     #                                                                args.get('high_value', 100),
#     #                                                                tests_meta[longest_test]['start_time'],
#     #                                                                tests_meta[longest_test]['end_time'],
#     #                                                                args.get('aggregator', 'auto'))
#     # if args.get('aggregator', 'auto') != "auto":
#     #     aggregation = args.get('aggregator')
#     metric = args.get('metric', '')
#     scope = args.get('scope', '')
#     status = args.get("status", 'all')
#     timestamps, users = get_backend_users(tests_meta[longest_test]['build_id'],
#                                           tests_meta[longest_test]['lg_type'], start_time, end_time, aggregation)
#     test_start_time = "{}_{}".format(tests_meta[longest_test]['start_time'].replace("T", " ").split(".")[0], metric)
#     data = {test_start_time: calculate_analytics_dataset(tests_meta[longest_test]['build_id'],
#                                                          tests_meta[longest_test]['name'],
#                                                          tests_meta[longest_test]['lg_type'],
#                                                          start_time, end_time, aggregation,
#                                                          sampler, scope, metric, status)}
#     for i in range(len(tests_meta)):
#         if i != longest_test:
#             test_start_time = "{}_{}".format(tests_meta[i]['start_time'].replace("T", " ").split(".")[0], metric)
#             data[test_start_time] = calculate_analytics_dataset(tests_meta[i]['build_id'], tests_meta[i]['name'],
#                                                                 tests_meta[i]['lg_type'],
#                                                                 tests_meta[i]['start_time'],
#                                                                 tests_meta[i]['end_time'],
#                                                                 aggregation, sampler, scope, metric, status)
#     return comparison_data(timeline=timestamps, data=data)


# def compare_tests(args):
#     labels, rps_data, errors_data, users_data, responses_data = get_tests_metadata(args['id[]'])
#     return {
#         "response": chart_data(labels, {"users": users_data}, {"pct95": responses_data}, "time"),
#         "errors": chart_data(labels, {"users": users_data}, {"errors": errors_data}, "count"),
#         "rps": chart_data(labels, {"users": users_data}, {"RPS": rps_data}, "count")
#     }


# def create_benchmark_dataset(args):
#     build_ids = args['id[]']
#     req = args.get('request')
#     calculation = args.get('calculation')
#     aggregator = args.get('aggregator')
#     status = args.get("status", 'all')
#     if not aggregator or aggregator == 'auto':
#         aggregator = '1s'
#     tests_meta = Report.query.filter(Report.id.in_(build_ids)).order_by(Report.vusers.asc()).all()
#     labels = set()
#     data = {}
#     y_axis = ''
#     for _ in tests_meta:
#         try:
#             labels.add(_.vusers)
#             if _.environment not in data:
#                 data[_.environment] = {}
#             if calculation == 'throughput':
#                 y_axis = 'Requests per second'
#                 data[_.environment][str(_.vusers)] = get_throughput_per_test(
#                     _.build_id, _.name, _.lg_type, "", req, aggregator, status)
#             elif calculation != ['throughput']:
#                 y_axis = 'Response time, ms'
#                 if calculation == 'errors':
#                     y_axis = 'Errors'
#                 data[_.environment][str(_.vusers)] = get_response_time_per_test(
#                     _.build_id, _.name, _.lg_type, "", req, calculation, status, aggregator)
#             else:
#                 data[_.environment][str(_.vusers)] = None
#         except IndexError:
#             pass
#
#     labels = [""] + sorted(list(labels)) + [""]
#     return {"data": chart_data(labels, [], data, "data"), "label": y_axis}


def engine_health(args: dict, connector, part: str = 'all') -> dict:
    part_mapping = {
        'cpu': engine_health_cpu,
        'memory': engine_health_memory,
        'load': engine_health_load,
    }
    func = part_mapping.get(part)
    if not func:  # e.g. part == 'all'
        return {k: v(connector) for k, v in part_mapping.items()}
    return func(connector)


def generate_engine_health_dataset(host_name: str, series_data: list, data_structure: dict,
                                   palette: Optional[Generator] = None):
    for section, options in data_structure.items():
        dataset = {
            'data': list(map(lambda x: x[section], series_data)),
            # 'label': f'{section}:{host_name}',
            'label': section,
            'borderWidth': 2,
            'fill': False,
            'lineTension': 0.1,
            'pointRadius': 1,
            'spanGaps': True,
            'tag_host': host_name,
        }
        if palette:
            try:
                dataset['borderColor'] = 'rgb({}, {}, {})'.format(*next(palette))
            except StopIteration:
                dataset['borderColor'] = '#ffffff'
        dataset.update(options)
        yield dataset


def format_engine_health_data(health_data: dict, data_structure: dict) -> dict:
    datasets = []
    labels = []
    palette = data_tools.charts.color_gen(len(health_data.keys()) * len(data_structure.keys()))
    for host, series in health_data.items():
        if not labels:
            labels = list(map(lambda x: x['time'], series))

        datasets.extend(generate_engine_health_dataset(host, series, data_structure, palette))

    return {
        'datasets': datasets,
        'labels': labels,
        'hosts': list(health_data.keys()),
    }


def engine_health_cpu(connector) -> dict:
    health_data = connector.get_engine_health_cpu()
    structure = {
        'system': {
            'hidden': True
        },
        'user': {},
        'softirq': {
            'hidden': True
        },
        'iowait': {
            'hidden': True
        },
    }
    return format_engine_health_data(health_data, structure)


def engine_health_memory(connector) -> dict:
    health_data = connector.get_engine_health_memory()
    structure = {
        'heap memory': {},
        'non-heap memory': {},
    }
    return format_engine_health_data(health_data, structure)


def engine_health_load(connector) -> dict:
    health_data = connector.get_engine_health_load()
    structure = {
        'load1': {},
        'load5': {},
        'load15': {},
    }
    return format_engine_health_data(health_data, structure)
