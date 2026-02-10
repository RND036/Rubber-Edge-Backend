from django.contrib import admin
from .models import LatexQualityReading, LatexQualityAlert

@admin.register(LatexQualityReading)
class LatexQualityReadingAdmin(admin.ModelAdmin):
    list_display = [
        'farmer', 'rss_grade', 'quality_score', 
        'ph_value', 'turbidity_ntu', 'drc_percent',
        'estimated_price_per_kg', 'timestamp'
    ]
    list_filter = [
        'rss_grade', 
        'quality_status', 
        'timestamp',
        'farmer__district'
    ]
    search_fields = [
        'farmer__name', 
        'farmer__user__phone_number',
        'notes'
    ]
    readonly_fields = [
        'id', 'rss_grade', 'quality_status', 
        'quality_score', 'estimated_price_per_kg',
        'created_at', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Farmer Information', {
            'fields': ('farmer',)
        }),
        ('Quality Measurements', {
            'fields': (
                ('ph_value', 'turbidity_ntu', 'drc_percent'),
                ('temperature_celsius', 'humidity_percent'),
            )
        }),
        ('Quality Assessment (Auto-calculated)', {
            'fields': (
                ('rss_grade', 'quality_status'),
                ('quality_score', 'estimated_price_per_kg'),
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'timestamp', 'created_at', 'id'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Readings should come from mobile app
        return False

@admin.register(LatexQualityAlert)
class LatexQualityAlertAdmin(admin.ModelAdmin):
    list_display = [
        'farmer', 'alert_type', 'severity', 
        'is_read', 'created_at'
    ]
    list_filter = [
        'alert_type', 
        'severity', 
        'is_read',
        'created_at'
    ]
    search_fields = [
        'farmer__name',
        'message',
        'recommendations'
    ]
    readonly_fields = ['id', 'created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Alert Information', {
            'fields': (
                'farmer',
                'reading',
                'alert_type',
                'severity',
            )
        }),
        ('Details', {
            'fields': ('message', 'recommendations')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
