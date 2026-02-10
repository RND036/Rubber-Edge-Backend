from django.contrib import admin
from .models import Event, EventAttendance


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'location', 'created_by', 'is_active', 'is_cancelled', 'created_at']
    list_filter = ['is_active', 'is_cancelled', 'event_date', 'created_at']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'event_date', 'location', 'image')
        }),
        ('Event Details', {
            'fields': ('max_participants', 'contact_number')
        }),
        ('Status', {
            'fields': ('is_active', 'is_cancelled')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ['event', 'farmer', 'status', 'registered_at']
    list_filter = ['status', 'registered_at']
    search_fields = ['event__title', 'farmer__username', 'farmer__email']
    readonly_fields = ['registered_at']
    date_hierarchy = 'registered_at'
