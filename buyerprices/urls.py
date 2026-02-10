from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ✅ CHANGE THIS LINE - Use BuyerPriceViewSet instead of RubberPriceViewSet
router.register(r'', views.BuyerPriceViewSet, basename='buyer-prices')
router.register(r'alerts', views.PriceAlertViewSet, basename='price-alert')

app_name = 'buyerprices'

urlpatterns = [
    path('', include(router.urls)),
]
