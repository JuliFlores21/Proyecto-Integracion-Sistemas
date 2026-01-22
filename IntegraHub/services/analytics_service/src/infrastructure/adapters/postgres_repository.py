from sqlalchemy import create_engine, Column, Integer, Float, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
from ...domain.ports import MetricsRepository
from ...domain.models import DailyMetrics

Base = declarative_base()

class DailyMetricsModel(Base):
    __tablename__ = "daily_analytics"
    date_entry = Column(Date, primary_key=True, default=date.today)
    total_sales = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    rejected_orders = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class PostgresMetricsRepository(MetricsRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create_today(self, session):
        today = date.today()
        record = session.query(DailyMetricsModel).filter_by(date_entry=today).first()
        if not record:
            record = DailyMetricsModel(date_entry=today)
            session.add(record)
            session.commit() # Commit to get it created
            session.refresh(record)
        return record

    def get_today_metrics(self) -> DailyMetrics:
        session = self.Session()
        try:
            record = self._get_or_create_today(session)
            return DailyMetrics(
                date=record.date_entry,
                total_sales_amount=record.total_sales,
                total_orders_count=record.total_orders,
                rejected_orders_count=record.rejected_orders,
                last_updated=record.last_updated
            )
        finally:
            session.close()

    def increment_orders(self, amount: float = 0.0):
        session = self.Session()
        try:
            record = self._get_or_create_today(session)
            record.total_orders += 1
            record.total_sales += amount
            record.last_updated = datetime.utcnow()
            session.commit()
        finally:
            session.close()

    def increment_rejections(self):
        session = self.Session()
        try:
            record = self._get_or_create_today(session)
            record.rejected_orders += 1
            record.last_updated = datetime.utcnow()
            session.commit()
        finally:
            session.close()
