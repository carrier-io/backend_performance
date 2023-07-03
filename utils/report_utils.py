import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Tuple, Union, Optional, List
from pydantic import BaseModel, validator, ValidationError

from tools import data_tools, constants as c, MinioClient, rpc_tools

from pylon.core.tools import log

from ..models.baselines import Baseline
from ..models.reports import Report
# from influxdb.exceptions import InfluxDBClientError


def _create_dataset_for_users(timeline, data, scope, metric, axe):
    labels = []
    for _ in timeline:
        labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    datasets = []
    colors = data_tools.charts.color_gen(len(scope))
    for each, color in zip(scope, colors):
        datasets.append({
            "label": f"{each}_{metric}",
            "fill": False,
            "data": list(data.values()),
            "yAxisID": axe,
            "borderWidth": 2,
            "lineTension": 0,
            "spanGaps": True,
            "backgroundColor": "rgb({}, {}, {})".format(*color),
            "borderColor": "rgb({}, {}, {})".format(*color)
        })
    return {
        "labels": labels,
        "datasets": datasets
    }


# def _create_dataset(timeline, data, scope, metric, axe):
#     labels = []
#     for _ in timeline:
#         labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
#     datasets = []
#     colors = data_tools.charts.color_gen(len(data))
#     for each, color in zip(data, colors):
#         key = list(each.keys())[0]
#         datasets.append({
#             "label": f"{key}_{metric}",
#             "fill": False,
#             "data": list(each[key].values()),
#             "yAxisID": axe,
#             "borderWidth": 2,
#             "lineTension": 0,
#             "spanGaps": True,
#             "backgroundColor": "rgb({}, {}, {})".format(*color),
#             "borderColor": "rgb({}, {}, {})".format(*color)
#         })
#     return {
#         "labels": labels,
#         "datasets": datasets
#     }


def create_dataset(timeline, data, scope, metric, axe):
    labels = []
    for ts in timeline:
        labels.append(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    _data = {
        "labels": labels,
        "datasets": []
    }
    colors = data_tools.charts.color_gen(len(data))
    if metric == "Users":
        return _create_dataset_for_users(timeline, data['users'], scope, metric, axe)
    for key, color in zip(data, colors):
        dataset = {
            "label": f"{key}_{metric}",
            "fill": False,
            "data": [],
            "yAxisID": axe,
            "borderWidth": 2,
            "lineTension": 0,
            "spanGaps": True,
            "backgroundColor": "rgb({}, {}, {})".format(*color),
            "borderColor": "rgb({}, {}, {})".format(*color)
        }
        for _ in timeline:
            # todo: refactor - this is ridiculous
            dumb_fix = str(_).strip('Z') + 'Z'
            if dumb_fix in data[key]:
                dataset['data'].append(data[key][dumb_fix])
            else:
                dataset['data'].append(None)
        _data['datasets'].append(dataset)

    return _data


def comparison_data(timeline, data):
    labels = []
    for _ in timeline:
        labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    chart_data = {
        "labels": labels,
        "datasets": []
    }
    colors = data_tools.charts.color_gen(len(data))
    for record, color in zip(data, colors):
        dataset = {
            "label": record,
            "fill": False,
            "data": list(data[record][0].values()),
            "yAxisID": data[record][1],
            "borderWidth": 2,
            "lineTension": 0,
            "spanGaps": True,
            "backgroundColor": "rgb({}, {}, {})".format(*color),
            "borderColor": "rgb({}, {}, {})".format(*color)
        }
        chart_data["datasets"].append(dataset)
    return chart_data


def chart_data(timeline, users, other, yAxis="response_time", convert_time: bool = True) -> dict:
    if convert_time:
        labels = []
        try:
            for t in timeline:
                labels.append(datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
                # labels.append(t)
        except ValueError:
            labels = timeline
    else:
        labels = timeline
    _data = {
        "labels": labels,
        "datasets": []
    }
    if users:
        _data['datasets'].append({"label": "Active Users", "fill": False,
                                  "data": list(users['users'].values()),
                                  "yAxisID": "active_users", "pointRadius": 0,
                                  "borderColor": "rgb(94,114,228)",
                                  "borderWidth": 2, "lineTension": 0.1, "spanGaps": True})
    colors = data_tools.charts.color_gen(len(other.keys()))
    for each, color in zip(other, colors):
        dataset = {
            "label": each,
            "fill": False,
            "yAxisID": yAxis,
            "borderWidth": 1,
            "lineTension": 0.2,
            "pointRadius": 1,
            "spanGaps": True,
            "backgroundColor": "rgb({}, {}, {})".format(*color),
            "borderColor": "rgb({}, {}, {})".format(*color),
            "data": []
        }
        for _ in timeline:
            # todo: refactor - this is ridiculous
            dumb_fix = str(_).strip('Z') + 'Z'
            if dumb_fix in other[each]:
                dataset['data'].append(other[each][dumb_fix])
            else:
                dataset['data'].append(None)
        _data['datasets'].append(dataset)
    return _data


def render_analytics_control(requests: list) -> dict:
    item = {
        "Users": "getData('Users', '{}')",
        # "Hits": "getData('Hits', '{}')",
        "Throughput": "getData('Throughput', '{}')",
        "Errors": "getData('Errors', '{}')",
        "Min": "getData('Min', '{}')",
        "Median": "getData('Median', '{}')",
        "Max": "getData('Max', '{}')",
        "pct90": "getData('pct90', '{}')",
        "pct95": "getData('pct95', '{}')",
        "pct99": "getData('pct99', '{}')",
        "1xx": "getData('1xx', '{}')",
        "2xx": "getData('2xx', '{}')",
        "3xx": "getData('3xx', '{}')",
        "4xx": "getData('4xx', '{}')",
        "5xx": "getData('5xx', '{}')"
    }
    control = defaultdict(dict)
    for each in ["All", *requests]:
        for every in item:
            control[each][every] = item[every].format(each)
    return control


# def _check_equality(func, *, second_func=None):
#     log.info('calculate_proper_timeframe')
#     def wrapper(*args, **kwargs):
#         result = func(*args, **kwargs)
#         result2 = second_func(*args, **kwargs)
#         log.info(f'FUNCTIONS RETURN RESULTS {result} | {result2}')
#         log.info(f'RESULTS equal? {all(i == j for i, j in zip(result, result2))} | {list(i == j for i, j in zip(result, result2))}')
#         return result2
#     return wrapper

def calculate_proper_timeframe(build_id: str, test_name: str, lg_type: str, low_value: int, high_value: int,
                               start_time: datetime, end_time: datetime, aggregation: str,
                               time_as_ts: bool = False, source: str = None,
                               ) -> Union[Tuple[str, str, str], Tuple[int, int, str]]:
    start_time_ts = start_time.timestamp()
    end_time_ts = end_time.timestamp()

    interval = end_time_ts - start_time_ts
    start_shift = interval * (float(low_value) / 100.0)
    end_shift = interval * (float(high_value) / 100.0)

    end_time_ts = start_time_ts + end_shift
    start_time_ts += start_shift
    if time_as_ts:
        return int(start_time_ts), int(end_time_ts)

    t_format = "%Y-%m-%dT%H:%M:%SZ"
    _start_time = datetime.fromtimestamp(start_time_ts).strftime(t_format)
    _end_time = datetime.fromtimestamp(end_time_ts).strftime(t_format)
    return _start_time, _end_time
    # _start_time = datetime.utcfromtimestamp(start_time_ts).isoformat(sep=' ', timespec='seconds')
    # _end_time = datetime.utcfromtimestamp(end_time_ts).isoformat(sep=' ', timespec='seconds')
    # return _start_time, _end_time


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
    try:
        _parsed_args = TimeframeArgs.parse_obj(args)
    except ValidationError:
        return None, None
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


def delete_project_reports(project: Union['Project', int], report_ids: List[int]) -> None:
    if isinstance(project, int):
        project = rpc_tools.RpcMixin().rpc.call.project_get_or_404(
            project_id=project)

    # query only needed fields
    query_result = Report.query.with_entities(
        Report.build_id, Report.name, Report.lg_type, Report.test_config
    ).filter(
        Report.project_id == project.id,
        Report.id.in_(report_ids)
    ).all()

    minio_delete_build_ids = dict()
    for build_id, name, lg_type, test_config in query_result:
        # delete influx tables
        # try:
        #     InfluxConnector(build_id=build_id, test_name=name, lg_type=lg_type).delete_test_data()
        # except InfluxDBClientError as e:
        #     log.warning('InfluxDBClientError %s', e)

        # collect s3 data for deletion
        s3_settings = test_config.get(
            'integrations', {}).get('system', {}).get('s3_integration', {'integration_id': 1})
        if s3_settings:
            try:
                minio_delete_build_ids[s3_settings['integration_id']]['names'][name].add(build_id)
            except KeyError:
                minio_delete_build_ids[s3_settings['integration_id']] = {
                    'settings': s3_settings,
                    'names': defaultdict(set)
                }
                minio_delete_build_ids[s3_settings['integration_id']]['names'][name].add(build_id)

    # log.info('DEELEETE  %s', minio_delete_build_ids)
    # delete files from s3
    # tmp = []
    for i in minio_delete_build_ids.values():
        minio_client = MinioClient(project, **i['settings'])
        for test_name, build_ids in i['names'].items():
            bucket_name = str(test_name).replace("_", "").replace(" ", "").lower()
            patt = re.compile(r'|'.join(build_ids))
            minio_files = minio_client.list_files(bucket_name)
            files_to_delete = [
                {'Key': f['name']}
                for f in minio_files
                if re.search(patt, f['name'])
            ]
            minio_client.s3_client.delete_objects(
                Bucket=minio_client.format_bucket_name(bucket_name),
                Delete={'Objects': files_to_delete},
            )
            # tmp.append(dict(
            #     Bucket=minio_client.format_bucket_name(bucket_name),
            #     Delete={'Objects': files_to_delete},
            # ))
    # log.info('DELETE REPORT %s', tmp)

    # delete baselines
    Baseline.query.filter(
        Baseline.project_id == project.id,
        Baseline.report_id.in_(report_ids)
    ).delete()
    Baseline.commit()

    # delete reports
    Report.query.filter(
        Report.project_id == project.id,
        Report.id.in_(report_ids)
    ).delete()
    Report.commit()
