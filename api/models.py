from django.db import models
from django.conf import settings  # Changed: Import settings instead of User
from decimal import Decimal


class RubberPrice(models.Model):
    """Store RRISL rubber prices from auctions"""
    grade = models.CharField(max_length=50)  # RSS1, RSS2, RSS3, etc.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='LKR')
    auction_date = models.DateField()
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-auction_date', 'grade']
        unique_together = ['grade', 'auction_date']
        indexes = [
            models.Index(fields=['-auction_date']),
            models.Index(fields=['grade']),
        ]
    
    def __str__(self):
        return f"{self.grade} - Rs.{self.price} ({self.auction_date})"
    
    def calculate_change(self):
        """Calculate percentage change from previous auction"""
        try:
            previous = RubberPrice.objects.filter(
                grade=self.grade,
                auction_date__lt=self.auction_date
            ).first()
            
            if previous:
                change = ((self.price - previous.price) / previous.price) * 100
                self.change_percentage = round(change, 2)
                self.save(update_fields=['change_percentage'])
        except Exception as e:
            print(f"Error calculating change: {e}")


class MarketStats(models.Model):
    """Store market statistics"""
    date = models.DateField(unique=True)
    week_high = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    week_low = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_high = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_low = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_volume = models.CharField(max_length=50, default='N/A')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Market Statistic'
        verbose_name_plural = 'Market Statistics'
    
    def __str__(self):
        return f"Stats for {self.date}"


class ScrapingLog(models.Model):
    """Log scraping activities"""
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    grades_scraped = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    source_url = models.URLField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        return f"{status} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} ({self.grades_scraped} grades)"


class DiseaseDetectionLog(models.Model):
    """Log disease detection requests"""
    timestamp = models.DateTimeField(auto_now_add=True)
    disease_detected = models.CharField(max_length=100)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    image_size = models.CharField(max_length=50, blank=True)
    processing_time_ms = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Disease Detection Log'
        verbose_name_plural = 'Disease Detection Logs'
    
    def __str__(self):
        return f"{self.disease_detected} ({self.confidence}%) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# ============================================
# CHATBOT MODELS
# ============================================
class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Changed: Use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']
    
    def __str__(self):
        user_info = f" - {self.user.phone_number}" if self.user else ""
        return f"Session {self.session_id}{user_info}"


class ChatMessage(models.Model):
    MESSAGE_TYPES = [('user', 'User'), ('bot', 'Bot'), ('system', 'System')]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"


class DiseaseQuery(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    disease_name = models.CharField(max_length=200, blank=True)
    query_text = models.TextField()
    bot_response = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'disease_queries'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Disease Query: {self.disease_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class ShopQuery(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    product_type = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    query_text = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shop_queries'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Shop Query: {self.product_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
