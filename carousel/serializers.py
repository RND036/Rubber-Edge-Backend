from rest_framework import serializers
from .models import CarouselItem


class CarouselItemSerializer(serializers.ModelSerializer):
    """
    Serializer for carousel items with full image URLs
    Handles optional text fields
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CarouselItem
        fields = [
            'id',
            'title',
            'value',
            'subtitle',
            'image_url',
            'color',
            'icon',
            'order',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """
        Returns absolute URL for the image
        Works with both development and production
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
