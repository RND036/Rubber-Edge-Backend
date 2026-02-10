from django.contrib import admin
from .models import RubberPrice, MarketStats, ScrapingLog
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import traceback
from .models import DiseaseDetectionLog
import time
from .models import *  # Chat models, DiseaseQuery, ShopQuery

@admin.register(RubberPrice)
class RubberPriceAdmin(admin.ModelAdmin):
    change_list_template = 'admin/api/rubber_price/change_list.html'
    
    list_display = ['grade', 'price_display', 'currency', 'auction_date', 'change_display', 'updated_at']
    list_filter = ['auction_date', 'currency', 'grade']
    search_fields = ['grade']
    ordering = ['-auction_date', 'grade']
    date_hierarchy = 'auction_date'
    
    def price_display(self, obj):
        return format_html(
            '<strong style="color: #27ae60;">Rs. {}</strong>',
            obj.price
        )
    price_display.short_description = 'Price'
    
    def change_display(self, obj):
        if obj.change_percentage > 0:
            return format_html(
                '<span style="color: #27ae60;">▲ {}%</span>',
                obj.change_percentage
            )
        elif obj.change_percentage < 0:
            return format_html(
                '<span style="color: #e74c3c;">▼ {}%</span>',
                abs(obj.change_percentage)
            )
        return '—'
    change_display.short_description = 'Change'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-entry/', self.admin_site.admin_view(self.bulk_entry_view), name='bulk_price_entry'),
            path('trigger-scrape/', self.admin_site.admin_view(self.trigger_scrape_view), name='trigger_scrape'),
        ]
        return custom_urls + urls
    
    def bulk_entry_view(self, request):
        """Bulk price entry form"""
        if request.method == 'POST':
            auction_date = request.POST.get('auction_date')
            
            grades = [
                'LATEX CREPE 1X', 'LATEX CREPE 1', 'LATEX CREPE 2', 'LATEX CREPE 3', 'LATEX CREPE 4',
                'SC.CR. 1X(BR)', 'SC.CR. 2X(BR)', 'SC.CR. 3X(BR)', 'SC.CR. 4X(BR)',
                'SKIM CREPE', 'FLAT BARK', 'RSS1', 'RSS2', 'RSS3', 'RSS4', 'RSS5',
            ]
            
            count = 0
            for grade in grades:
                price_str = request.POST.get(f'price_{grade}', '').strip()
                
                if price_str and price_str != '' and price_str != '0':
                    try:
                        price = Decimal(price_str)
                        
                        if price > 0:
                            obj, created = RubberPrice.objects.update_or_create(
                                grade=grade,
                                auction_date=auction_date,
                                defaults={
                                    'price': price,
                                    'currency': 'LKR'
                                }
                            )
                            obj.calculate_change()
                            count += 1
                            
                    except (ValueError, Decimal.InvalidOperation):
                        continue
            
            messages.success(request, f'✅ Successfully added/updated {count} prices for {auction_date}')
            return redirect('/admin/api/rubberprice/')
        
        # GET request - show form
        context = {
            'title': 'Bulk Price Entry',
            'today': date.today().isoformat(),
        }
        return render(request, 'admin/bulk_price_entry.html', context)
    
    def trigger_scrape_view(self, request):
        """Trigger RRISL scraping manually"""
        from api.tasks import scrape_rrisl_prices_task
        
        if request.method == 'POST':
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    # Trigger async scraping task
                    task = scrape_rrisl_prices_task.delay()
                    
                    # Wait for task to complete (with timeout)
                    start_time = time.time()
                    result = task.get(timeout=30)
                    elapsed_time = round(time.time() - start_time, 1)
                    
                    # Check for both 'success' and 'status' keys (handle both return formats)
                    is_success = result.get('success') or result.get('status') == 'success'
                    
                    if result and is_success:
                        prices = result.get('prices', [])
                        count = result.get('count', len(prices))
                        
                        return JsonResponse({
                            'success': True,
                            'grades_count': count,
                            'message': f'Successfully scraped {count} rubber grades',
                            'time_taken': elapsed_time
                        })
                    else:
                        error_msg = result.get('error', 'No data returned from scraper')
                        return JsonResponse({
                            'success': False,
                            'error': f'Scraping failed: {error_msg}',
                            'details': f'Response from scraper:\n{str(result)}\n\n' +
                                     'This usually means:\n' +
                                     '1. No prices were found on the RRISL website\n' +
                                     '2. OCR failed to extract price data\n' +
                                     '3. The price image format has changed\n\n' +
                                     'Check the scraping logs for more details.'
                        })
                        
                except TimeoutError as e:
                    return JsonResponse({
                        'success': False,
                        'error': 'Scraping timed out after 30 seconds',
                        'details': 'The scraping process took too long. This might be due to:\n' +
                                 '1. Slow internet connection\n' +
                                 '2. RRISL website is down or slow\n' +
                                 '3. Large image file taking time to download\n\n' +
                                 'Please try again or check your connection.'
                    })
                    
                except ConnectionError as e:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot connect to Celery worker',
                        'details': 'Connection Error:\n' +
                                 str(e) + '\n\n' +
                                 'Make sure Celery worker is running:\n' +
                                 '  celery -A rubber_farm_api worker -l info\n\n' +
                                 'Also check Redis is running:\n' +
                                 '  redis-cli ping'
                    })
                    
                except Exception as e:
                    # Get full traceback
                    error_trace = traceback.format_exc()
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    return JsonResponse({
                        'success': False,
                        'error': f'{error_type}: {error_msg}',
                        'details': f'Error Type: {error_type}\n' +
                                 f'Error Message: {error_msg}\n\n' +
                                 f'Full Traceback:\n{error_trace}\n\n' +
                                 'Common Causes:\n' +
                                 '1. Celery worker not running\n' +
                                 '2. Redis not running\n' +
                                 '3. OCR libraries (tesseract) not installed\n' +
                                 '4. Network connection issues\n' +
                                 '5. RRISL website is down'
                    })
            else:
                # Regular form submission (fallback)
                try:
                    task = scrape_rrisl_prices_task.delay()
                    messages.success(
                        request, 
                        f'🔄 RRISL scraping started! Task ID: {task.id}. Prices will be updated shortly.'
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f'❌ Failed to start scraping: {str(e)}'
                    )
                return redirect('/admin/api/rubberprice/')
        
        # GET request - show confirmation page
        context = {
            'title': 'Trigger RRISL Scraping',
        }
        return render(request, 'admin/trigger_scrape.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Add custom buttons to changelist"""
        extra_context = extra_context or {}
        extra_context['show_bulk_entry_button'] = True
        extra_context['show_scrape_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(MarketStats)
class MarketStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'week_high', 'week_low', 'month_high', 'month_low', 'avg_volume']
    list_filter = ['date']
    ordering = ['-date']
    date_hierarchy = 'date'

@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'success_display', 'grades_scraped', 'error_preview', 'source_url']
    list_filter = ['success', 'timestamp']
    search_fields = ['error_message']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'success', 'grades_scraped', 'error_message', 'source_url']
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: #27ae60;">✅ Success</span>')
        return format_html('<span style="color: #e74c3c;">❌ Failed</span>')
    success_display.short_description = 'Status'
    
    def error_preview(self, obj):
        if obj.error_message:
            return obj.error_message[:100] + '...' if len(obj.error_message) > 100 else obj.error_message
        return '—'
    error_preview.short_description = 'Error'

@admin.register(DiseaseDetectionLog)
class DiseaseDetectionLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'disease_detected', 'confidence_display', 'processing_time_display', 'success_display']
    list_filter = ['success', 'disease_detected', 'timestamp']
    search_fields = ['disease_detected', 'error_message']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'disease_detected', 'confidence', 'image_size', 'processing_time_ms', 'success', 'error_message']
    
    def confidence_display(self, obj):
        """✅ FIXED: Safely convert confidence to float before formatting"""
        try:
            conf = float(obj.confidence) if obj.confidence else 0.0
            color = '#27ae60' if conf >= 70 else '#f39c12' if conf >= 50 else '#e74c3c'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, conf)
        except (ValueError, TypeError):
            return format_html('<span style="color: red;">Invalid</span>')
    confidence_display.short_description = 'Confidence'
    
    def processing_time_display(self, obj):
        return f'{obj.processing_time_ms} ms'
    processing_time_display.short_description = 'Time'
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: #27ae60;">✅</span>')
        return format_html('<span style="color: #e74c3c;">❌</span>')
    success_display.short_description = 'Status'

# Chatbot admin
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'created_at', 'is_active', 'message_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['session_id']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content']
    
    def session_id(self, obj):
        return obj.session.session_id[:8] + '...'
    session_id.short_description = 'Session'
    
    def content_preview(self, obj):
        preview = obj.content[:100]
        return preview + '...' if len(obj.content) > 100 else preview

@admin.register(DiseaseQuery)
class DiseaseQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'disease_name', 'query_preview', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['disease_name', 'query_text', 'bot_response']
    readonly_fields = ['timestamp']

    def query_preview(self, obj):
        text = obj.query_text or ""
        return text[:50] + '...' if len(text) > 50 else text
    query_preview.short_description = 'Query'

@admin.register(ShopQuery)
class ShopQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_type', 'location', 'query_preview', 'timestamp']
    list_filter = ['timestamp', 'location']
    search_fields = ['product_type', 'location', 'query_text']
    readonly_fields = ['timestamp']

    def query_preview(self, obj):
        text = obj.query_text or ""
        return text[:50] + '...' if len(text) > 50 else text
    query_preview.short_description = 'Query'
