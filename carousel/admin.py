from django.contrib import admin
from django.utils.html import format_html
from .models import CarouselItem


@admin.register(CarouselItem)
class CarouselItemAdmin(admin.ModelAdmin):
    """
    Admin interface for managing carousel items
    Focus on image uploads with optional text overlays
    Compatible with custom User model
    """
    
    list_display = [
        'order_display',
        'image_preview',
        'title_display',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'value',
        'subtitle',
    ]
    
    list_editable = [
        'is_active'
    ]
    
    ordering = ['order', '-created_at']
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'image_preview_large'
    ]
    
    fieldsets = (
        ('Image Upload (Required)', {
            'fields': (
                'image',
                'image_preview_large',
            ),
            'description': '⚠️ Image is required - Upload carousel image here'
        }),
        ('Optional Text Overlay', {
            'fields': (
                'title',
                'value',
                'subtitle',
                'color',
                'icon',
            ),
            'classes': ('collapse',),
            'description': '📝 Optional: Add text overlay on the image (leave empty for image-only carousel)'
        }),
        ('Display Settings', {
            'fields': (
                'order',
                'is_active'
            ),
            'description': 'Control visibility and ordering'
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',),
            'description': 'System information'
        }),
    )
    
    actions = [
        'activate_items',
        'deactivate_items',
        'move_to_top',
        'duplicate_item'
    ]
    
    # ========== CUSTOM DISPLAY METHODS ==========
    def order_display(self, obj):
        """Display order with badge styling"""
        return format_html(
            '<span style="background: #1B5E20; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-weight: bold; font-size: 12px;">{}</span>',
            obj.order
        )
    order_display.short_description = 'Order'
    
    def title_display(self, obj):
        """Display title or 'Image Only'"""
        if obj.title:
            return obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
        return format_html('<em style="color: #999;">📷 Image Only</em>')
    title_display.short_description = 'Title'
    
    def image_preview(self, obj):
        """Display image preview in list"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 60px; '
                'object-fit: cover; border-radius: 6px; border: 2px solid #1B5E20; '
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return format_html('<span style="color: red; font-weight: bold;">❌ No Image</span>')
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        """Display large image preview in detail view"""
        if obj.image:
            return format_html(
                '<div style="margin: 20px 0;">'
                '<img src="{}" style="max-width: 700px; width: 100%; height: auto; '
                'border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />'
                '<p style="margin-top: 10px; color: #666; font-size: 12px;">'
                '📁 File: {} | 🔗 <a href="{}" target="_blank">View Full Size</a></p>'
                '</div>',
                obj.image.url,
                obj.image.name,
                obj.image.url
            )
        return format_html(
            '<div style="padding: 40px; background: #f5f5f5; border-radius: 8px; text-align: center;">'
            '<p style="color: #999; font-size: 14px; margin: 0;">⚠️ No image uploaded yet</p>'
            '</div>'
        )
    image_preview_large.short_description = 'Image Preview'
    
    # ========== CUSTOM ACTIONS ==========
    def activate_items(self, request, queryset):
        """Activate selected items"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} item(s) activated successfully.')
    activate_items.short_description = '✓ Activate selected items'
    
    def deactivate_items(self, request, queryset):
        """Deactivate selected items"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'⏸️ {updated} item(s) deactivated successfully.')
    deactivate_items.short_description = '✗ Deactivate selected items'
    
    def move_to_top(self, request, queryset):
        """Move selected items to top of order"""
        for item in queryset:
            item.order = 0
            item.save()
        self.message_user(request, f'⬆️ {queryset.count()} item(s) moved to top.')
    move_to_top.short_description = '↑ Move to top'
    
    def duplicate_item(self, request, queryset):
        """Duplicate selected items"""
        count = 0
        for item in queryset:
            # Save old image
            old_image = item.image
            
            # Create new item
            item.pk = None
            item.title = f"{item.title} (Copy)" if item.title else ""
            item.is_active = False
            item.image = old_image  # Keep same image
            item.save()
            count += 1
        self.message_user(request, f'📋 {count} item(s) duplicated successfully.')
    duplicate_item.short_description = '📋 Duplicate selected items'
    
    # ========== DISABLE ADMIN LOGGING (FIX FOR CUSTOM USER) ==========
    def log_addition(self, request, object, message):
        """Disable admin logging to avoid custom User model issues"""
        pass
    
    def log_change(self, request, object, message):
        """Disable admin logging to avoid custom User model issues"""
        pass
    
    def log_deletion(self, request, object, object_repr):
        """Disable admin logging to avoid custom User model issues"""
        pass
    
    # ========== SAVE MODEL ==========
    def save_model(self, request, obj, form, change):
        """Save carousel item"""
        super().save_model(request, obj, form, change)
