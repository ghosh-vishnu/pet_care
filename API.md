# Dog Health AI - Complete API Documentation

Complete API reference with working examples for all endpoints in the Dog Health AI application.

---

## 📋 Table of Contents

1. [Base Information](#base-information)
2. [Authentication](#authentication)
3. [Health & Status](#health--status)
4. [Pet Profile](#pet-profile)
5. [Chat](#chat)
6. [Image Upload & Analysis](#image-upload--analysis)
7. [Document Upload & Analysis](#document-upload--analysis)
8. [Nutrition Calculator](#nutrition-calculator)
9. [Reports](#reports)
10. [Error Handling](#error-handling)

---

## Base Information

### Base URL
```
http://localhost:8000
```

### Authentication

Most endpoints require JWT (JSON Web Token) authentication. Include the token in the request header:

```
Authorization: Bearer <your_access_token>
```

### Getting Access Token

1. Register a new user using `/auth/register`
2. Login using `/auth/login`
3. Use the `access_token` from the response in subsequent requests

---

## Authentication

### 1. Register New User

**Endpoint:** `POST /auth/register`

**Description:** Create a new user account

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**JavaScript Fetch Example:**
```javascript
const response = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
console.log('Access Token:', data.access_token);
console.log('User ID:', data.user_id);
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

---

### 2. Login User

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and get access token

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**JavaScript Fetch Example:**
```javascript
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
// Store token for future requests
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user_id', data.user_id);
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

---

## Health & Status

### 1. Root Endpoint

**Endpoint:** `GET /`

**Description:** Check if API is running

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "Dog Health AI API running with PostgreSQL"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/"
```

---

### 2. Health Check

**Endpoint:** `GET /health`

**Description:** Check API health status

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "status": "healthy",
  "cors": "enabled"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/health"
```

---

### 3. Test FAQ Search

**Endpoint:** `GET /test/faq-search`

**Description:** Test endpoint for FAQ semantic search (for debugging)

**Authentication:** Not required

**Query Parameters:**
- `q` (string, optional): Search query (default: "Low-fat diet recommendation for dogs?")

**Response (200 OK):**
```json
{
  "query": "Low-fat diet recommendation for dogs?",
  "top_results": [
    {
      "question": "What is a good low-fat diet for dogs?",
      "answer": "Low-fat diets are ideal for overweight dogs...",
      "similarity": 0.87
    }
  ],
  "best_match": {
    "question": "What is a good low-fat diet for dogs?",
    "answer": "Low-fat diets are ideal for overweight dogs...",
    "confidence": "high",
    "similarity_score": 0.87
  }
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/test/faq-search?q=low%20fat%20diet"
```

**JavaScript Fetch Example:**
```javascript
const query = encodeURIComponent('low fat diet for dogs');
const response = await fetch(`http://localhost:8000/test/faq-search?q=${query}`);
const data = await response.json();
console.log('Best Match:', data.best_match);
```

---

## Pet Profile

### 1. Check Pet Profile Status

**Endpoint:** `GET /user/{user_id}/pet/{pet_id}/profile/status`

**Description:** Check if pet profile exists and get profile data

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Response (200 OK) - Profile Exists:**
```json
{
  "status": "EXISTS",
  "message": "Pet profile found.",
  "profile_data": {
    "petName": "Max",
    "breed": "Labrador Retriever",
    "weight": "30",
    "age": "3",
    "gender": "Male",
    "season": "Summer",
    "activityLevel": "High",
    "behaviorNotes": "Friendly and active",
    "medicalConditions": ["None"],
    "goals": ["Maintain healthy weight"]
  }
}
```

**Response (200 OK) - Profile Missing:**
```json
{
  "status": "MISSING",
  "message": "Pet profile not found. Must fill details.",
  "profile_data": null
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/user/1/pet/my_dog_123/profile/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/profile/status`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const data = await response.json();
if (data.status === 'EXISTS') {
  console.log('Profile:', data.profile_data);
} else {
  console.log('Profile not found, create one');
}
```

---

### 2. Save/Update Pet Profile

**Endpoint:** `POST /user/{user_id}/pet/{pet_id}/profile`

**Description:** Create or update pet profile

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Request Body:**
```json
{
  "petName": "Max",
  "breed": "Labrador Retriever",
  "weight": "30",
  "age": "3",
  "gender": "Male",
  "season": "Summer",
  "activityLevel": "High",
  "behaviorNotes": "Friendly and active",
  "medicalConditions": ["None"],
  "goals": ["Maintain healthy weight"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile saved successfully",
  "pet_id": "my_dog_123"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "petName": "Max",
    "breed": "Labrador Retriever",
    "weight": "30",
    "age": "3",
    "gender": "Male",
    "season": "Summer",
    "activityLevel": "High",
    "behaviorNotes": "Friendly and active",
    "medicalConditions": ["None"],
    "goals": ["Maintain healthy weight"]
  }'
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const profileData = {
  petName: 'Max',
  breed: 'Labrador Retriever',
  weight: '30',
  age: '3',
  gender: 'Male',
  season: 'Summer',
  activityLevel: 'High',
  behaviorNotes: 'Friendly and active',
  medicalConditions: ['None'],
  goals: ['Maintain healthy weight']
};

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/profile`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(profileData)
});

const data = await response.json();
console.log('Profile saved:', data.message);
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "Access denied"
}
```

---

## Chat

### 1. Send Chat Message

**Endpoint:** `POST /user/{user_id}/pet/{pet_id}/chat`

**Description:** Send a message to the AI chat assistant. The system uses intelligent intent routing:
- **GREETING**: Returns instant static response (no AI/DB calls)
- **IMAGE_QUERY**: Routes to image analysis flow
- **FAQ_QUESTION**: Uses RAG system with database vector search, falls back to GPT if needed

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Request Body:**
```json
{
  "question": "What should I feed my dog?",
  "pet_profile": {
    "petName": "Max",
    "breed": "Labrador Retriever",
    "weight": "30",
    "age": "3"
  },
  "image_url": null,
  "image_analysis_context": null
}
```

**Response (200 OK):**
```json
{
  "answer": "For a 3-year-old Labrador Retriever weighing 30kg, feed high-quality dog food...",
  "matched_question": "What should I feed my dog?",
  "score": 0.87,
  "source": "faq",
  "confidence": "high"
}
```

**Response Fields:**
- `answer` (string): The AI's response
- `matched_question` (string, optional): Matched FAQ question if found
- `score` (float): Similarity score (0.0 to 1.0)
- `source` (string): Response source - `"system"`, `"faq"`, or `"gpt"`
- `confidence` (string): Confidence level - `"high"`, `"medium"`, `"low"`, or `"none"`

**cURL Example - Text Question:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What should I feed my dog?",
    "pet_profile": {
      "petName": "Max",
      "breed": "Labrador Retriever",
      "weight": "30",
      "age": "3"
    }
  }'
```

**cURL Example - Greeting:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "hi"
  }'
```

**cURL Example - With Image Context:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What do you see in this image?",
    "image_url": "/images/20240101_120000_abc123.jpg",
    "image_analysis_context": {
      "breed": "Labrador Retriever",
      "health_status": "Good"
    }
  }'
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

// Send a text question
const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/chat`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'What should I feed my dog?',
    pet_profile: {
      petName: 'Max',
      breed: 'Labrador Retriever',
      weight: '30',
      age: '3'
    }
  })
});

const data = await response.json();
console.log('Answer:', data.answer);
console.log('Source:', data.source);
console.log('Confidence:', data.confidence);
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "Access denied"
}
```

---

### 2. Get Chat Messages

**Endpoint:** `GET /user/{user_id}/pet/{pet_id}/chat/messages`

**Description:** Get chat message history for a pet

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Response (200 OK):**
```json
{
  "messages": [
    {
      "sender": "user",
      "text": "What should I feed my dog?",
      "image_url": null,
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "sender": "ai",
      "text": "For a 3-year-old Labrador Retriever...",
      "image_url": null,
      "timestamp": "2024-01-15T10:30:05"
    },
    {
      "sender": "user",
      "text": "📷 Uploaded dog photo: image.jpg",
      "image_url": "/images/20240115_103000_abc123.jpg",
      "timestamp": "2024-01-15T10:35:00"
    },
    {
      "sender": "ai",
      "text": "I've analyzed your dog's photo!...",
      "image_url": null,
      "timestamp": "2024-01-15T10:35:10"
    }
  ],
  "pet_id": "my_dog_123"
}
```

**Response Fields:**
- `messages` (array): List of chat messages
  - `sender` (string): `"user"` or `"ai"`
  - `text` (string): Message text
  - `image_url` (string, optional): Image URL if message has an image
  - `timestamp` (string, ISO format): Message timestamp
- `pet_id` (string): Resolved pet ID (may differ from requested if fallback was used)

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/user/1/pet/my_dog_123/chat/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/chat/messages`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const data = await response.json();
console.log('Messages:', data.messages);
console.log('Pet ID:', data.pet_id);

// Update pet_id if it was resolved differently
if (data.pet_id !== petId) {
  localStorage.setItem('pet_id', data.pet_id);
}
```

---

## Image Upload & Analysis

### 1. Upload and Analyze Dog Image

**Endpoint:** `POST /user/{user_id}/pet/{pet_id}/upload/analyze`

**Description:** Upload a dog image for breed detection and health analysis. The system:
1. Validates the image contains a dog (using MobileNet V3)
2. Detects breed (using EfficientNet-B0)
3. Analyzes health indicators (using GPT-4o-mini Vision)
4. Auto-updates pet profile breed if missing
5. Saves analysis to chat history

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the image

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Image analyzed successfully",
  "filename": "20240115_103000_abc123.jpg",
  "breed": "Labrador Retriever",
  "breed_confidence": 85.5,
  "health_analysis": {
    "body_condition": "Normal",
    "coat_condition": "Healthy",
    "eye_condition": "Normal",
    "energy_level": "Normal",
    "observations": ["Healthy appearance", "Good posture"],
    "recommendations": ["Continue regular exercise", "Maintain current diet"],
    "concerns": []
  },
  "messages": [
    {
      "sender": "user",
      "text": "📷 Uploaded dog photo: image.jpg",
      "image_url": "/images/20240115_103000_abc123.jpg",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "sender": "ai",
      "text": "I've analyzed your dog's photo!...",
      "image_url": null,
      "timestamp": "2024-01-15T10:30:05"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/upload/analyze" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/dog_image.jpg"
```

**JavaScript Fetch Example - File Input:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

// Get file from input element
const fileInput = document.getElementById('imageUpload');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/upload/analyze`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // Don't set Content-Type - browser will set it with boundary
  },
  body: formData
});

const data = await response.json();
console.log('Breed:', data.breed);
console.log('Confidence:', data.breed_confidence);
console.log('Health Analysis:', data.health_analysis);
```

**JavaScript Fetch Example - Canvas/Blob:**
```javascript
// Convert canvas to blob
canvas.toBlob(async (blob) => {
  const formData = new FormData();
  formData.append('file', blob, 'dog_photo.jpg');

  const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/upload/analyze`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  const data = await response.json();
  // Handle response
}, 'image/jpeg', 0.9);
```

**Error Response (400 Bad Request) - No Dog Detected:**
```json
{
  "status": "validation_failed",
  "message": "Image does not appear to contain a dog",
  "detail": "The uploaded image does not appear to contain a recognizable dog...",
  "filename": "20240115_103000_abc123.jpg",
  "messages": [
    {
      "sender": "user",
      "text": "📷 Uploaded photo: image.jpg",
      "image_url": "/images/20240115_103000_abc123.jpg",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "sender": "ai",
      "text": "I couldn't detect a dog in this image...",
      "image_url": null,
      "timestamp": "2024-01-15T10:30:05"
    }
  ]
}
```

**Error Response (400 Bad Request) - Invalid File:**
```json
{
  "detail": "Unsupported file type. Please upload an image file."
}
```

**Error Response (400 Bad Request) - Low Breed Confidence:**
```json
{
  "status": "validation_failed",
  "message": "Breed detection confidence too low - image may not contain a dog",
  "breed": "Unknown",
  "confidence": 0.30,
  "filename": "20240115_103000_abc123.jpg",
  "messages": [...]
}
```

---

## Document Upload & Analysis

### 1. Upload and Analyze Veterinary Report

**Endpoint:** `POST /user/{user_id}/pet/{pet_id}/upload/analyze_document`

**Description:** Upload a veterinary report (PDF or image) for AI analysis

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the PDF or image

**Response (200 OK):**
```json
{
  "status": "Report analyzed",
  "message": "Results sent to chat."
}
```

**Note:** The analysis results are automatically saved to chat history. Use the `/chat/messages` endpoint to retrieve them.

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/upload/analyze_document" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/vet_report.pdf"
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const fileInput = document.getElementById('reportUpload');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/upload/analyze_document`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const data = await response.json();
console.log('Report analyzed:', data.message);

// Fetch chat messages to see analysis results
const messagesResponse = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/chat/messages`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const messagesData = await messagesResponse.json();
console.log('Latest messages:', messagesData.messages);
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Unsupported file type"
}
```

---

## Nutrition Calculator

### 1. Calculate Nutrition Requirements

**Endpoint:** `POST /user/{user_id}/pet/{pet_id}/nutrition/calculate`

**Description:** Calculate daily nutritional requirements based on pet profile using AAFCO standards

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Request Body:**
```json
{
  "petName": "Max",
  "breed": "Labrador Retriever",
  "weight": "30",
  "age": "3",
  "gender": "Male",
  "season": "Summer",
  "activityLevel": "High",
  "behaviorNotes": "Very active",
  "medicalConditions": ["None"],
  "goals": ["Maintain healthy weight"]
}
```

**Response (200 OK):**
```json
{
  "daily_calories": 1400,
  "protein_grams": 105,
  "fat_grams": 47,
  "carbs_grams": 175,
  "protein_percentage": 30,
  "fat_percentage": 30,
  "carbs_percentage": 40,
  "rer": 700,
  "mer": 1400,
  "recommendations": [
    "Feed 2-3 meals per day",
    "Ensure adequate hydration",
    "Monitor weight regularly"
  ],
  "supplements": [
    "Omega-3 fatty acids for joint health",
    "Probiotics for digestive health"
  ]
}
```

**Response Fields:**
- `daily_calories` (number): Total daily calories (kcal)
- `protein_grams` (number): Daily protein requirement (grams)
- `fat_grams` (number): Daily fat requirement (grams)
- `carbs_grams` (number): Daily carbs requirement (grams)
- `protein_percentage` (number): Protein percentage of total calories
- `fat_percentage` (number): Fat percentage of total calories
- `carbs_percentage` (number): Carbs percentage of total calories
- `rer` (number): Resting Energy Requirement (kcal)
- `mer` (number): Maintenance Energy Requirement (kcal)
- `recommendations` (array): Feeding recommendations
- `supplements` (array): Recommended supplements

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/user/1/pet/my_dog_123/nutrition/calculate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "petName": "Max",
    "breed": "Labrador Retriever",
    "weight": "30",
    "age": "3",
    "gender": "Male",
    "season": "Summer",
    "activityLevel": "High",
    "behaviorNotes": "Very active",
    "medicalConditions": ["None"],
    "goals": ["Maintain healthy weight"]
  }'
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const profileData = {
  petName: 'Max',
  breed: 'Labrador Retriever',
  weight: '30',
  age: '3',
  gender: 'Male',
  season: 'Summer',
  activityLevel: 'High',
  behaviorNotes: 'Very active',
  medicalConditions: ['None'],
  goals: ['Maintain healthy weight']
};

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/nutrition/calculate`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(profileData)
});

const data = await response.json();
console.log('Daily Calories:', data.daily_calories);
console.log('Protein:', data.protein_grams, 'g');
console.log('Recommendations:', data.recommendations);
```

---

## Reports

### 1. Get Pet Reports

**Endpoint:** `GET /user/{user_id}/pet/{pet_id}/reports`

**Description:** Get all veterinary reports for a pet

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer): User ID
- `pet_id` (string): Pet ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "filename": "blood_test_report.pdf",
    "file_path": "/reports/blood_test_report.pdf",
    "analysis_result": "The blood test shows normal values for most parameters...",
    "created_at": "2024-01-15T10:00:00"
  },
  {
    "id": 2,
    "filename": "xray_report.jpg",
    "file_path": "/reports/xray_report.jpg",
    "analysis_result": "The X-ray shows no signs of fractures...",
    "created_at": "2024-01-20T14:30:00"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/user/1/pet/my_dog_123/reports" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**JavaScript Fetch Example:**
```javascript
const userId = 1;
const petId = 'my_dog_123';
const token = localStorage.getItem('access_token');

const response = await fetch(`http://localhost:8000/user/${userId}/pet/${petId}/reports`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const reports = await response.json();
console.log('Reports:', reports);

// Display reports
reports.forEach(report => {
  console.log(`Report: ${report.filename}`);
  console.log(`Analysis: ${report.analysis_result}`);
  console.log(`Date: ${report.created_at}`);
  console.log(`File URL: http://localhost:8000${report.file_path}`);
});
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Pet not found"
}
```

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Access denied (user doesn't have permission)
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Response Format

All errors follow this format:
```json
{
  "detail": "Error message description"
}
```

### Common Error Scenarios

#### 1. Invalid Token
```json
{
  "detail": "Invalid token"
}
```
**Solution:** Re-login to get a new access token

#### 2. Access Denied
```json
{
  "detail": "Access denied"
}
```
**Solution:** Ensure you're using the correct `user_id` that matches your token

#### 3. Pet Not Found
```json
{
  "detail": "Pet not found. Please complete your pet profile first."
}
```
**Solution:** Create a pet profile using `/user/{user_id}/pet/{pet_id}/profile`

#### 4. Invalid File Type
```json
{
  "detail": "Unsupported file type. Please upload an image file."
}
```
**Solution:** Upload a valid image file (JPG, PNG, etc.)

---

## Complete Workflow Example

Here's a complete example of using the API from registration to getting a chat response:

```javascript
// Step 1: Register
const registerResponse = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access_token, user_id } = await registerResponse.json();

// Step 2: Save Pet Profile
const profileResponse = await fetch(`http://localhost:8000/user/${user_id}/pet/my_dog_123/profile`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    petName: 'Max',
    breed: 'Labrador Retriever',
    weight: '30',
    age: '3',
    gender: 'Male',
    season: 'Summer',
    activityLevel: 'High',
    behaviorNotes: 'Friendly and active',
    medicalConditions: ['None'],
    goals: ['Maintain healthy weight']
  })
});
await profileResponse.json();

// Step 3: Send Chat Message
const chatResponse = await fetch(`http://localhost:8000/user/${user_id}/pet/my_dog_123/chat`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'What should I feed my dog?'
  })
});
const chatData = await chatResponse.json();
console.log('AI Response:', chatData.answer);

// Step 4: Upload Image
const fileInput = document.getElementById('imageInput');
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const imageResponse = await fetch(`http://localhost:8000/user/${user_id}/pet/my_dog_123/upload/analyze`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`
  },
  body: formData
});
const imageData = await imageResponse.json();
console.log('Breed:', imageData.breed);
console.log('Health Analysis:', imageData.health_analysis);

// Step 5: Get Chat History
const messagesResponse = await fetch(`http://localhost:8000/user/${user_id}/pet/my_dog_123/chat/messages`, {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
const messagesData = await messagesResponse.json();
console.log('All Messages:', messagesData.messages);
```

---

## API Rate Limits & Performance

### Expected Response Times

- **Health Check**: < 10ms
- **Greetings**: ~10ms (instant static response)
- **FAQ Queries**: ~100-300ms (database vector search)
- **GPT Responses**: ~1-3 seconds
- **Image Analysis**: ~2-5 seconds (breed detection + health analysis)
- **Nutrition Calculation**: ~1-2 seconds

### Rate Limits

Currently, no explicit rate limits are enforced. However, for production use, consider:
- Implementing rate limiting per user
- Caching frequent queries
- Using connection pooling for database

---

## Testing with Postman

### Import Collection

You can import these endpoints into Postman:

1. Create a new collection: "Dog Health AI API"
2. Add environment variables:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (will be set after login)
   - `user_id`: (will be set after login)
   - `pet_id`: `my_dog_123`

3. Set up Pre-request Script for authenticated endpoints:
```javascript
pm.request.headers.add({
  key: 'Authorization',
  value: 'Bearer ' + pm.environment.get('access_token')
});
```

4. Use variables in URLs:
```
{{base_url}}/user/{{user_id}}/pet/{{pet_id}}/chat
```

---

## Additional Notes

### Image URLs

After uploading an image, the URL format is:
```
http://localhost:8000/images/{filename}
```

You can use this URL in:
- Chat messages (`image_url` field)
- HTML `<img>` tags
- API requests that reference images

### Report URLs

Report files are accessible at:
```
http://localhost:8000/reports/{filename}
```

### CORS

The API allows requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

For production, update CORS settings in `backend/main.py`.

---

**For more information, see the main [README.md](README.md)**

