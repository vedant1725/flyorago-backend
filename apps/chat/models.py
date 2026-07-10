from django.db import models
from django.conf import settings

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        participants_emails = ", ".join([u.email for u in self.participants.all()])
        return f"Conversation #{self.id} between [{participants_emails}]"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    
    text = models.TextField(blank=True, null=True)
    attachment_url = models.CharField(max_length=500, blank=True, null=True)
    voice_note_url = models.CharField(max_length=500, blank=True, null=True)
    
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg #{self.id} by {self.sender.email} in Conv #{self.conversation.id}"
