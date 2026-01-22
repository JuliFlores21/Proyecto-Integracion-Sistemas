from fastapi import FastAPI
from ...application.services import GetMetricsUseCase

def create_app(get_metrics_use_case: GetMetricsUseCase):
    app = FastAPI(title="Analytics Service")

    @app.get("/metrics")
    def get_metrics():
        metrics = get_metrics_use_case.execute()
        return {
            "date": metrics.date,
            "sales_volume": metrics.total_sales_amount,
            "orders_count": metrics.total_orders_count,
            "rejected_orders": metrics.rejected_orders_count,
            "last_updated": metrics.last_updated
        }
    
    return app
