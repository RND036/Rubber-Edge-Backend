from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings


class Event(models.Model):
    """
    Event model for agricultural events, workshops, and announcements
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='created_events'
    )
    
    image = models.ImageField(
        upload_to='events/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    max_participants = models.IntegerField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        indexes = [
            models.Index(fields=['-event_date']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.event_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_past_event(self):
        from django.utils import timezone
        return self.event_date < timezone.now()


class EventAttendance(models.Model):
    """
    Track farmer attendance/interest in events
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_attendances'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('interested', 'Interested'),
            ('attending', 'Attending'),
            ('attended', 'Attended'),
            ('not_attending', 'Not Attending'),
        ],
        default='interested'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'farmer']
        ordering = ['-registered_at']
        verbose_name = 'Event Attendance'
        verbose_name_plural = 'Event Attendances'
    
    def __str__(self):
        return f"{self.farmer.username} - {self.event.title}"
