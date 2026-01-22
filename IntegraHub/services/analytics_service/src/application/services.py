from ..domain.ports import MetricsRepository

class ProcessEventUseCase:
    def __init__(self, repository: MetricsRepository):
        self.repository = repository

    def execute(self, event_type: str, data: dict):
        # Business Logic for Aggregation
        if event_type == "OrderConfirmed":
            # Assuming 'amount' or 'total_amount' is present
            amount = data.get("total_amount", 0.0) 
            # In case Payment doesn't pass amount, we might need to rely on OrderCreated event instead?
            # But OrderConfirmed is the source of truth for a SALE.
            # If Payment event lacks amount, we check if we can get it.
            # Let's support getting it from data.
            self.repository.increment_orders(amount)
            print(f"Analytics: Sale recorded +${amount}")

        elif event_type == "OrderRejected":
            self.repository.increment_rejections()
            print("Analytics: Rejection recorded")
            
        # We could also track OrderCreated for "Abandoned Carts" analysis later

class GetMetricsUseCase:
    def __init__(self, repository: MetricsRepository):
        self.repository = repository
        
    def execute(self):
        return self.repository.get_today_metrics()
