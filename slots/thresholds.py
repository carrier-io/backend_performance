from pylon.core.tools import web, log  # pylint: disable=E0611,E0401
from ..models.api_reports import APIReport
from tools import session_project


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('thresholds_content')
    def content(self, context, slot, payload):
        tests = APIReport.query.filter(APIReport.project_id == session_project.get()).with_entities(
            APIReport.name).distinct()
        tests = [each[0] for each in tests]
        with context.app.app_context():
            return self.descriptor.render_template(
                'thresholds/content.html',
                tests=tests
            )

    @web.slot('thresholds_scripts')
    def scripts(self, context, slot, payload):
        from pylon.core.tools import log
        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'thresholds/scripts.html',
            )

    @web.slot('thresholds_styles')
    def styles(self, context, slot, payload):
        from pylon.core.tools import log
        log.info('slot: [%s], payload: %s', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'thresholds/styles.html',
            )
