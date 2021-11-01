from .models.api_reports import APIReport


def backend_results_or_404(run_id):
    return APIReport.query.get_or_404(run_id)