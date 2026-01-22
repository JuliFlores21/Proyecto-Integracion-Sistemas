import random
import time
import pybreaker
from ...domain.ports import PaymentGateway

# Configure Circuit Breaker
# Opens after 3 consecutive failures.
# Stays open for 10 seconds before allowing a test request (Half-Open).
db_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=10
)

class MockPaymentGateway(PaymentGateway):
    
    @db_breaker
    def charge(self, order_id: str, amount: float) -> str:
        """
        Simulates an external payment call.
        Includes simulated failures to test Resiliency/Circuit Breaker.
        """
        # Simulate network latency
        time.sleep(0.5)

        # Logic to simulate failures based on amount or random
        # E.g. Amount > 1000 fails (Business Rule / Gateway Rejection)
        # E.g. Random failures (Infrastructure Instability)
        
        if amount > 5000:
            raise ValueError("Insufficient funds")

        # Simulate intermittent infrastructure failure (20% chance)
        # We need this to trigger the Circuit Breaker
        if random.random() < 0.2:
            raise ConnectionError("Payment Gateway Connection Timeout")

        return f"trans_{random.randint(10000,99999)}"
