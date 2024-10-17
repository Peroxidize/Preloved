from django.db import models

# Create your models here.
class ChatMessage(models.Model):
    name = models.CharField(max_length=255)  # Name of the chat or conversation
    userID = models.CharField(max_length=255)  # Name or ID of the sender
    sellerID = models.CharField(max_length=255)  # Name or ID of the receiver
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp of the message
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['userID', 'sellerID'])
        ]  # Adding indexes to improve query performance
