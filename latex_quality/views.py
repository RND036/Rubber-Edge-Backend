from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Q
from .models import LatexQualityReading, LatexQualityAlert
from .serializers import (
    LatexQualityReadingCreateSerializer,
    LatexQualityReadingSerializer,
    LatexQualityAlertSerializer,
    DashboardStatsSerializer
)

# ==================== LIVE SENSOR DATA STORAGE ====================
# In-memory storage for real-time sensor data from ESP32
LATEST_READINGS = {}


# ==================== ESP32 LIVE DATA INGESTION ====================
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow ESP32 to post without authentication
def latex_live_ingest(request):
    """
    ESP32 posts live sensor data here every 2 seconds
    Endpoint: POST /latex-quality/live-ingest/?device_id=SENSOR_001
    Body: {"ph": 6.8, "turbidity": 250, "drc": 35, "temperature": 28, "humidity": 75}
    """
    device_id = request.query_params.get('device_id', 'SENSOR_001')
    data = request.data
    
    try:
        # Store in memory for quick access
        LATEST_READINGS[device_id] = {
            'ph_value': float(data.get('ph', 0)),
            'turbidity_ntu': float(data.get('turbidity', 0)),
            'drc_percent': float(data.get('drc', 0)),
            'temperature_celsius': float(data.get('temperature', 0)),
            'humidity_percent': float(data.get('humidity', 0)),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Log to console
        print(f"✅ ESP32 [{device_id}] → pH:{data.get('ph')} Turb:{data.get('turbidity')} DRC:{data.get('drc')}")
        
        return Response({
            'status': 'ok',
            'device_id': device_id,
            'message': 'Data received successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    except ValueError as e:
        print(f"❌ Invalid data format: {e}")
        return Response({
            'status': 'error',
            'message': 'Invalid data format',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(f"❌ Error storing sensor data: {e}")
        return Response({
            'status': 'error',
            'message': 'Failed to store sensor data',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GET LIVE SENSOR DATA ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latex_live_get(request):
    """
    React Native app gets latest sensor data from memory
    Endpoint: GET /latex-quality/live/?device_id=SENSOR_001
    """
    device_id = request.query_params.get('device_id', 'SENSOR_001')
    reading = LATEST_READINGS.get(device_id)
    
    if not reading:
        return Response({
            'status': 'no_data',
            'live': None,
            'message': f'No live data available for device {device_id}'
        }, status=status.HTTP_200_OK)
    
    # Check if data is fresh (within last 10 seconds)
    reading_time = timezone.datetime.fromisoformat(reading['timestamp'])
    age_seconds = (timezone.now() - reading_time).total_seconds()
    
    return Response({
        'status': 'ok',
        'live': reading,
        'age_seconds': age_seconds,
        'is_fresh': age_seconds < 10
    }, status=status.HTTP_200_OK)


# ==================== FARMER SUBMIT READING ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_latex_reading(request):
    """
    Farmer submits new latex quality reading from mobile app
    POST /api/latex-quality/readings/create/
    Body: {"ph_value": 6.8, "turbidity_ntu": 250, "drc_percent": 36.5, 
           "temperature_celsius": 28, "humidity_percent": 75, "notes": "Morning collection"}
    """
    try:
        # Check if user is a farmer
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can submit latex quality readings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        
        # Validate input
        serializer = LatexQualityReadingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Create reading (quality metrics auto-calculated in model's save method)
        reading = LatexQualityReading.objects.create(
            farmer=farmer,
            ph_value=data['ph_value'],
            turbidity_ntu=data['turbidity_ntu'],
            drc_percent=data['drc_percent'],
            temperature_celsius=data.get('temperature_celsius'),
            humidity_percent=data.get('humidity_percent'),
            notes=data.get('notes', ''),
        )
        
        # Check for quality issues and create alerts
        alerts_created = create_quality_alerts(farmer, reading)
        
        # Return created reading
        response_serializer = LatexQualityReadingSerializer(reading)
        
        return Response({
            'status': 'success',
            'message': 'Reading recorded successfully',
            'reading': response_serializer.data,
            'alerts_created': alerts_created
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Error creating reading: {e}")
        return Response(
            {'error': 'Failed to create reading', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def create_quality_alerts(farmer, reading):
    """Create alerts based on reading quality"""
    alerts_created = 0
    
    # Alert for overall poor quality
    if reading.quality_status == 'POOR':
        LatexQualityAlert.objects.create(
            farmer=farmer,
            reading=reading,
            alert_type='LOW_QUALITY',
            severity='HIGH',
            message=f'Poor latex quality detected: Grade {reading.rss_grade}, Score {reading.quality_score}/100',
            recommendations='''• Check collection containers for cleanliness
• Review tapping technique
• Verify proper storage conditions
• Consider adding preservative if not already done'''
        )
        alerts_created += 1
    
    # Alert for high turbidity
    if reading.turbidity_ntu > 800:
        LatexQualityAlert.objects.create(
            farmer=farmer,
            reading=reading,
            alert_type='HIGH_TURBIDITY',
            severity='MEDIUM',
            message=f'High turbidity detected: {reading.turbidity_ntu} NTU (Normal: <300)',
            recommendations='''• Filter latex before storage
• Check for dirt or debris contamination
• Clean collection containers thoroughly
• Avoid rain water mixing'''
        )
        alerts_created += 1
    
    # Alert for abnormal pH
    if reading.ph_value < 6.0:
        LatexQualityAlert.objects.create(
            farmer=farmer,
            reading=reading,
            alert_type='ABNORMAL_PH',
            severity='HIGH',
            message=f'Low pH detected: {reading.ph_value} - Risk of spoilage',
            recommendations='''• Add ammonia preservative immediately (0.7% concentration)
• Check storage temperature
• Use within 24 hours if no preservative added'''
        )
        alerts_created += 1
    elif reading.ph_value > 11:
        LatexQualityAlert.objects.create(
            farmer=farmer,
            reading=reading,
            alert_type='ABNORMAL_PH',
            severity='MEDIUM',
            message=f'Very high pH: {reading.ph_value} - Excess preservative',
            recommendations='''• Reduce ammonia concentration in future batches
• Optimal preservative: 0.7% ammonia'''
        )
        alerts_created += 1
    
    # Alert for low DRC
    if reading.drc_percent < 25:
        LatexQualityAlert.objects.create(
            farmer=farmer,
            reading=reading,
            alert_type='LOW_DRC',
            severity='MEDIUM',
            message=f'Low dry rubber content: {reading.drc_percent}% (Normal: >30%)',
            recommendations='''• Check tapping technique - avoid over-dilution
• Tap early morning (5-7 AM) for best DRC
• Ensure trees are properly rested between tappings
• Avoid tapping during heavy rain'''
        )
        alerts_created += 1
    
    return alerts_created


# ==================== GET FARMER'S READINGS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latex_readings(request):
    """
    Get farmer's latex quality readings
    GET /api/latex-quality/readings/?days=7&limit=20
    """
    try:
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can view readings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        
        # Query parameters
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 50))
        
        # Get readings from last N days
        since = timezone.now() - timedelta(days=days)
        readings = LatexQualityReading.objects.filter(
            farmer=farmer,
            timestamp__gte=since
        ).order_by('-timestamp')[:limit]
        
        serializer = LatexQualityReadingSerializer(readings, many=True)
        
        return Response({
            'count': readings.count(),
            'period_days': days,
            'readings': serializer.data
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== DASHBOARD STATS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """
    Get farmer's latex quality dashboard statistics
    GET /api/latex-quality/dashboard/?days=7
    """
    try:
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can view dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        # Get readings
        readings = LatexQualityReading.objects.filter(
            farmer=farmer,
            timestamp__gte=since
        )
        
        # Calculate aggregated statistics
        stats = readings.aggregate(
            total_readings=Count('id'),
            avg_quality_score=Avg('quality_score'),
            avg_ph=Avg('ph_value'),
            avg_turbidity=Avg('turbidity_ntu'),
            avg_drc=Avg('drc_percent'),
        )
        
        # Grade distribution
        grade_counts = readings.values('rss_grade').annotate(count=Count('id'))
        grade_dist = {item['rss_grade']: item['count'] for item in grade_counts}
        
        total = stats['total_readings'] or 1  # Avoid division by zero
        
        # Calculate percentages
        rss1_count = grade_dist.get('RSS1', 0)
        excellent_count = readings.filter(quality_status='EXCELLENT').count()
        
        # Unread alerts
        unread_alerts = LatexQualityAlert.objects.filter(
            farmer=farmer,
            is_read=False
        ).count()
        
        return Response({
            'period_days': days,
            'total_readings': total,
            'avg_quality_score': round(stats['avg_quality_score'] or 0, 1),
            'avg_ph': round(stats['avg_ph'] or 0, 2),
            'avg_turbidity': round(stats['avg_turbidity'] or 0, 1),
            'avg_drc': round(stats['avg_drc'] or 0, 1),
            
            # Grade distribution
            'rss1_count': rss1_count,
            'rss2_count': grade_dist.get('RSS2', 0),
            'rss3_count': grade_dist.get('RSS3', 0),
            'rss4_count': grade_dist.get('RSS4', 0),
            'rejected_count': grade_dist.get('REJECTED', 0),
            
            # Percentages
            'rss1_percent': round((rss1_count / total) * 100, 1),
            'excellent_percent': round((excellent_count / total) * 100, 1),
            
            'unread_alerts': unread_alerts
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== GET ALERTS ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quality_alerts(request):
    """
    Get farmer's quality alerts
    GET /api/latex-quality/alerts/?unread_only=true
    """
    try:
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can view alerts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        
        alerts = LatexQualityAlert.objects.filter(farmer=farmer)
        
        if unread_only:
            alerts = alerts.filter(is_read=False)
        
        alerts = alerts.order_by('-created_at')[:50]
        
        serializer = LatexQualityAlertSerializer(alerts, many=True)
        
        return Response({
            'count': alerts.count(),
            'alerts': serializer.data
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== MARK ALERT READ ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """
    Mark alert as read
    POST /api/latex-quality/alerts/<alert_id>/read/
    """
    try:
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can mark alerts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        
        alert = LatexQualityAlert.objects.get(
            id=alert_id,
            farmer=farmer
        )
        
        alert.is_read = True
        alert.read_at = timezone.now()
        alert.save()
        
        return Response({
            'status': 'success',
            'message': 'Alert marked as read'
        })
    
    except LatexQualityAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== MARK ALL ALERTS READ ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_alerts_read(request):
    """
    Mark all farmer's alerts as read
    POST /api/latex-quality/alerts/read-all/
    """
    try:
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'error': 'Only farmers can mark alerts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        farmer = request.user.farmer_profile
        
        updated_count = LatexQualityAlert.objects.filter(
            farmer=farmer,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'message': f'{updated_count} alerts marked as read'
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
