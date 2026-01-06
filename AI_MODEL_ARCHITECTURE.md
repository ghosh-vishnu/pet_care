# Dog Health AI - AI Model Architecture (AI Model कैसे काम करता है)

यह document समझाता है कि Dog Health AI application में AI models कैसे काम करते हैं।

---

## 📋 Table of Contents

1. [Overview (सम्पूर्ण दृष्टिकोण)](#overview)
2. [AI Models Used (उपयोग किए गए AI Models)](#ai-models-used)
3. [Image Analysis Flow (Image Analysis का Flow)](#image-analysis-flow)
4. [Chat System Flow (Chat System का Flow)](#chat-system-flow)
5. [Nutrition Calculation Flow (Nutrition Calculation का Flow)](#nutrition-calculation-flow)
6. [Model Details (Model की Details)](#model-details)
7. [API Integration (API Integration)](#api-integration)

---

## Overview (सम्पूर्ण दृष्टिकोण)

यह application multiple AI models use करता है dog health analysis के लिए:

- **Computer Vision Models** (PyTorch-based): Dog detection और breed classification
- **OpenAI Vision API**: Advanced health analysis from images
- **OpenAI GPT Models**: Chat responses, nutrition calculations, report analysis

---

## AI Models Used (उपयोग किए गए AI Models)

### 1. **Dog Detector Model**
- **Technology**: PyTorch (MobileNet V3 Small)
- **Purpose**: Image में dog है या नहीं detect करना
- **Location**: `backend/services/dog_detector.py`
- **Model**: ImageNet pre-trained MobileNet V3 Small
- **Method**: 
  - Image को 224x224 में resize करता है
  - ImageNet classes में से top prediction निकालता है
  - 50+ dog-related keywords से match करता है
  - Top 5 predictions check करता है (fallback)

### 2. **Breed Classifier Model**
- **Technology**: PyTorch (EfficientNet-B0)
- **Purpose**: Dog की breed identify करना
- **Location**: `backend/services/breed_classifier.py`
- **Model**: Custom trained EfficientNet-B0 (120 dog breeds)
- **Method**:
  - Image को pre-process करता है (resize, normalize)
  - 120 breeds में से prediction करता है
  - Confidence score के साथ breed return करता है

### 3. **OpenAI Vision API (GPT-4o-mini)**
- **Technology**: OpenAI GPT-4o-mini with Vision
- **Purpose**: Image से health indicators analyze करना
- **Location**: `backend/services/health_vision_service.py`
- **Method**:
  - Image को base64 में encode करता है
  - Detailed prompt के साथ Vision API को भेजता है
  - Health observations parse करता है (body condition, coat, eyes, energy)
  - Structured health analysis return करता है

### 4. **OpenAI GPT Models (Chat & Analysis)**
- **Models Used**:
  - **GPT-3.5-turbo**: Chat conversations के लिए
  - **GPT-4o-mini**: Nutrition calculations और report analysis के लिए
- **Location**: 
  - Chat: `backend/services/llm_service.py`
  - Nutrition: `backend/services/nutrition_service.py`
  - Reports: `backend/services/report_reader.py`

---

## Image Analysis Flow (Image Analysis का Flow)

जब user एक image upload करता है, यह step-by-step process follow होता है:

```
1. Image Upload
   ↓
2. Image Validation (format, size)
   ↓
3. Dog Detection (MobileNet V3)
   ├─ ✅ Dog found → Continue
   └─ ❌ No dog → Error message
   ↓
4. Breed Classification (EfficientNet-B0)
   ├─ Breed identified with confidence
   └─ Falls back to detector label if needed
   ↓
5. Image Quality Analysis (OpenCV)
   ├─ Brightness, clarity, color balance
   └─ Basic image metrics
   ↓
6. Health Analysis (OpenAI Vision API)
   ├─ GPT-4o-mini Vision API call
   ├─ Analyzes: body condition, coat, eyes, energy
   ├─ Extracts structured observations
   └─ Falls back to OpenCV analysis if API fails
   ↓
7. Health Summary Generation
   ├─ Formats user-friendly response
   ├─ Includes breed, health status, observations
   ├─ Adds recommendations and concerns
   └─ User-friendly format (no markdown headings)
   ↓
8. Save to Database & Return Response
```

### Code Flow (main.py - `/upload/analyze` endpoint):

```python
# Step 1: Validate image contains dog
is_valid_dog, dog_conf, dog_message, detected_label = validate_dog_image(dst)

# Step 2: Predict breed
breed, breed_conf = predict_breed(dst)

# Step 3: Basic image analysis
brightness, clarity, color_balance, summary, nutrition = analyze_image(dst)

# Step 4: Advanced health analysis
health_analysis = analyze_health_with_vision(dst, breed)
health_summary = generate_health_summary(health_analysis, clean_breed, breed_conf)

# Step 5: Save and return
await write_ai_message_to_database(db, pet.id, full_summary, sender_is_user=False)
```

---

## Chat System Flow (Chat System का Flow)

Chat system तीन layers use करता है:

```
User Question
   ↓
1. Keyword Check (Nutrition-related?)
   ├─ Yes → Calculate nutrients
   └─ No → Continue
   ↓
2. FAQ Semantic Matching (Sentence Transformers)
   ├─ Load pre-computed embeddings
   ├─ Calculate cosine similarity
   ├─ If score > 0.6 → Return FAQ answer
   └─ Else → Continue
   ↓
3. OpenAI GPT-3.5-turbo Fallback
   ├─ System prompt with pet profile context
   ├─ Include chat history (last 5 messages)
   ├─ Generate contextual response
   └─ Return to user
   ↓
4. Fallback (if OpenAI fails)
   └─ Rule-based responses based on keywords
```

### Models Used in Chat:

1. **Sentence Transformers (all-MiniLM-L6-v2)**
   - FAQ questions को embeddings में convert करता है
   - User query को encode करता है
   - Cosine similarity से best match find करता है

2. **OpenAI GPT-3.5-turbo**
   - Dynamic responses generate करता है
   - Pet profile context use करता है
   - Conversation history maintain करता है

3. **Fallback System**
   - Rule-based responses
   - Keyword matching
   - No API dependency

### Code Flow (llm_service.py):

```python
def generate_dynamic_answer(question, history, location, pet_profile):
    # Build system prompt with pet profile
    system_prompt = f"""You are a helpful AI assistant...
    Pet Profile:
    - Name: {pet_profile.get('petName')}
    - Breed: {pet_profile.get('breed')}
    ...
    """
    
    # Add chat history
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-5:]:
        messages.append({"role": "user", "content": msg["question"]})
        messages.append({"role": "assistant", "content": msg["answer"]})
    
    # Generate response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
```

---

## Nutrition Calculation Flow (Nutrition Calculation का Flow)

Nutrition calculation OpenAI GPT-4o-mini के साथ structured JSON output use करता है:

```
Pet Profile Input
   ↓
1. Build System Prompt (AAFCO standards)
   ├─ RER calculation: 70 * (Weight in kg)^0.75
   ├─ MER calculation: RER * multiplier
   ├─ Macronutrient distribution
   └─ Supplement recommendations
   ↓
2. Call GPT-4o-mini with JSON schema
   ├─ Model: gpt-4o-mini
   ├─ Response format: JSON object
   ├─ Temperature: 0.7
   └─ Structured output guarantee
   ↓
3. Parse JSON Response
   ├─ Calories (kcal/day)
   ├─ Protein (grams/day)
   ├─ Fat (grams/day)
   ├─ Carbs (grams/day)
   ├─ Macro distribution
   └─ Supplement suggestions
   ↓
4. Validate & Return
   └─ Pydantic model validation
```

### Code Flow (nutrition_service.py):

```python
async def calculate_and_suggest_nutrition(pet_profile):
    # System prompt with AAFCO standards
    system_prompt = """
    You are an expert Certified Veterinary Nutritionist.
    Calculation Steps MUST be based on industry standards:
    1. RER = 70 * (Weight in kg)^0.75
    2. MER = RER * multiplier (based on age, activity)
    3. Macronutrients based on AAFCO minimums
    4. Supplement recommendations
    """
    
    # Structured JSON output
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        response_format={"type": "json_object"},  # Guaranteed JSON
        temperature=0.7
    )
    
    # Parse and validate
    result_dict = json.loads(response.choices[0].message.content)
    return NutritionResult.model_validate(result_dict)
```

---

## Model Details (Model की Details)

### 1. Dog Detector (MobileNet V3 Small)

**Architecture:**
- Pre-trained on ImageNet (1000 classes)
- MobileNet V3 Small (lightweight, fast)
- Input: 224x224 RGB image
- Output: 1000 class probabilities

**Detection Logic:**
```python
DOG_KEYWORDS = {
    "dog", "retriever", "terrier", "poodle", "beagle",
    "husky", "shepherd", "bulldog", ... (50+ keywords)
}

# Method 1: Direct keyword match in top prediction
if any(k in label.lower() for k in DOG_KEYWORDS):
    return True

# Method 2: Check top 5 predictions
for prob, idx in top5_predictions:
    if any(k in pred_label for k in DOG_KEYWORDS):
        if prob >= 0.15:
            return True
```

### 2. Breed Classifier (EfficientNet-B0)

**Architecture:**
- EfficientNet-B0 (custom trained)
- 120 dog breeds classes
- Input: 224x224 RGB image
- Output: 120 breed probabilities

**Processing:**
```python
# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

# Prediction
outputs = model(img_tensor)
probabilities = softmax(outputs)
confidence, predicted = max(probabilities)
breed = BREED_CLASSES[predicted]
```

### 3. Health Vision Analysis (GPT-4o-mini Vision)

**Prompt Structure:**
```python
prompt = f"""Analyze this dog image for health indicators. Focus on:
1. Body condition (underweight, normal, overweight)
2. Coat condition (healthy, dry, matted, skin issues)
3. Eye condition (clear, discharge, redness)
4. Overall posture and energy level
5. Any visible health concerns
6. General appearance and vitality

{"This appears to be a " + breed + " breed." if breed else ""}
"""
```

**Response Parsing:**
- Keyword-based extraction
- Maps to structured fields:
  - `body_condition`: "Normal" | "Underweight" | "Overweight"
  - `coat_condition`: "Healthy" | "Dry" | "Needs Grooming" | "Skin Issues"
  - `eye_condition`: "Normal" | "Needs Attention"
  - `energy_level`: "Normal" | "High" | "Low"

### 4. Chat Models (GPT-3.5-turbo / GPT-4o-mini)

**Chat System (GPT-3.5-turbo):**
- Model: `gpt-3.5-turbo`
- Temperature: 0.7
- Max tokens: 500
- Context: Pet profile + last 5 messages

**Nutrition System (GPT-4o-mini):**
- Model: `gpt-4o-mini`
- Temperature: 0.7
- Response format: JSON object
- Context: Pet profile + AAFCO standards

**Report Analysis (GPT-4o-mini):**
- Model: `gpt-4o-mini`
- Temperature: 0.7
- Context: Vet report text (up to 4000 chars)

---

## API Integration (API Integration)

### OpenAI API Configuration

**Environment Variables:**
```bash
OPENAI_API_KEY=your-api-key-here
```

**Client Initialization:**
```python
from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
```

**Error Handling:**
- API key not set → Fallback responses
- Quota exceeded → User-friendly error message
- Invalid API key → Error message
- API failure → Fallback to rule-based responses

### API Endpoints Used

1. **Chat Completions API**
   - Endpoint: `client.chat.completions.create()`
   - Used for: Chat, nutrition, reports

2. **Vision API (Chat Completions with images)**
   - Endpoint: `client.chat.completions.create()` (with image_url)
   - Used for: Health analysis from images
   - Model: `gpt-4o-mini`

---

## Key Features (मुख्य Features)

### 1. **Multi-Model Architecture**
- Local models (PyTorch) for fast dog/breed detection
- Cloud models (OpenAI) for advanced analysis
- Fallback mechanisms for reliability

### 2. **Structured Output**
- Health analysis: Structured dictionary
- Nutrition: JSON schema with Pydantic validation
- Chat: Natural language with context

### 3. **User-Friendly Formatting**
- Health summaries: Clean, friendly format (no markdown)
- Bullet points, emojis, simple language
- Under 300 words, actionable recommendations

### 4. **Error Resilience**
- Fallback to OpenCV if Vision API fails
- Rule-based responses if OpenAI fails
- Graceful degradation

---

## File Structure (File Structure)

```
backend/services/
├── dog_detector.py          # MobileNet V3 - Dog detection
├── breed_classifier.py      # EfficientNet-B0 - Breed classification
├── health_vision_service.py # GPT-4o-mini Vision - Health analysis
├── llm_service.py           # GPT-3.5-turbo - Chat responses
├── nutrition_service.py     # GPT-4o-mini - Nutrition calculations
└── report_reader.py         # GPT-4o-mini - Report analysis
```

---

## Performance Considerations (Performance)

1. **Model Loading**
   - Models cached with `@lru_cache` decorator
   - Load once, reuse for all requests

2. **API Calls**
   - Sequential calls (not parallel)
   - Timeout handling
   - Retry logic (implicit via error handling)

3. **Image Processing**
   - PIL for format support (AVIF, WebP, etc.)
   - OpenCV for computer vision analysis
   - Efficient preprocessing pipelines

---

## Future Improvements (भविष्य के सुधार)

1. **Parallel API Calls**: Health analysis और breed detection parallel में
2. **Caching**: Frequent queries के responses cache करना
3. **Model Updates**: Latest EfficientNet versions use करना
4. **Batch Processing**: Multiple images को एक साथ process करना
5. **Custom Training**: Domain-specific health analysis model train करना

---

## Summary (सारांश)

Dog Health AI application में AI models का उपयोग इस प्रकार है:

1. **Computer Vision (Local)**: Fast dog detection और breed classification
2. **OpenAI Vision API**: Advanced health analysis from images
3. **OpenAI GPT Models**: Chat, nutrition, और report analysis
4. **Hybrid Approach**: Local + Cloud models for best performance और reliability

सभी models एक साथ काम करते हैं user को comprehensive, user-friendly health analysis provide करने के लिए। 🐕🤖




