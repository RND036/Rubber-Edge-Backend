from rest_framework import serializers
from .models import User, FarmerProfile, BuyerProfile, OfficerProfile
import re


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = ['name', 'nic_number', 'farm_location', 'district', 'land_area_hectares']
    
    def validate_nic_number(self, value):
        if not re.match(r'^(\d{9}[vVxX]|\d{12})$', value):
            raise serializers.ValidationError("Invalid NIC format")
        return value.upper()


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = ['name', 'company_name', 'business_reg_number']


class OfficerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficerProfile
        fields = ['name','employee_id', 'department']


class UserSerializer(serializers.ModelSerializer):
    farmer_profile = FarmerProfileSerializer(required=False, read_only=True)
    buyer_profile = BuyerProfileSerializer(required=False, read_only=True)
    officer_profile = OfficerProfileSerializer(required=False, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'phone_number', 
            'role', 
            'is_verified', 
            'created_at', 
            'farmer_profile', 
            'buyer_profile', 
            'officer_profile'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        value = re.sub(r'[^\d+]', '', value)
        if value.startswith('0'):
            value = '+94' + value[1:]
        elif not value.startswith('+94'):
            value = '+94' + value
        if not re.match(r'^\+94[0-9]{9}$', value):
            raise serializers.ValidationError("Invalid phone number")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    
    def validate_phone_number(self, value):
        value = re.sub(r'[^\d+]', '', value)
        if value.startswith('0'):
            value = '+94' + value[1:]
        return value
    
    def validate_otp(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("OTP must be 6 digits")
        return value


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    profile_data = serializers.JSONField()
    
    def validate_phone_number(self, value):
        value = re.sub(r'[^\d+]', '', value)
        if value.startswith('0'):
            value = '+94' + value[1:]
        elif not value.startswith('+94'):
            value = '+94' + value
        if not re.match(r'^\+94[0-9]{9}$', value):
            raise serializers.ValidationError("Invalid phone number")
        return value
    
    def validate(self, attrs):
        role = attrs.get('role')
        profile_data = attrs.get('profile_data', {})
        
        if role == 'farmer':
            required = ['name', 'nic_number', 'farm_location', 'district', 'land_area']
            for field in required:
                if field not in profile_data:
                    raise serializers.ValidationError({f'{field} required for farmer'})
        elif role == 'buyer':
            required = ['name', 'company_name', 'business_reg_number']
            for field in required:
                if field not in profile_data:
                    raise serializers.ValidationError({f'{field} required for buyer'})
        elif role == 'officer':
            required = ['name', 'employee_id', 'department']
            for field in required:
                if field not in profile_data:
                    raise serializers.ValidationError({f'{field} required for officer'})
        
        return attrs
