from django.urls import path
from . import views

app_name = 'carousel'

urlpatterns = [
    path('items/', views.CarouselItemListView.as_view(), name='item_list'),
    path('health/', views.CarouselHealthCheckView.as_view(), name='health_check'),
]
