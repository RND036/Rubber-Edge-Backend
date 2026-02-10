from rest_framework import serializers
from .models import LatexQualityReading, LatexQualityAlert
from django.utils.timesince import timesince

class LatexQualityReadingCreateSerializer(serializers.Serializer):
    """Serializer for creating readings from mobile app"""
    
    ph_value = serializers.FloatField(min_value=0, max_value=14)
    turbidity_ntu = serializers.FloatField(min_value=0)
    drc_percent = serializers.FloatField(min_value=0, max_value=100)
    temperature_celsius = serializers.FloatField(required=False, allow_null=True)
    humidity_percent = serializers.FloatField(
        required=False, 
        allow_null=True,
        min_value=0,
        max_value=100
    )
    notes = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=1000
    )
    
    def validate(self, data):
        """Custom validation"""
        # Check if pH is realistic
        if data['ph_value'] < 4 or data['ph_value'] > 12:
            raise serializers.ValidationError({
                'ph_value': 'pH value seems unrealistic. Please check your measurement.'
            })
        
        # Check if turbidity is reasonable
        if data['turbidity_ntu'] > 2000:
            raise serializers.ValidationError({
                'turbidity_ntu': 'Turbidity seems too high. Please verify measurement.'
            })
        
        return data

class LatexQualityReadingSerializer(serializers.ModelSerializer):
    """Serializer for displaying readings"""
    
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)
    farmer_phone = serializers.CharField(source='farmer.user.phone_number', read_only=True)
    farmer_district = serializers.CharField(source='farmer.district', read_only=True)
    
    time_ago = serializers.SerializerMethodField()
    grade_display = serializers.CharField(source='get_rss_grade_display', read_only=True)
    status_display = serializers.CharField(source='get_quality_status_display', read_only=True)
    
    # Format prices
    estimated_price_lkr = serializers.SerializerMethodField()
    
    class Meta:
        model = LatexQualityReading
        fields = [
            'id',
            'farmer_name',
            'farmer_phone',
            'farmer_district',
            'ph_value',
            'turbidity_ntu',
            'drc_percent',
            'temperature_celsius',
            'humidity_percent',
            'rss_grade',
            'grade_display',
            'quality_status',
            'status_display',
            'quality_score',
            'estimated_price_per_kg',
            'estimated_price_lkr',
            'timestamp',
            'time_ago',
            'notes',
        ]
        read_only_fields = [
            'id', 'rss_grade', 'quality_status', 
            'quality_score', 'estimated_price_per_kg', 'timestamp'
        ]
    
    def get_time_ago(self, obj):
        return timesince(obj.timestamp) + " ago"
    
    def get_estimated_price_lkr(self, obj):
        if obj.estimated_price_per_kg:
            return f"LKR {obj.estimated_price_per_kg:.2f}/kg"
        return None

class LatexQualityAlertSerializer(serializers.ModelSerializer):
    """Serializer for quality alerts"""
    
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    # Include reading summary
    reading_grade = serializers.CharField(source='reading.rss_grade', read_only=True)
    reading_score = serializers.IntegerField(source='reading.quality_score', read_only=True)
    
    class Meta:
        model = LatexQualityAlert
        fields = [
            'id',
            'reading',
            'reading_grade',
            'reading_score',
            'alert_type',
            'alert_type_display',
            'severity',
            'severity_display',
            'message',
            'recommendations',
            'is_read',
            'created_at',
            'time_ago',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_time_ago(self, obj):
        return timesince(obj.created_at) + " ago"

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_readings = serializers.IntegerField()
    avg_quality_score = serializers.FloatField()
    avg_ph = serializers.FloatField()
    avg_turbidity = serializers.FloatField()
    avg_drc = serializers.FloatField()
    
    # Grade distribution
    rss1_count = serializers.IntegerField()
    rss2_count = serializers.IntegerField()
    rss3_count = serializers.IntegerField()
    rss4_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    
    # Percentages
    rss1_percent = serializers.FloatField()
    excellent_percent = serializers.FloatField()
    
    unread_alerts = serializers.IntegerField()
