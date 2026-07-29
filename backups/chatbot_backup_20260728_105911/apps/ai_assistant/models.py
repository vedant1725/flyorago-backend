from django.db import models

class AIKnowledgeBaseItem(models.Model):
    CATEGORY_CHOICES = [
        ('platform', 'Platform & How It Works'),
        ('traveller', 'Traveller Workflow & Earning'),
        ('sender', 'Sender & Package Delivery'),
        ('security', 'Safety, KYC & Security'),
        ('prohibited_items', 'Prohibited Items & Illegal Goods'),
        ('payments', 'Escrow, Wallet & Payments'),
        ('disputes', 'Disputes & Cancellations'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='platform')
    question = models.CharField(max_length=255, help_text="Question or trigger keyword phrase")
    answer = models.TextField(help_text="Factual answer or policy response text")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.question}"
