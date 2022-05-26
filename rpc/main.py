from tools import rpc_tools
from ..models.api_reports import APIReport
from pylon.core.tools import web


class RPC:
    @web.rpc('backend_results_or_404')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def backend_results_or_404(self, run_id):
        return APIReport.query.get_or_404(run_id)
