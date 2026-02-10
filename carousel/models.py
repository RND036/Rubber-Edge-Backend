from django.db import models
from django.core.validators import RegexValidator


class CarouselItem(models.Model):
    """
    Carousel items for officer dashboard hero section
    Only image is required, all text fields are optional
    """
    
    # Content Fields (ALL OPTIONAL)
    title = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Optional: Main heading (e.g., 'Rubber Market Price')"
    )
    value = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Optional: Primary value/metric (e.g., 'RSS-1: LKR 885.00')"
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Optional: Supporting text (e.g., '+2.5% from yesterday')"
    )
    
    # Visual Fields
    image = models.ImageField(
        upload_to='carousel/%Y/%m/',
        help_text="Required: Background image for carousel (recommended: 1200x600px)",
        blank=False,  # Required field
        null=False    # Required field
    )
    
    color_validator = RegexValidator(
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        message='Enter a valid hex color code (e.g., #1B5E20)'
    )
    color = models.CharField(
        max_length=7,
        default='#1B5E20',
        validators=[color_validator],
        help_text="Overlay color for text (if text is present)"
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Optional: Ionicon name (e.g., trending-up, water-outline)"
    )
    
    # Display Settings
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this item is visible in the carousel"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Carousel Item'
        verbose_name_plural = 'Carousel Items'
        indexes = [
            models.Index(fields=['order', 'is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        if self.title:
            return f"{self.order}. {self.title}"
        return f"{self.order}. Carousel Image #{self.id}"
    
    def save(self, *args, **kwargs):
        # Auto-increment order if not set
        if self.order == 0 and not self.pk:
            max_order = CarouselItem.objects.aggregate(
                models.Max('order')
            )['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)
