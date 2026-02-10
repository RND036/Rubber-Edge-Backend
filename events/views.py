# events/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Event, EventAttendance
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    EventAttendanceSerializer,
    AttendanceCreateSerializer,
)
from users.models import User


def notify_farmers_of_new_event(event):
    """
    Send WebSocket notifications to all farmers when a new event is created
    """
    channel_layer = get_channel_layer()
    
    # Get all active farmers
    farmers = User.objects.filter(role='farmer', is_active=True)
    
    # Get officer name
    officer_name = event.created_by.phone_number
    if event.created_by.role == 'officer' and hasattr(event.created_by, 'officer_profile'):
        officer_name = event.created_by.officer_profile.name
    
    print(f"📢 Notifying {farmers.count()} farmers about event: {event.title}")
    
    for farmer in farmers:
        notification_data = {
            'eventId': event.id,
            'eventTitle': event.title,
            'eventDescription': event.description,
            'eventDate': event.event_date.isoformat(),
            'officerName': officer_name,
        }
        
        # Send to farmer's notification channel
        group_name = f'notifications_{farmer.id}'
        
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'message': notification_data,
                }
            )
            print(f"✅ Sent event notification to farmer {farmer.id}")
        except Exception as e:
            print(f"❌ Failed to send notification to farmer {farmer.id}: {e}")


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event management
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Event.objects.select_related('created_by').prefetch_related('attendances')
        
        # Officers can see all events, farmers see only active events
        if user.role == 'farmer':
            queryset = queryset.filter(is_active=True, is_cancelled=False)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventListSerializer
    
    def list(self, request, *args, **kwargs):
        """List all events with debugging"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        print(f"📤 List method: Returning {len(serializer.data)} events")
        if serializer.data:
            print(f"📦 First event: {serializer.data[0]}")
        
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single event"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        print(f"📤 Retrieve: Event {instance.id} - {instance.title}")
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create new event and return full data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the event and get the instance
        event = self.perform_create(serializer)
        
        # Use EventListSerializer to return complete event data with ID
        output_serializer = EventListSerializer(event, context={'request': request})
        headers = self.get_success_headers(output_serializer.data)
        
        print(f"📤 Created event: ID={event.id}, Title={event.title}")
        print(f"📦 Response data: {output_serializer.data}")
        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Create event and notify all farmers"""
        # Only officers can create events
        if self.request.user.role != 'officer':
            raise PermissionError("Only officers can create events")
        
        event = serializer.save(created_by=self.request.user)
        print(f"✅ Event created: {event.id} - {event.title}")
        
        # Notify all farmers
        notify_farmers_of_new_event(event)
        
        return event
    
    def perform_update(self, serializer):
        """Only creator can update event"""
        event = self.get_object()
        if event.created_by != self.request.user:
            raise PermissionError("Only the creator can update this event")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only creator can delete event"""
        if instance.created_by != self.request.user:
            raise PermissionError("Only the creator can delete this event")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events (not past)"""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            event_date__gte=now,
            is_active=True,
            is_cancelled=False
        ).order_by('event_date')
        
        serializer = EventListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        print(f"📤 Upcoming: Returning {len(serializer.data)} events")
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get past events"""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            event_date__lt=now
        ).order_by('-event_date')
        
        serializer = EventListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        print(f"📤 Past: Returning {len(serializer.data)} events")
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events created by the current officer"""
        if request.user.role != 'officer':
            return Response(
                {"error": "Only officers can view their events"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(
            created_by=request.user
        ).order_by('-event_date')
        
        serializer = EventListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        print(f"📤 My Events: Returning {len(serializer.data)} events")
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register farmer for an event"""
        if request.user.role != 'farmer':
            return Response(
                {"error": "Only farmers can register for events"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event = self.get_object()
        
        # Check if event is in the past
        if event.event_date < timezone.now():
            return Response(
                {"error": "Cannot register for past events"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is active
        if not event.is_active or event.is_cancelled:
            return Response(
                {"error": "This event is not available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if max participants reached
        if event.max_participants:
            current_count = event.attendances.filter(
                status__in=['interested', 'attending', 'attended']
            ).count()
            if current_count >= event.max_participants:
                return Response(
                    {"error": "Event is full"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get or create attendance
        attendance, created = EventAttendance.objects.get_or_create(
            event=event,
            farmer=request.user,
            defaults={'status': request.data.get('status', 'interested')}
        )
        
        if not created:
            # Update existing attendance
            attendance.status = request.data.get('status', 'interested')
            attendance.save()
        
        serializer = EventAttendanceSerializer(attendance, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def unregister(self, request, pk=None):
        """Unregister farmer from an event"""
        if request.user.role != 'farmer':
            return Response(
                {"error": "Only farmers can unregister from events"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event = self.get_object()
        
        try:
            attendance = EventAttendance.objects.get(
                event=event,
                farmer=request.user
            )
            attendance.delete()
            return Response(
                {"message": "Successfully unregistered from event"},
                status=status.HTTP_200_OK
            )
        except EventAttendance.DoesNotExist:
            return Response(
                {"error": "You are not registered for this event"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """Get list of attendees (officer only)"""
        if request.user.role != 'officer':
            return Response(
                {"error": "Only officers can view attendees"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event = self.get_object()
        
        # Only creator can view attendees
        if event.created_by != request.user:
            return Response(
                {"error": "Only the event creator can view attendees"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendances = event.attendances.all()
        serializer = EventAttendanceSerializer(
            attendances,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get event statistics for the user"""
        user = request.user
        
        if user.role == 'officer':
            # Officer statistics
            my_events = Event.objects.filter(created_by=user)
            stats = {
                'total_events': my_events.count(),
                'upcoming_events': my_events.filter(
                    event_date__gte=timezone.now(),
                    is_active=True,
                    is_cancelled=False
                ).count(),
                'total_attendees': EventAttendance.objects.filter(
                    event__created_by=user
                ).count(),
            }
        elif user.role == 'farmer':
            # Farmer statistics
            my_registrations = EventAttendance.objects.filter(farmer=user)
            stats = {
                'registered_events': my_registrations.count(),
                'upcoming_registered': my_registrations.filter(
                    event__event_date__gte=timezone.now(),
                    event__is_active=True,
                    event__is_cancelled=False
                ).count(),
            }
        else:
            stats = {}
        
        print(f"📤 Statistics: {stats}")
        return Response(stats)
