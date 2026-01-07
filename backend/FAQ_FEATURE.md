# FAQ-Based Intelligent Chat Feature

## Overview

This feature adds semantic search-based FAQ answering to the Dog Health AI chat system. It uses OpenAI embeddings to match user questions (including Hinglish, informal English, and typos) with relevant FAQ answers.

## Architecture

### Components

1. **`backend/services/faq_service.py`** - Core FAQ service with:
   - Semantic similarity search using OpenAI embeddings
   - In-memory caching of FAQs and embeddings
   - Support for Hinglish and informal queries

2. **Updated Chat Endpoint** (`/user/{user_id}/pet/{pet_id}/chat`):
   - Auto-detects input type (image vs text)
   - Routes text-only queries to FAQ search
   - Falls back to GPT when no strong FAQ match found

3. **LLM Service Enhancement**:
   - New `generate_dynamic_answer_with_faq_context()` function
   - Provides FAQ context to GPT for better responses

## Features

### 1. Semantic Search
- Uses OpenAI `text-embedding-3-small` model
- Cosine similarity for matching
- Handles:
  - Spelling mistakes
  - Hinglish queries (e.g., "mera dog subah yellow vomit kyu karta h?")
  - Informal English
  - Rephrased questions

### 2. Confidence Levels
- **High** (≥0.85): Direct FAQ answer returned
- **Medium** (≥0.70): FAQ answer returned, may enhance with GPT
- **Low** (≥0.55): GPT answer with FAQ context
- **None** (<0.55): GPT answer only

### 3. Auto-Detection
The system automatically detects:
- **Image-based queries**: Uses existing image analysis flow
- **Text-only queries**: Routes to FAQ semantic search

## API Response Format

```json
{
  "answer": "Answer text here...",
  "matched_question": "Matching FAQ question (if found)",
  "score": 0.87,
  "source": "faq",  // or "gpt"
  "confidence": "high"  // "high", "medium", "low", or "none"
}
```

## Setup

### 1. FAQ JSON File
Place `refined_faqs.json` or `faqs_final.json` in the project root directory.

Format:
```json
[
  {
    "question": "Why does my dog vomit yellow bile in the morning?",
    "answer": "Morning bile vomiting often happens...",
    "category": "Dog Health"
  }
]
```

### 2. OpenAI API Key
Ensure `OPENAI_API_KEY` is set in `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Dependencies
All required packages are already in `requirements.txt`:
- `openai` - For embeddings and GPT
- `numpy` - For vector operations

## Usage

### Testing FAQ Search

Use the test endpoint:
```bash
GET /test/faq-search?q=mera%20dog%20subah%20yellow%20vomit%20kyu%20karta%20h
```

### Chat Endpoint

**Text-only query:**
```bash
POST /user/{user_id}/pet/{pet_id}/chat
{
  "question": "mera dog subah yellow vomit kyu karta h?",
  "pet_profile": {...}
}
```

**Image-based query (unchanged):**
```bash
POST /user/{user_id}/pet/{pet_id}/chat
{
  "question": "What do you see?",
  "image_url": "/images/photo.jpg",
  "pet_profile": {...}
}
```

## How It Works

1. **Text-Only Query Flow**:
   ```
   User Question
   ↓
   Check for image_url/image_analysis_context
   ↓ (No image found)
   Generate embedding for question
   ↓
   Search FAQs using cosine similarity
   ↓
   Match found?
   ├─ Yes (high/medium confidence) → Return FAQ answer
   ├─ Yes (low confidence) → GPT with FAQ context
   └─ No → GPT with FAQ context as background
   ```

2. **Image-Based Query Flow** (unchanged):
   ```
   User Question + Image
   ↓
   Image analysis flow (existing)
   ↓
   GPT with image context
   ```

## Caching

- FAQ embeddings are cached in `backend/services/faq_embeddings_cache.pkl`
- First load generates embeddings (takes ~30-60 seconds)
- Subsequent loads use cache (instant)
- To regenerate: Delete cache file or call `load_or_generate_embeddings(force_regenerate=True)`

## Performance

- **Embedding Generation**: ~30-60 seconds (first time only)
- **Cache Load**: <1 second
- **FAQ Search**: ~100-300ms (includes embedding generation for query)
- **GPT Fallback**: ~1-3 seconds

## Safety Rules

All responses follow these rules:
- No medical diagnosis
- Friendly, concise, chat-style responses
- Advisory language when needed
- Always suggest veterinary consultation for serious health concerns

## Troubleshooting

### FAQ file not found
- Ensure `refined_faqs.json` exists in project root
- Check file path in error message

### Embeddings not generating
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI API quota
- Review error logs

### Low similarity scores
- Normal for very different queries
- System will use GPT fallback automatically
- Consider adding more FAQs to improve coverage

## Example Queries

### Hinglish Support
- ✅ "mera dog subah yellow vomit kyu karta h?"
- ✅ "kya dogs ko chocolate de sakte hain?"
- ✅ "dog ka diet kya hona chahiye?"

### Informal English
- ✅ "why does my dog puke yellow stuff in morning"
- ✅ "can i give chocolate to dog"
- ✅ "what should i feed my pup"

### Rephrased Questions
- ✅ "low fat food for dogs?"
- ✅ "recommendations for low-fat canine diet"
- ✅ "best diet for dogs with fat sensitivity"

## Future Enhancements

- [ ] PostgreSQL + pgvector for database-backed FAQ storage
- [ ] Multi-language support (Hindi, etc.)
- [ ] User feedback loop for improving matches
- [ ] FAQ analytics and usage tracking

