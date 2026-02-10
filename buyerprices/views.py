from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Min, Max, Avg
from datetime import timedelta
from .models import BuyerPrice, PriceAlert
from .serializers import (
    BuyerPriceSerializer,
    BulkPriceUpdateSerializer,
    PriceAlertSerializer
)


class BuyerPriceViewSet(viewsets.ModelViewSet):
    """ViewSet for BuyerPrice model"""
    serializer_class = BuyerPriceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter prices based on user role"""
        user = self.request.user
        
        if user.role == 'buyer':
            return BuyerPrice.objects.filter(
                buyer=user
            ).select_related('buyer').order_by('-created_at')
        elif user.role == 'farmer':
            # Farmers see only currently active prices
            return BuyerPrice.objects.filter(
                is_active=True,
                effective_from__lte=timezone.now(),
                effective_to__gte=timezone.now()
            ).select_related('buyer').order_by('buyer', 'grade')
        elif user.role == 'officer':
            return BuyerPrice.objects.all().select_related('buyer').order_by('-created_at')
        
        return BuyerPrice.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set the buyer to the current user"""
        if self.request.user.role != 'buyer':
            raise PermissionError("Only buyers can create prices")
        serializer.save(buyer=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='my-latest')
    def my_latest(self, request):
        """Get buyer's latest prices for today (for pre-filling the form)"""
        if request.user.role != 'buyer':
            return Response(
                {'error': 'Only buyers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        today = timezone.now().date()
        
        # Get prices where effective_from date is today
        prices = BuyerPrice.objects.filter(
            buyer=request.user,
            effective_from__date=today,
            is_active=True
        ).select_related('buyer').order_by('grade')
        
        serializer = self.get_serializer(prices, many=True)
        
        return Response({
            'success': True,
            'count': prices.count(),
            'date': today.isoformat(),
            'prices': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Bulk update/create prices for multiple grades at once"""
        if request.user.role != 'buyer':
            return Response(
                {'error': 'Only buyers can update prices'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkPriceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        prices_data = serializer.validated_data['prices']
        notes = serializer.validated_data.get('notes')
        today = timezone.now().date()
        
        updated_prices = []
        updated_count = 0
        new_count = 0
        
        for price_data in prices_data:
            grade = price_data['grade']
            price_value = price_data['price']
            custom_grade_name = price_data.get('custom_grade_name')
            
            # Try to find existing price for this grade today
            existing_price = BuyerPrice.objects.filter(
                buyer=request.user,
                grade=grade,
                custom_grade_name=custom_grade_name,
                effective_from__date=today,
                is_active=True
            ).first()
            
            if existing_price:
                # Update existing price
                existing_price.price = price_value
                if notes:
                    existing_price.notes = notes
                existing_price.save()
                updated_prices.append(existing_price)
                updated_count += 1
            else:
                # Create new price
                new_price = BuyerPrice.objects.create(
                    buyer=request.user,
                    grade=grade,
                    custom_grade_name=custom_grade_name,
                    price=price_value,
                    notes=notes,
                    effective_from=timezone.now(),
                    is_active=True
                )
                updated_prices.append(new_price)
                new_count += 1
        
        # Fetch prices with select_related to avoid N+1 queries
        updated_prices_qs = BuyerPrice.objects.filter(
            id__in=[p.id for p in updated_prices]
        ).select_related('buyer')
        
        response_serializer = self.get_serializer(updated_prices_qs, many=True)
        
        return Response({
            'success': True,
            'message': f'Successfully updated {updated_count} and created {new_count} prices',
            'total_count': len(updated_prices),
            'updated_count': updated_count,
            'new_count': new_count,
            'prices': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='farmer-view')
    def farmer_view(self, request):
        """Get all active prices grouped by buyer (for farmers panel)"""
        if request.user.role not in ['farmer', 'buyer']:
            return Response(
                {'error': 'Only farmers and buyers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        today = timezone.now().date()
        
        # Get all active prices for today
        prices = BuyerPrice.objects.filter(
            effective_from__date=today,
            is_active=True
        ).select_related('buyer').order_by('buyer', 'grade')
        
        # Group by buyer
        buyers_dict = {}
        for price in prices:
            buyer_id = price.buyer.id
            if buyer_id not in buyers_dict:
                buyer_profile = getattr(price.buyer, 'buyer_profile', None)
                buyers_dict[buyer_id] = {
                    'buyer_id': buyer_id,
                    'buyer_name': getattr(buyer_profile, 'company_name', None) or price.buyer.phone_number,
                    'buyer_username': price.buyer.phone_number,
                    'buyer_company': getattr(buyer_profile, 'company_name', None),
                    'buyer_phone': getattr(buyer_profile, 'phone', None) or price.buyer.phone_number,
                    'buyer_city': getattr(buyer_profile, 'city', None),
                    'buyer_verified': price.buyer.is_verified,
                    'prices': [],
                    'notes': price.notes or '',
                    'last_updated': price.updated_at.isoformat()
                }
            
            buyers_dict[buyer_id]['prices'].append({
                'id': price.id,
                'grade': price.grade,
                'grade_display': price.grade_display,
                'price': str(price.price),
                'created_at': price.created_at.isoformat(),
                'updated_at': price.updated_at.isoformat()
            })
        
        buyers_list = list(buyers_dict.values())
        
        return Response({
            'success': True,
            'date': today.isoformat(),
            'buyers_count': len(buyers_list),
            'total_prices': prices.count(),
            'buyers': buyers_list
        })
    
    @action(detail=False, methods=['get'], url_path='price-history')
    def price_history(self, request):
        """Get price history for analytics"""
        grade = request.query_params.get('grade')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        queryset = BuyerPrice.objects.filter(
            effective_from__date__gte=start_date
        ).select_related('buyer').order_by('-effective_from', '-created_at')
        
        if grade:
            queryset = queryset.filter(grade=grade)
        
        # Calculate statistics
        statistics = {
            'average_change': 0,
            'max_increase': 0,
            'max_decrease': 0
        }
        
        history = []
        for price in queryset:
            history.append({
                'id': price.id,
                'buyer_name': getattr(price.buyer, 'buyer_profile', None) and 
                             price.buyer.buyer_profile.company_name or price.buyer.phone_number,
                'grade_display': price.grade_display,
                'old_price': '0.00',
                'new_price': str(price.price),
                'price_change': 0,
                'price_change_percentage': 0,
                'changed_at': price.updated_at.isoformat(),
                'changed_by_name': price.buyer.phone_number
            })
        
        return Response({
            'success': True,
            'count': len(history),
            'days': days,
            'statistics': statistics,
            'history': history
        })
    
    @action(detail=False, methods=['delete'], url_path='deactivate-all')
    def deactivate_all(self, request):
        """Deactivate all current prices for the buyer"""
        if request.user.role != 'buyer':
            return Response(
                {'error': 'Only buyers can deactivate prices'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        today = timezone.now().date()
        deactivated = BuyerPrice.objects.filter(
            buyer=request.user,
            effective_from__date=today,
            is_active=True
        ).update(is_active=False)
        
        return Response({
            'success': True,
            'message': f'Deactivated {deactivated} prices',
            'deactivated_count': deactivated
        })
    
    @action(detail=False, methods=['get'], url_path='market-overview')
    def market_overview(self, request):
        """Get market overview statistics"""
        today = timezone.now().date()
        
        prices = BuyerPrice.objects.filter(
            effective_from__date=today,
            is_active=True
        )
        
        # Calculate statistics per grade
        grade_stats = {}
        for grade_code, grade_name in BuyerPrice.GRADE_CHOICES:
            grade_prices = prices.filter(grade=grade_code)
            if grade_prices.exists():
                stats = grade_prices.aggregate(
                    min_price=Min('price'),
                    max_price=Max('price'),
                    avg_price=Avg('price'),
                    count=Count('id')
                )
                grade_stats[grade_code] = {
                    'grade_name': grade_name,
                    'buyer_count': stats['count'],
                    'min_price': float(stats['min_price'] or 0),
                    'max_price': float(stats['max_price'] or 0),
                    'avg_price': float(stats['avg_price'] or 0),
                    'price_range': float((stats['max_price'] or 0) - (stats['min_price'] or 0))
                }
        
        return Response({
            'success': True,
            'date': today.isoformat(),
            'active_buyers': prices.values('buyer').distinct().count(),
            'total_active_prices': prices.count(),
            'grade_statistics': grade_stats,
            'last_updated': timezone.now().isoformat()
        })


class PriceAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for PriceAlert model"""
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Farmers see only their alerts"""
        if self.request.user.role == 'farmer':
            return PriceAlert.objects.filter(farmer=self.request.user)
        return PriceAlert.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set the farmer"""
        if self.request.user.role != 'farmer':
            raise PermissionError("Only farmers can create alerts")
        serializer.save(farmer=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='active-alerts')
    def active_alerts(self, request):
        """Get only active alerts"""
        if request.user.role != 'farmer':
            return Response(
                {'error': 'Only farmers can access alerts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alerts = PriceAlert.objects.filter(
            farmer=request.user,
            is_active=True
        ).order_by('-created_at')
        
        serializer = self.get_serializer(alerts, many=True)
        
        return Response({
            'success': True,
            'count': alerts.count(),
            'alerts': serializer.data
        })
