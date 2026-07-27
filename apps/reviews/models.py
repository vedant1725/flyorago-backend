from django.db import models
from django.conf import settings
from bookings.models import Booking

class Review(models.Model):
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_written')
    reviewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.IntegerField(default=5) # 1-5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('reviewer', 'booking')

    def __str__(self):
        return f"Review by {self.reviewer.email} on {self.reviewed_user.email} (Rating: {self.rating})"
