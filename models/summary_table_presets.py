from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY

from tools import db, db_tools, rpc_tools


class BackendPerformanceSummaryTablePreset(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    __tablename__ = "backend_performance_summary_table_presets"
    __table_args__ = (
        UniqueConstraint('project_id', 'name'),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=True)
    name = Column(String(128), unique=False, nullable=True)
    fields = Column(ARRAY(String), default=[])
