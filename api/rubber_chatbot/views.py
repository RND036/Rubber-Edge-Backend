from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import uuid
from django.utils import timezone
from api.rubber_chatbot.agents import query_rubber_agent, clear_rubber_session
from api.models import ChatSession, ChatMessage, DiseaseQuery, ShopQuery
from api.rubber_chatbot.serializers import (
    ChatRequestSerializer, 
    ChatResponseSerializer,
    ChatSessionLimitedSerializer
)


@api_view(['POST'])
def chat(request):
    """Handle chatbot conversations"""
    serializer = ChatRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id') or str(uuid.uuid4())
    
    # Get or create session
    session, created = ChatSession.objects.get_or_create(
        session_id=session_id,
        defaults={'is_active': True}
    )
    
    # Save user message
    ChatMessage.objects.create(
        session=session,
        message_type='user',
        content=message
    )
    
    try:
        # Query the agent
        result = query_rubber_agent(message, session_id)
        
        # Save bot response
        ChatMessage.objects.create(
            session=session,
            message_type='bot',
            content=result['response'],
            metadata={'tools_used': result.get('tools_used', [])}
        )
        
        # Log specialized queries
        tools = result.get('tools_used', [])
        if 'rubber_disease_search' in tools:
            DiseaseQuery.objects.create(
                session=session,
                query_text=message,
                bot_response=result['response']
            )
        if 'rubber_medicine_location_search' in tools:
            ShopQuery.objects.create(
                session=session,
                query_text=message,
                bot_response=result['response']
            )
        
        # Return response
        return Response(result, status=status.HTTP_200_OK)
            
    except Exception as e:
        error_response = {
            'response': f"I encountered an error: {str(e)}\n\n⚠️ Please try again or rephrase your question.",
            'session_id': session_id,
            'timestamp': timezone.now().isoformat(),
            'error': True,
            'error_type': type(e).__name__,
            'tools_used': []
        }
        
        # Log error message
        ChatMessage.objects.create(
            session=session,
            message_type='system',
            content=f"Error: {str(e)}",
            metadata={'error_type': type(e).__name__}
        )
        
        return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_session(request, session_id):
    """Retrieve session with limited message history"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        serializer = ChatSessionLimitedSerializer(session)
        return Response(serializer.data)
    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def clear_session(request, session_id):
    """Clear/delete a session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        
        # Clear agent memory
        clear_rubber_session(session_id)
        
        # Mark session as inactive
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Session cleared successfully',
            'session_id': session_id
        }, status=status.HTTP_200_OK)
    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def health(request):
    """Health check endpoint"""
    return Response({
        "status": "healthy",
        "rubberbot": "active",
        "timestamp": timezone.now().isoformat()
    })
