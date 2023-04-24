from pylon.core.tools import web  # pylint: disable=E0611,E0401
from tools import auth


class Slot:
    @web.slot(f'backend_performance_runners_content')
    @auth.decorators.check_slot({
        "permissions": ["performance.backend.runners"]
    })
    def content(self, context, slot, payload):
        if payload is None:
            payload = {}
        with context.app.app_context():
            return self.descriptor.render_template(
                'runners_table/content.html',
            )

    @web.slot('backend_performance_runners_scripts')
    @auth.decorators.check_slot({
        "permissions": ["performance.backend.runners"]
    })
    def scripts(self, context, slot, payload):
        with context.app.app_context():
            return self.descriptor.render_template(
                'runners_table/scripts.html',
            )
