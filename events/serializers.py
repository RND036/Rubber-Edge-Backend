# events/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Event, EventAttendance
from users.models import User


class EventListSerializer(serializers.ModelSerializer):
    """Serializer for listing events"""
    created_by_name = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    attendance_count = serializers.SerializerMethodField()
    user_attendance_status = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_date', 'location',
            'image', 'created_by_name', 'is_active', 'is_cancelled',
            'created_at', 'contact_number', 'max_participants',
            'is_past', 'attendance_count', 'user_attendance_status'
        ]
        read_only_fields = ['id', 'created_at']

    def get_image(self, obj):
        """Get full image URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_created_by_name(self, obj):
        """Get the name of the event creator based on their role"""
        try:
            user = obj.created_by
            if user.role == 'farmer' and hasattr(user, 'farmer_profile'):
                return user.farmer_profile.name
            elif user.role == 'officer' and hasattr(user, 'officer_profile'):
                return user.officer_profile.name
            elif user.role == 'buyer' and hasattr(user, 'buyer_profile'):
                return user.buyer_profile.company_name
        except Exception:
            pass
        return obj.created_by.phone_number

    def get_is_past(self, obj):
        """Check if event is in the past"""
        return timezone.now() > obj.event_date

    def get_attendance_count(self, obj):
        """Get count of attendees"""
        return obj.attendances.count()

    def get_user_attendance_status(self, obj):
        """Get current user's attendance status"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attendance = obj.attendances.filter(farmer=request.user).first()
            if attendance:
                return attendance.status
        return None


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user info in event details"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'full_name', 'role']

    def get_full_name(self, obj):
        """Get the full name based on user role"""
        try:
            if obj.role == 'farmer' and hasattr(obj, 'farmer_profile'):
                return obj.farmer_profile.name
            elif obj.role == 'officer' and hasattr(obj, 'officer_profile'):
                return obj.officer_profile.name
            elif obj.role == 'buyer' and hasattr(obj, 'buyer_profile'):
                return obj.buyer_profile.company_name
        except Exception:
            pass
        return obj.phone_number


class EventAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for event attendance"""
    farmer_name = serializers.SerializerMethodField()
    farmer_phone = serializers.SerializerMethodField()
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventAttendance
        fields = [
            'id', 'event', 'farmer', 'status', 'registered_at',
            'farmer_name', 'farmer_phone', 'event_title'
        ]
        read_only_fields = ['id', 'registered_at']

    def get_farmer_name(self, obj):
        """Get farmer name from profile"""
        try:
            if hasattr(obj.farmer, 'farmer_profile'):
                return obj.farmer.farmer_profile.name
        except Exception:
            pass
        return obj.farmer.phone_number

    def get_farmer_phone(self, obj):
        """Get farmer phone number"""
        return obj.farmer.phone_number


class EventDetailSerializer(serializers.ModelSerializer):
    """Serializer for event details"""
    created_by = UserSerializer(read_only=True)
    is_past = serializers.SerializerMethodField()
    attendance_count = serializers.SerializerMethodField()
    attendees = EventAttendanceSerializer(source='attendances', many=True, read_only=True)
    user_attendance_status = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_date', 'location',
            'image', 'created_by', 'is_active', 'is_cancelled',
            'created_at', 'updated_at', 'contact_number', 'max_participants',
            'is_past', 'attendance_count', 'attendees', 'user_attendance_status'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_image(self, obj):
        """Get full image URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_is_past(self, obj):
        """Check if event is in the past"""
        return timezone.now() > obj.event_date

    def get_attendance_count(self, obj):
        """Get count of attendees"""
        return obj.attendances.count()

    def get_user_attendance_status(self, obj):
        """Get current user's attendance status"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attendance = obj.attendances.filter(farmer=request.user).first()
            if attendance:
                return attendance.status
        return None


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating events"""

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_date', 'location',
            'image', 'is_active', 'is_cancelled',
            'contact_number', 'max_participants'
        ]

    def validate_event_date(self, value):
        """Ensure event date is in the future"""
        if value < timezone.now():
            raise serializers.ValidationError("Event date must be in the future")
        return value

    def validate_max_participants(self, value):
        """Ensure max participants is positive"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Max participants must be positive")
        return value
    
    def to_representation(self, instance):
        """Return full event details using EventListSerializer"""
        return EventListSerializer(instance, context=self.context).data


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records"""

    class Meta:
        model = EventAttendance
        fields = ['status']

    def validate_status(self, value):
        """Validate status"""
        valid_statuses = ['interested', 'attending', 'attended', 'not_attending']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
