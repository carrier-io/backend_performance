from json import loads
from sqlalchemy import and_
from copy import deepcopy

from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import str2bool, build_req_parser
from ..models.api_tests import ApiTests
from ..models.api_reports import APIReport
from ..utils.utils import exec_test, get_backend_test_data


class TestApiBackend(RestResource):
    _get_rules = (
        dict(name="raw", type=int, default=0, location="args"),
        dict(name="type", type=str, default='cc', location="args"),
        dict(name="exec", type=str2bool, default=False, location="args")
    )

    _put_rules = (
        dict(name="parallel", type=int, required=False, location='json'),
        dict(name="region", type=str, required=False, location='json'),
        dict(name="params", type=str, default="[]", required=False, location='json'),
        dict(name="env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="customization", type=str, default="{}", required=False, location='json'),
        dict(name="cc_env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="reporter", type=list, required=False, location='json'),
        dict(name="emails", type=str, required=False, location='json'),
        dict(name="git", type=str, required=False, location='json'),
    )

    _post_rules = _put_rules + (
        dict(name="test_type", type=str, required=False, location='json'),
        dict(name="runner", type=str, required=False, location='json'),
        dict(name="type", type=str, default=None, required=False, location='json')
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.put_parser = build_req_parser(rules=self._put_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id, test_id):
        args = self.get_parser.parse_args(strict=False)
        project = self.rpc.project_get_or_404(project_id=project_id)
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        test = ApiTests.query.filter(_filter).first()
        if args.raw:
            return test.to_json(["influx.port", "influx.host", "galloper_url",
                                 "influx.db", "comparison_db", "telegraf_db",
                                 "loki_host", "loki_port", "influx.username", "influx.password"])
        if args["type"] == "docker":
            message = test.configure_execution_json(args.get("type"), execution=args.get("exec"))
        else:
            message = [{"test_id": test.test_uid}]
        return {"config": message}  # this is cc format

    def put(self, project_id, test_id):
        default_params = ["influx.port", "influx.host", "galloper_url", "influx.db", "comparison_db", "telegraf_db",
                          "loki_host", "loki_port", "test.type", "test_type", "influx.username", "influx.password"]
        project = self.rpc.project_get_or_404(project_id=project_id)
        args = self.put_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        task = ApiTests.query.filter(_filter).first()

        for each in ["params", "env_vars", "customization", "cc_env_vars"]:
            params = deepcopy(getattr(task, each))
            for key in list(params.keys()):
                if key not in loads(args.get(each)).keys() and key not in default_params:
                    del params[key]
            for key, value in loads(args.get(each)).items():
                if key not in params or params[key] != value:
                    params[key] = value
            setattr(task, each, params)

        if args.get("reporter"):
            task.reporting = args["reporter"]
        else:
            task.reporting = []

        if args.get("emails"):
            task.emails = args["emails"]
        else:
            task.emails = ""

        if args.get("parallel"):
            task.parallel = args.get("parallel")
        if args.get("region"):
            task.region = args.get("region")
        if args.get("git"):
            task.git = loads(args.get("git"))
        task.commit()
        return task.to_json(["influx.port", "influx.host", "galloper_url",
                             "influx.db", "comparison_db", "telegraf_db",
                             "loki_host", "loki_port", "influx.username", "influx.password"])

    def post(self, project_id, test_id):
        project = self.rpc.project_get_or_404(project_id=project_id)
        args = self.post_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(ApiTests.project_id == project.id, ApiTests.id == test_id)
        else:
            _filter = and_(ApiTests.project_id == project.id, ApiTests.test_uid == test_id)
        task = ApiTests.query.filter(_filter).first()
        event = list()
        execution = True if args['type'] and args["type"] == "config" else False
        event.append(task.configure_execution_json(output='cc',
                                                   test_type=args.get("test_type"),
                                                   params=loads(args.get("params", None)),
                                                   env_vars=loads(args.get("env_vars", None)),
                                                   reporting=args.get("reporter", None),
                                                   customization=loads(args.get("customization", None)),
                                                   cc_env_vars=loads(args.get("cc_env_vars", None)),
                                                   parallel=args.get("parallel", None),
                                                   region=args.get("region", "default"),
                                                   execution=execution, emails=args.get("emails", None)))
        if args['type'] and args["type"] == "config":
            return event[0]
        for each in event:
            each["test_id"] = task.test_uid

        test_data = get_backend_test_data(event[0])
        report = APIReport(name=test_data["test_name"],
                           project_id=project.id,
                           environment=test_data["environment"],
                           type=test_data["type"],
                           end_time="",
                           start_time=test_data["start_time"],
                           failures=0,
                           total=0,
                           thresholds_missed=0,
                           throughput=0,
                           vusers=test_data["vusers"],
                           pct50=0,
                           pct75=0,
                           pct90=0,
                           pct95=0,
                           pct99=0,
                           _max=0,
                           _min=0,
                           mean=0,
                           duration=test_data["duration"],
                           build_id=test_data["build_id"],
                           lg_type=test_data["lg_type"],
                           onexx=0,
                           twoxx=0,
                           threexx=0,
                           fourxx=0,
                           fivexx=0,
                           requests="",
                           test_uid=task.test_uid)
        report.insert()
        event[0]["cc_env_vars"]["REPORT_ID"] = str(report.id)
        event[0]["cc_env_vars"]["build_id"] = test_data["build_id"]
        response = exec_test(project.id, event)
        response["redirect"] = f'/task/{response["task_id"]}/results'
        return response
