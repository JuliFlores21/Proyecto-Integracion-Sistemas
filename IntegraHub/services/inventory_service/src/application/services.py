from typing import List, Dict
from ..domain.ports import InventoryRepository, EventPublisher

class ReserveInventoryUseCase:
    def __init__(self, repository: InventoryRepository, publisher: EventPublisher):
        self.repository = repository
        self.publisher = publisher

    def execute(self, order_id: str, items: List[Dict]):
        # 1. Idempotency Check
        if self.repository.is_order_processed(order_id):
            print(f"Order {order_id} already processed. Skipping.")
            return

        # 2. Check Stock availability
        can_fulfill = True
        failed_reason = ""

        # Using a simple check first (locking strategy would depend on specific DB isolation levels)
        # For simplicity in this demo: Check all, then Update all.
        # In production: Use row locking or atomic decrements.
        
        for item in items:
            product_id = item['product_id']
            qty = item['quantity']
            product = self.repository.get_product(product_id)
            
            if not product:
                can_fulfill = False
                failed_reason = f"Product {product_id} not found"
                break
            
            if product.stock < qty:
                can_fulfill = False
                failed_reason = f"Insufficient stock for product {product_id}"
                break

        # 3. Transaction Execution
        if can_fulfill:
            try:
                # Deduct stock
                for item in items:
                    self.repository.update_stock(item['product_id'], -item['quantity'])
                
                # Mark processed
                self.repository.mark_order_processed(order_id, "RESERVED")
                
                # Publish Success
                self.publisher.publish("inventory", "InventoryReserved", {"order_id": order_id})
                print(f"Inventory reserved for order {order_id}")
                
            except Exception as e:
                # Rollback/Fail handling should be in repo adapter usually, 
                # strictly here we might catch DB errors.
                # If DB fails here, we re-raise to let the consumer retry.
                raise e
        else:
            # Mark processed as failed so we don't retry logic unnecessarily, 
            # Or maybe we DO want to retry later? 
            # Requirement says: "Si no [hay stock], publicar OrderRejected".
            # Usually stock issues don't resolve quickly, so we reject.
            self.repository.mark_order_processed(order_id, "REJECTED")
            
            self.publisher.publish("inventory", "OrderRejected", {
                "order_id": order_id, 
                "reason": failed_reason
            })
            print(f"Order {order_id} rejected: {failed_reason}")
