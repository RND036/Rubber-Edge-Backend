from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


def default_effective_to():
    """Default function for effective_to"""
    return timezone.now() + timezone.timedelta(days=1)


class BuyerPrice(models.Model):
    """Model for storing buyer prices for different rubber grades"""
    
    GRADE_CHOICES = [
        ('rss1', 'RSS1'),
        ('rss2', 'RSS2'),
        ('rss3', 'RSS3'),
        ('rss4', 'RSS4'),
        ('rss5', 'RSS5'),
        ('latex', 'Latex 60%'),
        ('tsr20', 'TSR20'),
        ('crepe', 'Crepe'),
        ('custom', 'Custom Grade'),
    ]
    
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_prices',
        limit_choices_to={'role': 'buyer'}
    )
    grade = models.CharField(max_length=50, choices=GRADE_CHOICES, db_index=True)
    custom_grade_name = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price in LKR per kilogram"
    )
    notes = models.TextField(max_length=1000, null=True, blank=True)
    effective_from = models.DateTimeField(default=timezone.now, db_index=True)
    effective_to = models.DateTimeField(default=default_effective_to, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'buyer_prices'
        verbose_name = 'Buyer Price'
        verbose_name_plural = 'Buyer Prices'
        ordering = ['-effective_from', '-created_at']
        indexes = [
            models.Index(fields=['buyer', 'effective_from', 'is_active']),
            models.Index(fields=['grade', 'effective_from']),
        ]
        unique_together = [['buyer', 'grade', 'custom_grade_name', 'effective_from', 'is_active']]
    
    def __str__(self):
        grade_display = self.custom_grade_name if self.grade == 'custom' else self.get_grade_display()
        return f"{self.buyer.phone_number} - {grade_display}: LKR {self.price}"
    
    @property
    def grade_display(self):
        """Get human-readable grade name"""
        if self.grade == 'custom':
            return self.custom_grade_name or 'Custom Grade'
        return dict(self.GRADE_CHOICES).get(self.grade, self.grade)
    
    @property
    def effective_date(self):
        """Return the date portion of effective_from for compatibility with frontend"""
        return self.effective_from.date()
    
    def save(self, *args, **kwargs):
        """Deactivate previous prices for same grade in overlapping period"""
        if self.is_active:
            BuyerPrice.objects.filter(
                buyer=self.buyer,
                grade=self.grade,
                custom_grade_name=self.custom_grade_name,
                is_active=True,
                effective_to__gte=self.effective_from,
                effective_from__lte=self.effective_to
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def is_currently_active(self):
        """Check if price is currently active"""
        now = timezone.now()
        return self.is_active and self.effective_from <= now <= self.effective_to


class PriceAlert(models.Model):
    """Model for farmer price alerts"""
    
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='price_alerts',
        limit_choices_to={'role': 'farmer'}
    )
    grade = models.CharField(max_length=50, choices=BuyerPrice.GRADE_CHOICES)
    target_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'price_alerts'
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'
        ordering = ['-created_at']
        unique_together = [['farmer', 'grade', 'is_active']]
    
    def __str__(self):
        return f"{self.farmer.phone_number} - {self.get_grade_display()}: LKR {self.target_price}"
