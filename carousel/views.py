from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import CarouselItem
from .serializers import CarouselItemSerializer


class CarouselItemListView(generics.ListAPIView):
    """
    Public API endpoint to fetch active carousel items
    
    GET /api/carousel/items/
    
    Returns:
        - List of active carousel items ordered by 'order' field
        - Includes full image URLs
        - Text fields may be empty (image-only carousel)
    
    Authentication: Not required (public endpoint)
    """
    serializer_class = CarouselItemSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return only active carousel items, ordered by order field"""
        return CarouselItem.objects.filter(is_active=True)
    
    def get_serializer_context(self):
        """Pass request context to serializer for building absolute URLs"""
        return {'request': self.request}
    
    def list(self, request, *args, **kwargs):
        """Custom list method with logging"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        print(f"📡 Carousel API called - Returning {len(serializer.data)} items")
        
        return Response(serializer.data)


class CarouselHealthCheckView(APIView):
    """
    Health check endpoint for carousel service
    
    GET /api/carousel/health/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            active_count = CarouselItem.objects.filter(is_active=True).count()
            total_count = CarouselItem.objects.count()
            
            return Response({
                'status': 'healthy',
                'service': 'carousel',
                'timestamp': timezone.now().isoformat(),
                'statistics': {
                    'active_items': active_count,
                    'total_items': total_count,
                    'inactive_items': total_count - active_count
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'service': 'carousel',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
