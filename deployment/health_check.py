# Health Check endpoint for load balancers and monitoring
# Add this to your main urls.py

from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def health_check(request):
    """
    Simple health check endpoint
    Returns 200 OK if the application is running
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'rubberedge-backend'
    })

# In your urls.py, add:
# path('health/', health_check, name='health_check'),
