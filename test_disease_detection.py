#!/usr/bin/env python3
"""
Test script for disease detection API with confidence threshold
"""
import requests
import base64
import json
from PIL import Image
import io

# API endpoint
API_URL = "http://localhost:8000/api/disease/detect/"
HEALTH_CHECK_URL = "http://localhost:8000/api/disease/health/"

def create_test_image(color='green', size=(224, 224)):
    """Create a simple colored test image"""
    img = Image.new('RGB', size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

def test_health_check():
    """Test the health check endpoint"""
    print("=" * 60)
    print("1. Testing Health Check")
    print("=" * 60)
    try:
        response = requests.get(HEALTH_CHECK_URL)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        return data.get('status') == 'healthy'
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_random_object():
    """Test with a random colored image (should return Unknown Object)"""
    print("\n" + "=" * 60)
    print("2. Testing Random Object (Blue Square)")
    print("=" * 60)
    try:
        # Create a blue square - definitely not a rubber leaf
        image_b64 = create_test_image(color='blue')
        
        response = requests.post(
            API_URL,
            json={'image': image_b64},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if data.get('isValidDetection') == False:
            print("\n✅ SUCCESS: Random object correctly identified as 'Unknown Object'")
        else:
            print(f"\n⚠️  WARNING: Random object was classified as '{data.get('label')}' with {data.get('confidence')}% confidence")
        
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_another_random():
    """Test with another random image"""
    print("\n" + "=" * 60)
    print("3. Testing Another Random Object (Red Square)")
    print("=" * 60)
    try:
        # Create a red square
        image_b64 = create_test_image(color='red')
        
        response = requests.post(
            API_URL,
            json={'image': image_b64},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if data.get('isValidDetection') == False:
            print("\n✅ SUCCESS: Random object correctly identified as 'Unknown Object'")
        else:
            print(f"\n⚠️  WARNING: Random object was classified as '{data.get('label')}' with {data.get('confidence')}% confidence")
        
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🧪 Disease Detection API Test Suite")
    print("Testing confidence threshold functionality\n")
    
    # Test 1: Health check
    health_ok = test_health_check()
    if not health_ok:
        print("\n❌ Health check failed. Make sure the server is running.")
        return
    
    # Test 2: Random object (should be rejected)
    test_random_object()
    
    # Test 3: Another random object
    test_another_random()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✅ Tests completed!")
    print("Note: Random objects should show 'Unknown Object' with isValidDetection=false")
    print("If you have a real rubber leaf image, test with that to see valid detection.")

if __name__ == "__main__":
    main()
