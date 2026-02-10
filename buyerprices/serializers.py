from rest_framework import serializers
from .models import BuyerPrice, PriceAlert


class BuyerPriceSerializer(serializers.ModelSerializer):
    """Serializer for BuyerPrice model with safe field access"""
    buyer_name = serializers.SerializerMethodField()
    buyer_username = serializers.SerializerMethodField()
    buyer_company = serializers.SerializerMethodField()
    buyer_phone = serializers.SerializerMethodField()
    buyer_city = serializers.SerializerMethodField()
    grade_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = BuyerPrice
        fields = [
            'id', 'buyer', 'buyer_name', 'buyer_username', 'buyer_company',
            'buyer_phone', 'buyer_city', 'grade', 'custom_grade_name',
            'grade_display', 'price', 'notes', 'effective_date',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'buyer', 'created_at', 'updated_at', 'effective_date']
    
    def get_buyer_name(self, obj):
        """Get buyer name safely"""
        try:
            if hasattr(obj.buyer, 'buyer_profile'):
                return obj.buyer.buyer_profile.company_name
            return obj.buyer.phone_number
        except Exception:
            return obj.buyer.phone_number
    
    def get_buyer_username(self, obj):
        """Get buyer username"""
        return obj.buyer.phone_number
    
    def get_buyer_company(self, obj):
        """Get company name safely"""
        try:
            if hasattr(obj.buyer, 'buyer_profile'):
                return obj.buyer.buyer_profile.company_name
            return None
        except Exception:
            return None
    
    def get_buyer_phone(self, obj):
        """Get buyer phone safely"""
        try:
            if hasattr(obj.buyer, 'buyer_profile'):
                return getattr(obj.buyer.buyer_profile, 'phone', obj.buyer.phone_number)
            return obj.buyer.phone_number
        except Exception:
            return obj.buyer.phone_number
    
    def get_buyer_city(self, obj):
        """Get buyer city safely"""
        try:
            if hasattr(obj.buyer, 'buyer_profile'):
                return getattr(obj.buyer.buyer_profile, 'city', None)
            return None
        except Exception:
            return None


class BuyerPriceInputSerializer(serializers.Serializer):
    """Input serializer for bulk price updates"""
    grade = serializers.CharField(max_length=50)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    custom_grade_name = serializers.CharField(max_length=100, required=False, allow_blank=True)


class BulkPriceUpdateSerializer(serializers.Serializer):
    """Serializer for bulk price updates"""
    prices = BuyerPriceInputSerializer(many=True)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_prices(self, value):
        """Validate that custom grades have names"""
        if not value:
            raise serializers.ValidationError("At least one price is required")
        
        for price in value:
            if price.get('grade') == 'custom' and not price.get('custom_grade_name'):
                raise serializers.ValidationError(
                    "Custom grades must have a custom_grade_name"
                )
        return value


class PriceAlertSerializer(serializers.ModelSerializer):
    """Serializer for PriceAlert model"""
    farmer_name = serializers.CharField(source='farmer.phone_number', read_only=True)
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    
    class Meta:
        model = PriceAlert
        fields = [
            'id', 'farmer', 'farmer_name', 'grade', 'grade_display',
            'target_price', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'farmer', 'created_at', 'updated_at']
