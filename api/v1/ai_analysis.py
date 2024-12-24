from tools import MinioClient, auth, api_tools, VaultClient, TaskManager
from pylon.core.tools import log
from traceback import format_exc
import json
from flask import request


class ProjectAPI(api_tools.APIModeHandler):

    def post(self, project_id: int, report_id: int, **kwargs):
        task_name = "bp_ai_analysis"
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        args = request.json
        task_manager = TaskManager(project_id)
        tasks = task_manager.list_tasks()
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
        return {"status": f"{task_name} task started"}, 200

#
#     def get(self, project_id: int, report_id: int, **kwargs):
#         project = self.module.context.rpc_manager.call.project_get_or_404(
#             project_id=project_id)
#         vc = VaultClient(project)
#         secrets = vc.get_all_secrets()
#         try:
#             integration_uid = int(secrets['backend_performance_integration_uid'])
#         except KeyError:
#             log.critical('backend_performance_integration_uid secret not set!')
#             return {'error': 'backend_performance_integration_uid secret not set'}, 404
#
#         integration = self.module.context.rpc_manager.call.integrations_get_by_uid(integration_uid, project_id)
#         if integration is None:
#             raise Exception(
#                 f"Integration is not found when project_id={project_id}, integration_uid={integration_uid}"
#             )
#
#         model_settings = {
#             "api_token": integration.settings["api_token"],
#             "model_name": integration.settings["model_name"],
#             "temperature": 0.2,
#             "max_tokens": 1024,
#             "top_p": 0.8,
#         }
#
#         report = Report.query.filter(*[Report.project_id == project_id, Report.id == report_id]).first()
#         args = {"build_id": report.build_id, "test_name": report.name, "lg_type": report.lg_type,
#                 "project_id": report.project_id, "start_time": report.start_time, "end_time": report.end_time,
#                 "aggregator": "1s", "sampler": "REQUEST"}
#         s3_config = {
#             's3_config': report.test_config.get("integrations").get('system', {}).get('s3_integration', {})
#         }
#         args.update(s3_config)
#         requests_summary = self.module.context.rpc_manager.call.get_requests_summary(args)
#         request_data = {}
#         for record in requests_summary.get("datasets"):
#             if record.get("label") != "Active Users":
#                 request_data[record.get("label")] = record.get("data")
#         results = []
#         variables = {"stddev": "3", "threshold": "300ms"}
#         _context = "Act as a performance analyst\nBehavior of particular request presented in JSON below, response time is in data key and name is in label.  Please see if there anomalies with response times for this request\n\nUse {{ stddev }} std.dev for calculation of anomalies\nResponse time should be less then {{ threshold }} for request "
#         _examples = [{
#             "input": '{"NEW_Step2_GET": [158,157,176,156,153,154,152,151,167,155,152,156,165,151,151,154,187,211,154,158,151,150,153,151,152,168,150,167,191,174,195,152,151,224,153,157,153,157,151,159,166,166,169,176,158,150,151,151,167,163,152,161,163,162,162,162,169,162,196,207,154,151,155,155,161,150,155,165,153,161,149,160,162,158,157,166,226,152,146,154,152,152,168,161,172,176,158,151,163,152,159,152,150,155,159,178,153,158,162,158,167,151,177,150,154,156,158,155,155,166,159,175,149,178,164,171,152,170,149,151,147,155,168,153,152,150,159,168,164,153,152,151,153,151,149,157,156,153,164,152,158,158,151,155,null]}',
#             "output": '{"Mean Response Time": 161.26, "Standard Deviation": 15.22, "Threshold for Anomalies": "3 * 15.22 ≈ 45.66", "Threshold for Expected Response Time": 200,"Anomalies": [211, 224, 207, 226]}'
#         }]
#         for key, value in request_data.items():
#             value = [x for x in value if x]
#             predict_input = json.dumps({key: value})
#             try:
#                 text_prompt = self.module.context.rpc_manager.call.prompts_prepare_text_prompt(
#                     project_id, None, predict_input, _context, _examples, variables
#                 )
#             except Exception as e:
#                 log.info(e)
#                 log.info(str(format_exc()))
#                 return str(e), 400
#             result = self.module.context.rpc_manager.call.prompts_predict(project_id, integration, model_settings,
#                                                                           text_prompt)
#             results.append(result["response"])
#
#         table_summary = self.module.context.rpc_manager.call.get_table_summary(args)
#         variables = {"request_based_summary": "\n".join(results), "data_table_summary": json.dumps(table_summary)}
#         context = "Act as a performance analyst. Using two different summorizations of individual request summarize " \
#                   "the overall test run. \n\n Summary1: {{ request_based_summary }} \n\n " \
#                   "Summary2: {{ data_table_summary }} . Include short (1-2 sentances) overview," \
#                   " then 5-7 list items Highlight sections, following list of 3 major points of interests and closing" \
#                   " with Summary section with 3 sentances"
#
#         __input = ""
#         try:
#             text_prompt = self.module.context.rpc_manager.call.prompts_prepare_text_prompt(
#                 project_id=project_id, prompt_id=None, input_=__input, context=context, variables=variables
#             )
#         except Exception as e:
#             log.info(e)
#             log.info(str(format_exc()))
#             return str(e), 400
#         summary = self.module.context.rpc_manager.call.prompts_predict(project_id, integration, model_settings,
#                                                                       text_prompt)
#
#         if not summary['ok']:
#             return {"summary": f"AI failed to analyse the report {summary['error']}"}, 400
#
#         write_ai_summary_to_minio_bucket(report, summary["response"])
#
#         return {"summary": summary}, 200
#
#
# def write_ai_summary_to_minio_bucket(report: Report, result: str) -> str:
#     build_id = report.build_id
#     report_id = report.id
#     test_name = report.name
#
#     enc = 'utf-8'
#     file_output = BytesIO()
#     file_output.write(f'Test {test_name} (id={report_id}) AI summary:\n {result}'.encode(enc))
#     file_output.seek(0)
#     try:
#         s3_settings = report.test_config.get(
#             'integrations', {}).get('system', {}).get('s3_integration', {})
#         minio_client = MinioClient.from_project_id(report.project_id, **s3_settings)
#         bucket_name = str(test_name).replace("_", "").replace(" ", "").lower()
#         if bucket_name not in minio_client.list_bucket():
#             minio_client.create_bucket(bucket=bucket_name, bucket_type='autogenerated')
#         file_name = f"{build_id}_AI_summary.log"
#         minio_client.upload_file(bucket_name, file_output, file_name)
#         return file_name
#     except:
#         log.warning('Failed to store AI summary results %s', format_exc())
#

class API(api_tools.APIBase):
    url_params = [
        '<int:project_id>/<int:report_id>',
        '<string:mode>/<int:project_id>/<int:report_id>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        # 'administration': AdminAPI,
    }
