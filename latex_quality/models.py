from django.db import models
from django.utils import timezone
from users.models import FarmerProfile
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class LatexQualityReading(models.Model):
    """Latex quality measurement by farmer"""
    
    RSS_GRADES = [
        ('RSS1', 'RSS1 - Premium Grade'),
        ('RSS2', 'RSS2 - High Quality'),
        ('RSS3', 'RSS3 - Standard Quality'),
        ('RSS4', 'RSS4 - Low Quality'),
        ('REJECTED', 'Rejected - Poor Quality'),
    ]
    
    QUALITY_STATUS = [
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name='latex_readings'
    )
    
    # Sensor readings (manual input from mobile app)
    ph_value = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(14)],
        help_text="pH level (0-14)"
    )
    turbidity_ntu = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Turbidity in NTU (Nephelometric Turbidity Units)"
    )
    drc_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Dry Rubber Content (%)"
    )
    
    # Optional environmental data
    temperature_celsius = models.FloatField(
        null=True, 
        blank=True,
        help_text="Ambient temperature in Celsius"
    )
    humidity_percent = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Relative humidity (%)"
    )
    
    # Quality assessment (auto-calculated on save)
    rss_grade = models.CharField(
        max_length=20, 
        choices=RSS_GRADES, 
        db_index=True,
        editable=False
    )
    quality_status = models.CharField(
        max_length=20, 
        choices=QUALITY_STATUS,
        editable=False
    )
    quality_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall quality score (0-100)",
        editable=False
    )
    
    # Pricing recommendation (LKR per kg)
    estimated_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Estimated price in LKR per kg based on grade"
    )
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    notes = models.TextField(blank=True, help_text="Additional notes from farmer")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'latex_quality_readings'
        ordering = ['-timestamp']
        verbose_name = 'Latex Quality Reading'
        verbose_name_plural = 'Latex Quality Readings'
        indexes = [
            models.Index(fields=['farmer', '-timestamp']),
            models.Index(fields=['rss_grade']),
            models.Index(fields=['quality_status']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate quality metrics before saving
        if not self.rss_grade or not self.quality_score:
            self.calculate_quality()
        super().save(*args, **kwargs)
    
    def calculate_quality(self):
        """
        Calculate RSS grade and quality score based on pH, turbidity, and DRC
        Based on Sri Lankan rubber industry standards
        """
        
        # === pH SCORING ===
        # Fresh latex optimal pH: 6.5-7.0
        # Preserved latex: 9.0-10.0 (with ammonia)
        if 6.5 <= self.ph_value <= 7.0:
            ph_score = 100  # Perfect fresh latex
        elif 6.0 <= self.ph_value < 6.5 or 7.0 < self.ph_value <= 7.5:
            ph_score = 85   # Good
        elif 9.0 <= self.ph_value <= 10.0:
            ph_score = 80   # Well-preserved latex
        elif 5.5 <= self.ph_value < 6.0 or 7.5 < self.ph_value < 9.0:
            ph_score = 65   # Acceptable
        else:
            ph_score = 30   # Poor (spoilage or excess preservative)
        
        # === TURBIDITY SCORING ===
        # Lower turbidity = cleaner latex = better quality
        if self.turbidity_ntu < 200:
            turbidity_score = 100  # Excellent clarity
        elif self.turbidity_ntu < 300:
            turbidity_score = 90   # Very good
        elif self.turbidity_ntu < 500:
            turbidity_score = 70   # Acceptable
        elif self.turbidity_ntu < 800:
            turbidity_score = 50   # Poor
        else:
            turbidity_score = 30   # Very poor (contaminated)
        
        # === DRC SCORING ===
        # Higher DRC = more rubber content = better quality
        if self.drc_percent >= 35:
            drc_score = 100  # Excellent
        elif self.drc_percent >= 30:
            drc_score = 85   # Very good
        elif self.drc_percent >= 25:
            drc_score = 70   # Good
        elif self.drc_percent >= 20:
            drc_score = 50   # Fair
        else:
            drc_score = 30   # Poor (too diluted)
        
        # === WEIGHTED FINAL SCORE ===
        # DRC is most important (40%), then turbidity (30%), then pH (30%)
        final_score = int(
            (drc_score * 0.4) + 
            (turbidity_score * 0.3) + 
            (ph_score * 0.3)
        )
        
        # === DETERMINE RSS GRADE ===
        # RSS (Ribbed Smoked Sheet) grading system
        if final_score >= 90 and self.drc_percent >= 35 and self.turbidity_ntu < 200:
            grade = 'RSS1'
            status = 'EXCELLENT'
            price = 450.00  # LKR per kg
        elif final_score >= 80 and self.drc_percent >= 30 and self.turbidity_ntu < 300:
            grade = 'RSS2'
            status = 'GOOD'
            price = 400.00
        elif final_score >= 65 and self.drc_percent >= 25 and self.turbidity_ntu < 500:
            grade = 'RSS3'
            status = 'FAIR'
            price = 350.00
        elif final_score >= 50 and self.drc_percent >= 20:
            grade = 'RSS4'
            status = 'FAIR'
            price = 300.00
        else:
            grade = 'REJECTED'
            status = 'POOR'
            price = 200.00
        
        self.rss_grade = grade
        self.quality_status = status
        self.quality_score = final_score
        self.estimated_price_per_kg = price
    
    def __str__(self):
        return f"{self.farmer.name} - {self.rss_grade} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

class LatexQualityAlert(models.Model):
    """Alerts for quality issues requiring farmer attention"""
    
    ALERT_TYPES = [
        ('LOW_QUALITY', 'Low Quality Detected'),
        ('HIGH_TURBIDITY', 'High Turbidity'),
        ('ABNORMAL_PH', 'Abnormal pH Level'),
        ('LOW_DRC', 'Low Dry Rubber Content'),
        ('SPOILAGE_RISK', 'Spoilage Risk'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name='quality_alerts'
    )
    reading = models.ForeignKey(
        LatexQualityReading,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, db_index=True)
    message = models.TextField(help_text="Alert message for farmer")
    recommendations = models.TextField(
        blank=True,
        help_text="Actionable recommendations to fix the issue"
    )
    
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'latex_quality_alerts'
        ordering = ['-created_at']
        verbose_name = 'Latex Quality Alert'
        verbose_name_plural = 'Latex Quality Alerts'
        indexes = [
            models.Index(fields=['farmer', '-created_at']),
            models.Index(fields=['severity', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.farmer.name} ({self.severity})"
