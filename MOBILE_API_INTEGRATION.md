# Mobile App API Integration Guide

This guide helps mobile app developers (iOS/Android) connect to the Rubber Farm API backend.

## 🔗 API Configuration

### Base URL
```
Production: https://yourdomain.com
Development: http://localhost:8000
```

### API Version
All endpoints are versioned: `/api/v1/...`

---

## 🔐 Authentication

### Step 1: Login (Get Token)
```
POST /api/token/
Content-Type: application/json

{
  "username": "farmer_name",
  "password": "password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Step 2: Use Access Token in Headers
Attach the `access` token to all API requests:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Step 3: Refresh Token (When expired)
```
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 📡 Key API Endpoints

### Users
```
GET /api/users/profile/               # Get user profile
PUT /api/users/profile/               # Update profile
POST /api/users/register/             # Register new user
POST /api/token/                      # Login
POST /api/token/refresh/              # Refresh token
POST /api/logout/                     # Logout
```

### Disease Detection (AI)
```
POST /api/diseases/detect/            # Analyze leaf image
Body: FormData with 'image' field

Response:
{
  "disease": "Leaf Spot",
  "confidence": 0.95,
  "treatment": "Apply fungicide X",
  "severity": "high"
}
```

### Real-Time Chat (WebSocket)
```
WebSocket: wss://yourdomain.com/ws/chat/
Message format:
{
  "type": "chat_message",
  "message": "Hello",
  "receiver_id": 123
}
```

### Events
```
GET /api/events/                      # List events
POST /api/events/                     # Create event
GET /api/events/{id}/                 # Get event details
PUT /api/events/{id}/                 # Update event
DELETE /api/events/{id}/              # Delete event
```

### Prices (Buyer Prices)
```
GET /api/buyerprices/                 # List all buyer prices
GET /api/buyerprices/{id}/            # Get price details
```

### Carousel/Media
```
GET /api/carousel/                    # List carousel items
POST /api/carousel/                   # Upload media
GET /api/carousel/{id}/               # Get media details
```

---

## 🎯 Common Implementation Examples

### Example: Flutter/Dart

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiClient {
  final String baseUrl = "https://yourdomain.com/api";
  String? accessToken;
  String? refreshToken;

  // Login
  Future<void> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/token/'),
      body: {
        'username': username,
        'password': password,
      },
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      accessToken = data['access'];
      refreshToken = data['refresh'];
    }
  }

  // Get with auth
  Future<Map> getUserProfile() async {
    final response = await http.get(
      Uri.parse('$baseUrl/users/profile/'),
      headers: {
        'Authorization': 'Bearer $accessToken',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load profile');
  }

  // Disease detection with image
  Future<Map> detectDisease(File imageFile) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/diseases/detect/'),
    );
    
    request.headers['Authorization'] = 'Bearer $accessToken';
    request.files.add(
      await http.MultipartFile.fromPath('image', imageFile.path),
    );
    
    final response = await request.send();
    if (response.statusCode == 200) {
      return jsonDecode(await response.stream.bytesToString());
    }
    throw Exception('Disease detection failed');
  }
}
```

### Example: React Native (JavaScript)

```javascript
class API {
  baseURL = 'https://yourdomain.com/api';
  accessToken = null;

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    this.accessToken = data.access;
    return data;
  }

  async detectDisease(imageUri) {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'disease.jpg'
    });

    const response = await fetch(`${this.baseURL}/diseases/detect/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      },
      body: formData
    });
    
    return response.json();
  }

  async getUserProfile() {
    const response = await fetch(`${this.baseURL}/users/profile/`, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    });
    
    return response.json();
  }
}
```

### Example: Swift (iOS)

```swift
import Foundation
import Combine

class APIClient: ObservableObject {
    let baseURL = "https://yourdomain.com/api"
    @Published var accessToken: String?

    func login(username: String, password: String) -> AnyPublisher<AuthResponse, Error> {
        let url = URL(string: "\(baseURL)/token/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["username": username, "password": password]
        request.httpBody = try? JSONEncoder().encode(body)
        
        return URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: AuthResponse.self, decoder: JSONDecoder())
            .handleEvents(receiveOutput: { [weak self] response in
                self?.accessToken = response.access
            })
            .eraseToAnyPublisher()
    }

    func getUserProfile() -> AnyPublisher<User, Error> {
        let url = URL(string: "\(baseURL)/users/profile/")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(accessToken ?? "")", forHTTPHeaderField: "Authorization")
        
        return URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: User.self, decoder: JSONDecoder())
            .eraseToAnyPublisher()
    }
}
```

---

## ⚠️ Error Handling

Common HTTP Status Codes:

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh token or re-login |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Server issue, retry later |

### Example Error Response:
```json
{
  "detail": "Invalid token or token expired",
  "code": "invalid_token"
}
```

---

## 🔌 WebSocket (Real-Time Chat)

### Connect to WebSocket
```
wss://yourdomain.com/ws/chat/?token=<access_token>
```

### Send Message
```json
{
  "type": "chat_message",
  "message": "Hello farmer!",
  "receiver_id": 5
}
```

### Receive Message
```json
{
  "type": "chat_message",
  "message": "Hello!",
  "sender_id": 3,
  "sender_name": "John",
  "timestamp": "2024-02-10T10:30:00Z"
}
```

---

## 🖼️ Image Upload Best Practices

When uploading images (disease detection, profile picture, etc.):

1. **Compress before sending** (reduce file size to <2MB)
2. **Use JPEG or PNG format**
3. **Add proper Content-Type header**
4. **Handle large files with chunked upload if needed**

Example Flutter image compression:
```dart
final imageBytes = await compressImage(originalFile);
final multiPartFile = http.MultipartFile.fromBytes(
  'image',
  imageBytes,
  filename: 'disease.jpg',
  contentType: MediaType('image', 'jpeg'),
);
```

---

## 🔐 Security Tips

1. **Never store access token in SharedPreferences/UserDefaults**
   - Use secure storage (Keychain, Keystore)

2. **Always use HTTPS/WSS** (not HTTP/WS)
   - Enable Certificate Pinning in production

3. **Implement token refresh logic**
   - Refresh before token expires
   - Handle 401 responses gracefully

4. **Validate all user inputs** before sending to API

5. **Don't expose error details to users**
   - Log errors on client, show generic messages

---

## 🧪 Testing API Locally

Use Postman or Insomnia to test endpoints before integrating into mobile app:

1. Import API endpoints
2. Set up authorization in Postman (Bearer token)
3. Test each endpoint manually
4. Check response formats

---

## 📚 Full API Reference

For complete API documentation with all endpoints and parameters, see:
- `rubber_farm_api/urls.py` - All URL patterns
- Individual app `views.py` - Endpoint implementations
- Run `python manage.py spectacular --file schema.yml` for OpenAPI schema

---

**Questions?** Check the main [GITHUB_SETUP.md](GITHUB_SETUP.md) or project README.
