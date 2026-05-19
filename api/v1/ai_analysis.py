from tools import MinioClient, auth, api_tools, VaultClient, TaskManager
from pylon.core.tools import log
from traceback import format_exc
import json
from flask import request
from ...models.reports import Report


class ProjectAPI(api_tools.APIModeHandler):

    def post(self, project_id: int, report_id: int, **kwargs):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        task_manager = TaskManager(project_id)
        tasks = task_manager.list_tasks()
        args = request.json
        if args["include_trend"] != "true":
            task_name = "bp_ai_analysis"
            task_id = None
            llm_parser_task = None
            queue_name = None
            for task in tasks:
                if task_name == task.task_name:
                    task_id = task.task_id
                    queue_name = task.region
                    llm_parser_task = task
            if not task_id:
                return {"status": f"{task_name} task not found for the project"}, 404
            env_vars = json.loads(llm_parser_task.env_vars)
            event = [{row['name']: row['default'] for row in env_vars.get("task_parameters")}]
            event[0]["report_id"] = report_id
            event[0]["project_id"] = project_id
            event[0]["token"] = "{{secret.auth_token}}"
            event[0]["url"] = "{{secret.galloper_url}}"
            event[0]["api_token"] = "{{secret.llm_api_token}}"
            event[0]["smtp_email_recipients"] = args["email_list"]
            event[0]["store_report"] = args["store_report"]
            task_manager.run_task(event, task_id=task_id, queue_name=queue_name)
            return {"status": f"{task_name} single report task started", "args": f"{args}"}, 200
        else:
            task_name = "email_integration"
            task_id = None
            llm_parser_task = None
            queue_name = None
            for task in tasks:
                if task.project_id == project_id and task_name in task.task_name and "dial_token" in task.env_vars:
                    task_id = task.task_id
                    queue_name = task.region
                    llm_parser_task = task.to_json()
            if not task_id:
                return {"status": f"{task_name} task not found for the project or dial_token not set for the task"}, 404

            report = Report.query.filter(
                Report.project_id == project_id,
                Report.id == report_id
            ).first_or_404().to_json()
            event = {}
            try:
                task_env_vars = json.loads(llm_parser_task["env_vars"])
                reasons_to_fail_report = report["test_status"]["description"].split(";")
                status = report["test_status"]["status"]
                test_data = {"throughput": report["throughput"], "ko": report["failures"],
                             "total": report["total"], "request_name": "all", "min": report["min"],
                             "max": report["max"], "avg": report["mean"], "pct50": report["pct50"],
                             "pct75": report["pct75"], "pct90": report["pct90"], "pct95": report["pct95"],
                             "pct99": report["pct99"]}
                try:
                    quality_gate_config = report["test_config"]["integrations"]["processing"]["quality_gate"]
                except:
                    quality_gate_config = {}
                event = {
                    "galloper_url": "{{secret.galloper_url}}",
                    "token": "{{secret.auth_token}}",
                    "project_id": project_id,
                    "influx_host": "{{secret.influx_ip}}",
                    "influx_port": "{{secret.influx_port}}",
                    "influx_user": "{{secret.influx_user}}",
                    "influx_password": "{{secret.influx_password}}",
                    "influx_db": "{{secret.gatling_db}}",
                    "comparison_db": "{{secret.comparison_db}}",
                    "user_list": args["email_list"].split(","),
                    "notification_type": "api",
                    "test": report['name'],
                    "test_type": report['type'],
                    "env": report['environment'],
                    "users": report['vusers'],
                    "smtp_host": task_env_vars["host"],
                    "smtp_port": task_env_vars["port"],
                    "smtp_user": task_env_vars["user"],
                    "smtp_sender": task_env_vars["sender"],
                    "smtp_password": task_env_vars["passwd"]["value"],
                    "performance_degradation_rate": 0,
                    "missed_threshold_rate": 0,
                    "reasons_to_fail_report": reasons_to_fail_report,
                    "status": status,
                    "test_data": test_data,
                    "quality_gate_config": quality_gate_config
                }
            except Exception as e:
                log.info("***************************************")
                log.info(e)
                log.info(format_exc())
                log.info("***************************************")
                return {"status": f"failed to start task. {e}", "args": f"{args}"}, 200
            task_manager.run_task(event, task_id=task_id, queue_name=queue_name)
            return {"status": f"{task_name} AI analysis with trend report task started", "args": f"{args}"}, 200




class API(api_tools.APIBase):
    url_params = [
        '<int:project_id>/<int:report_id>',
        '<string:mode>/<int:project_id>/<int:report_id>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        # 'administration': AdminAPI,
    }