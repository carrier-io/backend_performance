from pylon.core.tools import web  # pylint: disable=E0611,E0401
from tools import auth  # pylint: disable=E0401

from ..constants import JMETER_MAPPING, GATLING_MAPPING


class Slot:  # pylint: disable=E1101,R0903
    @web.slot('backend_performance_content')
    def content(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/content.html',
                runners={
                    'jMeter': list(map(lambda i: {'version': i}, JMETER_MAPPING.keys())),
                    'Gatling': list(map(lambda i: {'version': i}, GATLING_MAPPING.keys()))
                }
            )

    @web.slot('backend_performance_scripts')
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/scripts.html',
            )

    @web.slot('backend_performance_styles')
    def styles(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'backend_performance/styles.html',
            )
