from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    farmer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="farmer_conversations"
    )
    officer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="officer_conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("farmer", "officer")

    def __str__(self):
        return f"{self.id}: {self.farmer_id} <-> {self.officer_id}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} in convo {self.conversation_id}"
