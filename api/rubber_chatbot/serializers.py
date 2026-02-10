from rest_framework import serializers
from api.models import ChatSession, ChatMessage
from django.utils import timezone
from datetime import timedelta


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'message_type', 'content', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'created_at', 'updated_at', 'is_active', 
                  'messages', 'message_count', 'last_activity']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_activity(self, obj):
        return obj.updated_at


class ChatSessionLimitedSerializer(serializers.ModelSerializer):
    """Serializer that returns only recent messages to reduce payload"""
    recent_messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'created_at', 'is_active', 
                  'recent_messages', 'message_count']
    
    def get_recent_messages(self, obj):
        """Return only last 10 messages"""
        recent = obj.messages.all()[:10]
        return ChatMessageSerializer(recent, many=True).data
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(
        required=True,
        min_length=1,
        max_length=2000,
        trim_whitespace=True,
        error_messages={
            'required': 'Message is required',
            'blank': 'Message cannot be empty',
            'max_length': 'Message is too long (max 2000 characters)',
            'min_length': 'Message is too short'
        }
    )
    session_id = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=False,
        trim_whitespace=True
    )
    
    def validate_message(self, value):
        """Validate message content"""
        # Remove excessive whitespace
        cleaned = ' '.join(value.split())
        
        if not cleaned:
            raise serializers.ValidationError("Message cannot be only whitespace")
        
        # Check for minimum meaningful length
        if len(cleaned) < 2:
            raise serializers.ValidationError("Message is too short")
        
        return cleaned
    
    def validate_session_id(self, value):
        """Validate session ID format"""
        if value:
            # Check if session exists and is not too old
            try:
                session = ChatSession.objects.get(session_id=value)
                
                # Check if session is too old (> 24 hours inactive)
                inactive_threshold = timezone.now() - timedelta(hours=24)
                if session.updated_at < inactive_threshold:
                    raise serializers.ValidationError(
                        "Session expired. Please start a new conversation."
                    )
                    
            except ChatSession.DoesNotExist:
                # Session will be created in view, so this is fine
                pass
        
        return value


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chatbot responses"""
    response = serializers.CharField()
    session_id = serializers.CharField()
    timestamp = serializers.CharField()
    tools_used = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    error = serializers.BooleanField(default=False)
    error_type = serializers.CharField(required=False, allow_blank=True, default="")
