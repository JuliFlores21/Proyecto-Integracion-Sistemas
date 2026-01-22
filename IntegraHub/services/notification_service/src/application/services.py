from typing import List
from ..domain.ports import NotificationChannel

class MessageTranslator:
    """
    Implements the Message Translator pattern.
    Converts raw domain events into user-friendly messages.
    """
    @staticmethod
    def translate(event_type: str, data: dict) -> str:
        order_id = data.get("order_id", "Unknown")
        
        if event_type == "OrderCreated":
            total = data.get("total_amount", 0)
            return f"🆕 New Order Received! ID: {order_id}. Total: ${total}. Waiting for processing."
        
        elif event_type == "OrderConfirmed":
            txn_id = data.get("transaction_id", "N/A")
            return f"✅ Order {order_id} Confirmed! Payment successful (Txn: {txn_id}). Preparing for shipment."
        
        elif event_type == "OrderRejected":
            reason = data.get("reason", "Unknown reason")
            return f"❌ Order {order_id} Failed. Reason: {reason}. Please check system logs."
        
        return f"ℹ️ Update on Order {order_id}: {event_type}"

class NotificationUseCase:
    def __init__(self, channels: List[NotificationChannel]):
        self.channels = channels
        self.translator = MessageTranslator()

    def execute(self, event_type: str, data: dict):
        # 1. Translate Message
        human_message = self.translator.translate(event_type, data)
        
        # 2. Fan-out to all channels (Pub/Sub pattern internal usage)
        print(f"\n[Notification Logic] Broadcast: '{human_message}'")
        
        for channel in self.channels:
            try:
                # In a real app, recipient might come from 'data' (e.g. customer_email) 
                # or config (e.g. slack_channel_id)
                channel.send(human_message)
            except Exception as e:
                print(f"Error sending payload to channel {channel.__class__.__name__}: {e}")
