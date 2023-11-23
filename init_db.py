from tools import db


def init_db():
    from .models.reports import Report
    from .models.baselines import Baseline
    from .models.tests import Test
    from .models.thresholds import Threshold
    from .models.runners import Runner
    from .models.summary_table_presets import BackendPerformanceSummaryTablePreset
    db.get_shared_metadata().create_all(bind=db.engine)

