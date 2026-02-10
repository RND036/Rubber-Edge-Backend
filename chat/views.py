from django.db.models import Q
from rest_framework import status, permissions, views
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from users.models import User  # adjust if different


class ConversationListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Conversation.objects.filter(
            Q(farmer=user) | Q(officer=user)
        ).order_by("-created_at")
        serializer = ConversationSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Body: { "other_user_id": <int> }
        Creates or gets existing conversation between two users.
        Prevents duplicate conversations by checking both directions.
        """
        user = request.user
        other_id = request.data.get("other_user_id")

        if not other_id:
            return Response(
                {"detail": "other_user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            other = User.objects.get(id=other_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Determine farmer and officer based on actual roles
        if getattr(user, "role", None) == "FARMER":
            farmer, officer = user, other
        else:
            farmer, officer = other, user

        # ✅ CRITICAL FIX: Check BOTH directions to prevent duplicate conversations
        # This handles cases where the conversation might have been created
        # with farmer/officer in either order
        convo = Conversation.objects.filter(
            (Q(farmer=farmer) & Q(officer=officer)) |
            (Q(farmer=officer) & Q(officer=farmer))
        ).first()
        
        if not convo:
            # Create new conversation with correct farmer/officer assignment
            convo = Conversation.objects.create(farmer=farmer, officer=officer)
            print(f"✅ CREATED new conversation #{convo.id}: Farmer={farmer.id} <-> Officer={officer.id}")
        else:
            print(f"✅ FOUND existing conversation #{convo.id}: Farmer={convo.farmer_id} <-> Officer={convo.officer_id}")
        
        return Response(
            ConversationSerializer(convo).data,
            status=status.HTTP_201_CREATED,
        )


class MessageListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            convo = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if user is part of this conversation
        if request.user not in [convo.farmer, convo.officer]:
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Return ALL messages in the conversation (from both users)
        messages = convo.messages.order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        
        print(f"📨 Returning {messages.count()} messages for conversation #{conversation_id} to user {request.user.id}")
        
        return Response(serializer.data, status=status.HTTP_200_OK)