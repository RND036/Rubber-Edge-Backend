from django.urls import path
from api.rubber_chatbot import views

urlpatterns = [
    path('chat/', views.chat, name='chatbot_chat'),
    path('session/<str:session_id>/', views.get_session, name='get_session'),
    path('session/<str:session_id>/clear/', views.clear_session, name='clear_session'),
    path('health/', views.health, name='chatbot_health'),
]
