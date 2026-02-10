from django.contrib import admin
from .models import BuyerPrice, PriceAlert


@admin.register(BuyerPrice)
class BuyerPriceAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'grade_display', 'price', 'effective_from', 'effective_to', 'is_active', 'created_at']
    list_filter = ['grade', 'is_active', 'effective_from', 'effective_to', 'created_at']
    search_fields = ['buyer__phone_number', 'grade', 'custom_grade_name']
    ordering = ['-effective_from', '-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Buyer Information', {
            'fields': ('buyer',)
        }),
        ('Price Details', {
            'fields': ('grade', 'custom_grade_name', 'price', 'notes')
        }),
        ('Status', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'grade', 'target_price', 'is_active', 'created_at']
    list_filter = ['grade', 'is_active', 'created_at']
    search_fields = ['farmer__phone_number']
    ordering = ['-created_at']
