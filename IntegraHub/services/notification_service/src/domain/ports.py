from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str = None):
        """
        Sends a message through the channel.
        :param message: The body of the notification.
        :param recipient: Optional target (email address, slack channel ID, etc.)
        """
        pass
