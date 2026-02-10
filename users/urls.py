from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # ========== AUTHENTICATION ==========
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # ========== USER PROFILE ==========
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),  # NEW LINE
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ========== FARMER MANAGEMENT (Officer Only) ==========
    path('farmers/', views.get_farmers, name='get_farmers'),
    
    # ========== OFFICER DIRECTORY (All Authenticated Users) ==========
    path('officers/', views.get_officers, name='get_officers'),
]
