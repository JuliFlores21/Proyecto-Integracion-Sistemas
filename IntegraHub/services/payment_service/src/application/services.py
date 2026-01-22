from ..domain.ports import PaymentGateway, EventPublisher
from ..domain.models import PaymentTransaction
import pybreaker

class ProcessPaymentUseCase:
    def __init__(self, gateway: PaymentGateway, publisher: EventPublisher):
        self.gateway = gateway
        self.publisher = publisher

    def execute(self, order_id: str, amount: float):
        print(f"Processing payment for Order: {order_id}, Amount: {amount}")
        
        try:
            # 1. Attempt Charge (Protected by Circuit Breaker inside the adapter)
            transaction_id = self.gateway.charge(order_id, amount)
            
            # 2. Success Case
            print(f"Payment successful: {transaction_id}")
            self.publisher.publish("payments", "OrderConfirmed", {
                "order_id": order_id,
                "status": "CONFIRMED",
                "transaction_id": transaction_id
            })

        except pybreaker.CircuitBreakerError:
            # Circuit is OPEN - Fail fast
            print(f"Circuit Breaker is OPEN. Payment failed for {order_id}")
            # Re-raise to let the consumer handle DLQ routing for transient/system issues
            raise 

        except Exception as e:
            # Logic/Gateway Error (e.g., Insufficient Funds, Declined)
            # We treat this as a definitive business failure.
            print(f"Payment failed: {e}")
            self.publisher.publish("payments", "OrderRejected", {
                "order_id": order_id,
                "reason": f"Payment Failed: {str(e)}"
            })
