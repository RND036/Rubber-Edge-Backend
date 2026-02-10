from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from datetime import timedelta


class UserManager(BaseUserManager):
    """Custom manager for User model"""
    
    def create_user(self, phone_number, role, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        user = self.model(phone_number=phone_number, role=role, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, role='officer', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, role, password, **extra_fields)
    
    def get_by_natural_key(self, phone_number):
        """Get user by phone number - required for Django authentication"""
        return self.get(**{self.model.USERNAME_FIELD: phone_number})


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model with phone authentication"""
    
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('officer', 'Rubber Officer'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+94[0-9]{9}$',
        message="Phone number must be in format: '+94771234567'"
    )
    
    phone_number = models.CharField(validators=[phone_regex], max_length=15, unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    failed_otp_attempts = models.IntegerField(default=0)
    last_otp_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['role']
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone_number} ({self.get_role_display()})"
    
    def get_username(self):
        """Return the username for this User"""
        return getattr(self, self.USERNAME_FIELD)
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser


class FarmerProfile(models.Model):
    """Farmer profile"""
    
    DISTRICT_CHOICES = [
        ('Kalutara', 'Kalutara'), ('Galle', 'Galle'), ('Matara', 'Matara'),
        ('Ratnapura', 'Ratnapura'), ('Kegalle', 'Kegalle'), ('Moneragala', 'Moneragala'),
        ('Ampara', 'Ampara'), ('Badulla', 'Badulla'), ('Kandy', 'Kandy'),
        ('Colombo', 'Colombo'), ('Gampaha', 'Gampaha'), ('Kurunegala', 'Kurunegala'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile', primary_key=True)
    name = models.CharField(max_length=255)
    nic_number = models.CharField(max_length=12, unique=True)
    farm_location = models.CharField(max_length=255)
    district = models.CharField(max_length=100, choices=DISTRICT_CHOICES, db_index=True)
    land_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01), MaxValueValidator(1000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farmer_profiles'
        verbose_name = 'Farmer Profile'
    
    def __str__(self):
        return f"Farmer: {self.name} ({self.user.phone_number})"


class BuyerProfile(models.Model):
    """Buyer profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile', primary_key=True)
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    business_reg_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'buyer_profiles'
        verbose_name = 'Buyer Profile'

    def __str__(self):
        return f"Buyer: {self.company_name} ({self.name})"


class OfficerProfile(models.Model):
    """Officer profile"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer_profile', primary_key=True)
    name = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'officer_profiles'
        verbose_name = 'Officer Profile'
    
    def __str__(self):
        return f"Officer: {self.employee_id} ({self.user.phone_number})"


class OTP(models.Model):
    """OTP storage"""
    
    phone_number = models.CharField(max_length=15, db_index=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.phone_number}"
