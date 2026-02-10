from django.urls import path
from . import views

app_name = 'latex_quality'

urlpatterns = [
    # ==================== LIVE SENSOR ENDPOINTS ====================
    path('latex-quality/live-ingest/', views.latex_live_ingest, name='live_ingest'),
    path('latex-quality/live/', views.latex_live_get, name='live_get'),
    
    # ==================== FARMER ENDPOINTS ====================
    path('readings/create/', views.create_latex_reading, name='create_reading'),
    path('readings/', views.get_latex_readings, name='get_readings'),
    path('dashboard/', views.get_dashboard_stats, name='dashboard'),
    path('alerts/', views.get_quality_alerts, name='get_alerts'),
    path('alerts/<uuid:alert_id>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/read-all/', views.mark_all_alerts_read, name='mark_all_read'),
]
