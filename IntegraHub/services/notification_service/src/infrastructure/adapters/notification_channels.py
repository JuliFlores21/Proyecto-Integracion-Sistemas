from ...domain.ports import NotificationChannel

class SlackAdapter(NotificationChannel):
    def send(self, message: str, recipient: str = "#ops-alerts"):
        # Simulated Webhook call
        print(f"   [Slack Webhook] 📢 Posting to {recipient}: {message}")

class EmailAdapter(NotificationChannel):
    def send(self, message: str, recipient: str = "customer@example.com"):
        # Simulated SMTP call
        print(f"   [Email Service] 📧 Sending to {recipient}: \n      Subject: Order Update\n      Body: {message}")
