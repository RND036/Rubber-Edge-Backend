from django.urls import path,include
from . import views
from . import disease_detection
from .rubber_chatbot import urls as chatbot_urls 

app_name = 'api'

urlpatterns = [
    # Existing endpoints
    path('rubber-prices/', views.get_rubber_prices, name='rubber-prices'),
    path('trigger-scrape/', views.trigger_scrape, name='trigger-scrape'),
    path('market-stats/', views.get_market_stats, name='market-stats'),
    path('historical-prices/', views.get_historical_prices, name='historical-prices'),
    path('scraping-logs/', views.get_scraping_logs, name='scraping-logs'),

    # Disease Detection APIs
    path('disease/detect/', disease_detection.detect_disease, name='disease_detect'),
    path('disease/health/', disease_detection.disease_health_check, name='disease_health'),
    path('disease/labels/', disease_detection.disease_labels, name='disease_labels'),

   path('chatbot/', include(chatbot_urls)),
   path("chat/", include("chat.urls")),
      # ========== CAROUSEL (NEW) ==========
   path('carousel/', include('carousel.urls')),
   # price management
   path('buyer-prices/', include('buyerprices.urls')),
   # latex quality
   path('latex-quality/', include('latex_quality.urls')),
]
