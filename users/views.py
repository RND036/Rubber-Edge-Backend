from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import User, FarmerProfile, BuyerProfile, OfficerProfile, OTP
from .serializers import (
    SendOTPSerializer, 
    VerifyOTPSerializer, 
    RegisterSerializer, 
    UserSerializer
)
from .utils import send_sms
import random
import logging

logger = logging.getLogger(__name__)


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP to phone number"""
    serializer = SendOTPSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False, 
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    
    # Rate limiting
    attempts_key = f'otp_attempts_{phone_number}'
    attempts = cache.get(attempts_key, 0)
    if attempts >= 5:
        return Response({
            'success': False, 
            'error': 'Too many requests'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Generate OTP
    otp_code = str(random.randint(100000, 999999))
    
    # Store in cache (5 minutes)
    cache.set(f'otp_{phone_number}', otp_code, timeout=300)
    cache.set(attempts_key, attempts + 1, timeout=3600)
    
    # Save to database
    OTP.objects.create(phone_number=phone_number, otp_code=otp_code)
    
    # Send SMS
    try:
        message = f'Your RubberEdge verification code is: {otp_code}\nValid for 5 minutes.'
        send_sms(phone_number, message)
        logger.info(f"OTP sent to {phone_number}")
    except Exception as e:
        logger.error(f"SMS failed: {str(e)}")
        return Response({
            'success': False, 
            'error': 'Failed to send SMS'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': True,
        'message': 'OTP sent successfully',
        'data': {
            'phone_number': phone_number, 
            'expires_in': 300
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP"""
    serializer = VerifyOTPSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False, 
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp']
    
    stored_otp = cache.get(f'otp_{phone_number}')
    if not stored_otp or stored_otp != otp_code:
        return Response({
            'success': False, 
            'error': 'Invalid or expired OTP'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True, 
        'message': 'OTP verified'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register new user"""
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False, 
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp']
    role = serializer.validated_data['role']
    profile_data = serializer.validated_data['profile_data']
    
    # Verify OTP
    stored_otp = cache.get(f'otp_{phone_number}')
    if not stored_otp or stored_otp != otp_code:
        return Response({
            'success': False, 
            'error': 'Invalid OTP'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if exists
    if User.objects.filter(phone_number=phone_number).exists():
        return Response({
            'success': False, 
            'error': 'Phone already registered'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                phone_number=phone_number, 
                role=role, 
                is_verified=True
            )

            # Create profile
            if role == 'farmer':
                FarmerProfile.objects.create(
                    user=user,
                    name=profile_data.get('name', ''),
                    nic_number=profile_data['nic_number'].upper(),
                    farm_location=profile_data['farm_location'],
                    district=profile_data['district'],
                    land_area_hectares=profile_data['land_area']
                )
            elif role == 'buyer':
                BuyerProfile.objects.create(
                    user=user,
                    name=profile_data.get('name', ''),
                    company_name=profile_data['company_name'],
                    business_reg_number=profile_data['business_reg_number']
                )
            elif role == 'officer':
                officer_name = profile_data.get('name', '').strip()
                if not officer_name:
                    return Response({
                        'success': False,
                        'error': 'Officer name is required.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                OfficerProfile.objects.create(
                    user=user,
                    name=officer_name,
                    employee_id=profile_data['employee_id'],
                    department=profile_data['department']
                )

            # Clear OTP
            cache.delete(f'otp_{phone_number}')

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            user_serializer = UserSerializer(user)

            logger.info(f"User registered: {phone_number}")

            return Response({
                'success': True,
                'message': 'Registration successful',
                'data': {
                    'user': user_serializer.data,
                    'tokens': {
                        'refresh': str(refresh), 
                        'access': str(refresh.access_token)
                    }
                }
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'success': False, 
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user"""
    serializer = VerifyOTPSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False, 
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp']
    
    # Verify OTP
    stored_otp = cache.get(f'otp_{phone_number}')
    if not stored_otp or stored_otp != otp_code:
        return Response({
            'success': False, 
            'error': 'Invalid OTP'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user
    try:
        user = User.objects.select_related(
            'farmer_profile', 
            'buyer_profile', 
            'officer_profile'
        ).get(phone_number=phone_number)
    except User.DoesNotExist:
        return Response({
            'success': False, 
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not user.is_active:
        return Response({
            'success': False, 
            'error': 'Account deactivated'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Clear OTP
    cache.delete(f'otp_{phone_number}')
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    user_serializer = UserSerializer(user)
    
    logger.info(f"User logged in: {phone_number}")
    
    return Response({
        'success': True,
        'message': 'Login successful',
        'data': {
            'user': user_serializer.data,
            'tokens': {
                'refresh': str(refresh), 
                'access': str(refresh.access_token)
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            'success': True, 
            'message': 'Logged out'
        }, status=status.HTTP_200_OK)
    except:
        return Response({
            'success': True, 
            'message': 'Logged out'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get user profile"""
    user = request.user
    
    try:
        user = User.objects.select_related(
            'farmer_profile', 
            'buyer_profile', 
            'officer_profile'
        ).get(id=user.id)
        
        serializer = UserSerializer(user)
        return Response({
            'success': True, 
            'data': {'user': serializer.data}
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'success': False, 
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ============================================
# FARMER MANAGEMENT ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_farmers(request):
    """Get list of farmers - accessible by officers"""
    
    # Check if user is an officer
    if request.user.role != 'officer':
        return Response({
            'error': 'Only officers can access farmer list'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters for filtering/search
    search = request.query_params.get('search', '')
    district = request.query_params.get('district', '')
    
    # Get all farmers
    farmers = User.objects.filter(
        role='farmer',
        is_verified=True
    ).select_related('farmer_profile')
    
    # Apply filters
    if search:
        farmers = farmers.filter(
            Q(phone_number__icontains=search) |
            Q(farmer_profile__nic_number__icontains=search) |
            Q(farmer_profile__farm_location__icontains=search) |
            Q(farmer_profile__name__icontains=search)
        )
    
    if district:
        farmers = farmers.filter(farmer_profile__district=district)
    
    # Serialize data
    farmers_data = []
    for farmer in farmers:
        try:
            profile = farmer.farmer_profile
            farmers_data.append({
                'id': farmer.id,
                'phone_number': farmer.phone_number,
                'name': profile.name,
                'nic_number': profile.nic_number,
                'farm_location': profile.farm_location,
                'district': profile.district,
                'land_area_hectares': float(profile.land_area_hectares),
                'created_at': farmer.created_at.isoformat(),
            })
        except FarmerProfile.DoesNotExist:
            continue
    
    return Response({
        'success': True,
        'count': len(farmers_data),
        'farmers': farmers_data
    })


# ============================================
# OFFICER MANAGEMENT ENDPOINTS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_officers(request):
    """
    Get list of officers - accessible by all authenticated users
    Officers can be contacted for support
    """
    
    try:
        # Get all officers
        officers = User.objects.filter(
            role='officer',
            is_verified=True,
            is_superuser=False,
            is_active=True
        ).select_related('officer_profile').order_by('-created_at')
        
        # Serialize data
        officers_data = []
        for officer in officers:
            officer_info = {
                'id': officer.id,
                'phone_number': officer.phone_number,
                'role': officer.role,
                'is_verified': officer.is_verified,
                'created_at': officer.created_at.isoformat(),
            }
            
            # Add officer profile if exists
            try:
                profile = officer.officer_profile
                officer_info['officer_profile'] = {
                    'name': profile.name,
                    'employee_id': profile.employee_id,
                    'department': profile.department,
                }
            except OfficerProfile.DoesNotExist:
                officer_info['officer_profile'] = None
            
            officers_data.append(officer_info)
        
        logger.info(f"User {request.user.phone_number} fetched {len(officers_data)} officers")
        
        return Response({
            'success': True,
            'count': len(officers_data),
            'officers': officers_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Get officers error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch officers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ADD THIS TO THE END OF YOUR views.py FILE

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile based on role
    PUT - Full update
    PATCH - Partial update
    """
    user = request.user
    
    try:
        with transaction.atomic():
            # Officer profile update
            if user.role == 'officer':
                if not hasattr(user, 'officer_profile'):
                    return Response({
                        'success': False,
                        'error': 'Officer profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                officer_data = request.data.get('officer_profile', {})
                
                if not officer_data:
                    return Response({
                        'success': False,
                        'error': 'No profile data provided'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                officer_profile = user.officer_profile
                
                # Update fields (employee_id is read-only)
                if 'name' in officer_data:
                    if not officer_data['name'].strip():
                        return Response({
                            'success': False,
                            'error': 'Name cannot be empty'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    officer_profile.name = officer_data['name'].strip()
                
                if 'department' in officer_data:
                    if not officer_data['department'].strip():
                        return Response({
                            'success': False,
                            'error': 'Department cannot be empty'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    officer_profile.department = officer_data['department'].strip()
                
                officer_profile.save()
                logger.info(f"Officer profile updated: {user.phone_number}")
            
            # Farmer profile update
            elif user.role == 'farmer':
                if not hasattr(user, 'farmer_profile'):
                    return Response({
                        'success': False,
                        'error': 'Farmer profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                farmer_data = request.data.get('farmer_profile', {})
                
                if not farmer_data:
                    return Response({
                        'success': False,
                        'error': 'No profile data provided'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                farmer_profile = user.farmer_profile
                
                # Update allowed fields
                if 'name' in farmer_data:
                    farmer_profile.name = farmer_data['name'].strip()
                if 'farm_location' in farmer_data:
                    farmer_profile.farm_location = farmer_data['farm_location'].strip()
                if 'district' in farmer_data:
                    farmer_profile.district = farmer_data['district']
                if 'land_area_hectares' in farmer_data:
                    farmer_profile.land_area_hectares = farmer_data['land_area_hectares']
                
                farmer_profile.save()
                logger.info(f"Farmer profile updated: {user.phone_number}")
            
            # Buyer profile update
            elif user.role == 'buyer':
                if not hasattr(user, 'buyer_profile'):
                    return Response({
                        'success': False,
                        'error': 'Buyer profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                buyer_data = request.data.get('buyer_profile', {})
                
                if not buyer_data:
                    return Response({
                        'success': False,
                        'error': 'No profile data provided'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                buyer_profile = user.buyer_profile
                
                # Update allowed fields
                if 'company_name' in buyer_data:
                    buyer_profile.company_name = buyer_data['company_name'].strip()
                
                buyer_profile.save()
                logger.info(f"Buyer profile updated: {user.phone_number}")
            
            # Refresh user data
            user.refresh_from_db()
            user_serializer = UserSerializer(user)
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': {
                    'user': user_serializer.data
                }
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
