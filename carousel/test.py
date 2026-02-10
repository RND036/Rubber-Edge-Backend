from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import CarouselItem


class CarouselItemTests(TestCase):
    """Test cases for carousel functionality"""
    
    def setUp(self):
        """Set up test client and sample data"""
        self.client = APIClient()
        
        # Create test carousel items
        CarouselItem.objects.create(
            title='Test Item 1',
            value='Value 1',
            subtitle='Subtitle 1',
            color='#1B5E20',
            icon='trending-up',
            order=1,
            is_active=True
        )
        
        CarouselItem.objects.create(
            title='Test Item 2',
            value='Value 2',
            subtitle='Subtitle 2',
            color='#C62828',
            icon='warning-outline',
            order=2,
            is_active=False
        )
    
    def test_list_active_items(self):
        """Test that only active items are returned"""
        response = self.client.get('/api/carousel/items/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Item 1')
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/carousel/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'healthy')
