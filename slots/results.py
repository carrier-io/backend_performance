from pylon.core.tools import web, log  # pylint: disable=E0611,E0401
from tools import auth, theme  # pylint: disable=E0401
from ..connectors.minio_connector import MinioConnector
from ..connectors.influx_connector import InfluxConnector
from ..models.reports import Report
from ..utils.report_utils import render_analytics_control


def _get_connector(test_data):
    test_status = Report.query.with_entities(Report.test_status).filter(
        Report.build_id == test_data['build_id']
        ).first()[0]['status'].lower()
    if test_status in ('finished', 'error', 'failed', 'success'):
        log.info('Using MinioConnector in slot')
        return MinioConnector(build_id=test_data["build_id"], 
                              test_name=test_data["name"])
    else:
        log.info('Using InfluxConnector in slot')
        return InfluxConnector(build_id=test_data["build_id"], 
                               test_name=test_data["name"], 
                               lg_type=test_data["lg_type"])


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('results_content')
    @auth.decorators.check_slot({
        "permissions": ["performance.backend_results"]
    })
    def content(self, context, slot, payload):
        result_id = payload.request.args.get('result_id')
        if result_id:
            report = Report.query.get_or_404(result_id)
            test_data = report.to_json()
            test_data["is_baseline_report"] = report.is_baseline_report
            try:
                test_data["failure_rate"] = round((test_data["failures"] / test_data["total"]) * 100, 2)
            except:
                test_data["failure_rate"] = 0
                
            connector = _get_connector(test_data)
            test_data["samplers"] = connector.get_sampler_types()
            test_data["aggregations"] = connector.get_aggregations_list()
            
            analytics_control = render_analytics_control(test_data["requests"])

            with context.app.app_context():
                return self.descriptor.render_template(
                    'results/content.html',
                    test_data=test_data,
                    analytics_control=analytics_control
                )
        return theme.empty_content

    @web.slot('results_scripts')
    def scripts(self, context, slot, payload):
        # log.info('slot: [%s], payload: %s', slot, payload)
        result_id = payload.request.args.get('result_id')
        source_data = {}
        if result_id:
            test_data = Report.query.get_or_404(result_id).to_json()
            source_data = test_data['test_config'].get('source')
            analytics_control = render_analytics_control(test_data["requests"])

        with context.app.app_context():
            return self.descriptor.render_template(
                'results/scripts.html',
                source_data=source_data,
                test_data=test_data,
                analytics_control=analytics_control,
            )

    @web.slot('results_styles')
    def styles(self, context, slot, payload):
        # log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'results/styles.html',
            )
