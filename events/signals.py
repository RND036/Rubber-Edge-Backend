from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event
from users.models import User
import json


@receiver(post_save, sender=Event, created=True)
def event_created_notification(sender, instance, created, **kwargs):
    """Send notification to all users when a new event is created"""
    if created:
        channel_layer = get_channel_layer()
        
        # Get all users except the event creator
        users = User.objects.exclude(id=instance.created_by.id)
        
        notification_data = {
            'type': 'event_notification',
            'notification': {
                'id': f'event-{instance.id}',
                'type': 'event',
                'title': 'New Event Created',
                'message': f'{instance.title} - {instance.event_date.strftime("%B %d, %Y")}',
                'time': 'Just now',
                'read': False,
                'createdAt': int(instance.created_at.timestamp() * 1000),
                'data': {
                    'eventId': instance.id,
                    'eventTitle': instance.title,
                    'eventDate': instance.event_date.isoformat(),
                }
            }
        }
        
        # Send to each user's notification channel
        for user in users:
            try:
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user.id}',
                    notification_data
                )
                print(f'✅ Sent event notification to user {user.id}')
            except Exception as e:
                print(f'❌ Failed to send notification to user {user.id}: {e}')
