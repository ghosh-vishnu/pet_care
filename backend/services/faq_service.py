# faq_service.py - FAQ-based Semantic Search Service
import json
import os
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import pickle

load_dotenv()

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("WARNING: OpenAI API key not set. FAQ semantic search will not work.")

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# Similarity thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.85  # Strong match - use FAQ answer directly
MEDIUM_CONFIDENCE_THRESHOLD = 0.70  # Moderate match - use FAQ with GPT enhancement
LOW_CONFIDENCE_THRESHOLD = 0.55  # Weak match - use GPT with FAQ context

# In-memory cache for FAQs and embeddings
_faq_cache: Optional[List[Dict]] = None
_embeddings_cache: Optional[np.ndarray] = None
_cache_file = os.path.join(os.path.dirname(__file__), "faq_embeddings_cache.pkl")


def load_faqs_from_json(file_path: Optional[str] = None) -> List[Dict]:
    """
    Load FAQs from JSON file.
    Defaults to refined_faqs.json in project root.
    """
    if file_path is None:
        # Try multiple possible locations
        # Go up from services/ -> backend/ -> project root
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(backend_dir)
        
        possible_paths = [
            os.path.join(project_root, "refined_faqs.json"),
            os.path.join(project_root, "faqs_final.json"),
            os.path.join(backend_dir, "refined_faqs.json"),
            os.path.join(backend_dir, "faqs_final.json"),
            os.path.join(os.path.dirname(__file__), "refined_faqs.json"),
            os.path.join(os.path.dirname(__file__), "faqs_final.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if file_path is None:
            raise FileNotFoundError(
                f"FAQ JSON file not found. Tried: {possible_paths}\n"
                f"Please ensure refined_faqs.json or faqs_final.json exists in project root."
            )
    
    with open(file_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)
    
    # Validate FAQ structure
    for faq in faqs:
        if "question" not in faq or "answer" not in faq:
            raise ValueError("Invalid FAQ format: missing 'question' or 'answer'")
    
    print(f"Loaded {len(faqs)} FAQs from {file_path}")
    return faqs


def generate_embedding(text: str) -> Optional[np.ndarray]:
    """
    Generate embedding for text using OpenAI.
    Returns None if OpenAI client is not available.
    """
    if client is None:
        return None
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def load_or_generate_embeddings(force_regenerate: bool = False) -> Tuple[List[Dict], np.ndarray]:
    """
    Load FAQs and their embeddings.
    Uses cache file if available, otherwise generates embeddings and saves cache.
    """
    global _faq_cache, _embeddings_cache
    
    # Check if already loaded in memory
    if _faq_cache is not None and _embeddings_cache is not None and not force_regenerate:
        return _faq_cache, _embeddings_cache
    
    # Try to load from cache file
    if os.path.exists(_cache_file) and not force_regenerate:
        try:
            with open(_cache_file, "rb") as f:
                cache_data = pickle.load(f)
                _faq_cache = cache_data.get("faqs")
                _embeddings_cache = cache_data.get("embeddings")
                if _faq_cache and _embeddings_cache is not None:
                    print(f"Loaded {len(_faq_cache)} FAQs with embeddings from cache")
                    return _faq_cache, _embeddings_cache
        except Exception as e:
            print(f"Error loading cache: {e}, regenerating embeddings...")
    
    # Load FAQs
    faqs = load_faqs_from_json()
    
    if client is None:
        print("WARNING: OpenAI client not available. FAQ embeddings cannot be generated.")
        return faqs, None
    
    # Generate embeddings
    print("Generating embeddings for FAQs...")
    embeddings_list = []
    valid_faqs = []
    
    for i, faq in enumerate(faqs):
        question = faq["question"]
        embedding = generate_embedding(question)
        
        if embedding is not None:
            embeddings_list.append(embedding)
            valid_faqs.append(faq)
        else:
            print(f"Warning: Failed to generate embedding for FAQ {i+1}: {question[:50]}...")
    
    if not embeddings_list:
        print("ERROR: No embeddings generated. FAQ search will not work.")
        return faqs, None
    
    embeddings_array = np.array(embeddings_list, dtype=np.float32)
    
    # Save to cache
    try:
        cache_dir = os.path.dirname(_cache_file)
        os.makedirs(cache_dir, exist_ok=True)
        with open(_cache_file, "wb") as f:
            pickle.dump({"faqs": valid_faqs, "embeddings": embeddings_array}, f)
        print(f"Cached embeddings to {_cache_file}")
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")
    
    _faq_cache = valid_faqs
    _embeddings_cache = embeddings_array
    
    return valid_faqs, embeddings_array


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def search_faqs(
    query: str,
    top_k: int = 5,
    min_similarity: float = LOW_CONFIDENCE_THRESHOLD
) -> List[Tuple[Dict, float]]:
    if client is None:
        print("OpenAI client not available for FAQ search")
        return []
    
    # Load FAQs and embeddings (lazy initialization)
    try:
        _initialize_on_first_use()
        faqs, embeddings = load_or_generate_embeddings()
        if embeddings is None or len(faqs) == 0:
            print("No FAQ embeddings available")
            return []
    except Exception as e:
        print(f"Error loading FAQs: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    # Generate embedding for query
    try:
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            print("Could not generate query embedding")
            return []
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return []
    
    # Calculate similarities
    try:
        similarities = []
        for i, faq_embedding in enumerate(embeddings):
            similarity = cosine_similarity(query_embedding, faq_embedding)
            if similarity >= min_similarity:
                similarities.append((faqs[i], similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return similarities[:top_k]
    except Exception as e:
        print(f"Error calculating similarities: {e}")
        return []


def get_faq_answer(
    query: str,
    top_k: int = 3
) -> Tuple[Optional[str], Optional[Dict], str, float]:
    """
    Get best FAQ answer for a query.
    
    Returns:
        Tuple of (answer, best_faq, confidence_level, similarity_score)
        - answer: The FAQ answer text, or None if no good match
        - best_faq: The best matching FAQ dict, or None
        - confidence_level: "high", "medium", "low", or "none"
        - similarity_score: The similarity score (0-1)
    """
    try:
        results = search_faqs(query, top_k=top_k, min_similarity=LOW_CONFIDENCE_THRESHOLD)
        
        if not results:
            return None, None, "none", 0.0
        
        best_faq, similarity = results[0]
        
        # Ensure best_faq has required fields
        if not best_faq or "answer" not in best_faq:
            return None, None, "none", 0.0
        
        # Determine confidence level
        if similarity >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = "high"
            # High confidence - return FAQ answer directly
            return best_faq["answer"], best_faq, confidence, similarity
        elif similarity >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "medium"
            # Medium confidence - can use FAQ answer, but might enhance with GPT
            return best_faq["answer"], best_faq, confidence, similarity
        elif similarity >= LOW_CONFIDENCE_THRESHOLD:
            confidence = "low"
            # Low confidence - provide FAQ as context to GPT
            return best_faq["answer"], best_faq, confidence, similarity
        else:
            return None, None, "none", similarity
    except Exception as e:
        print(f"Error in get_faq_answer: {e}")
        import traceback
        traceback.print_exc()
        return None, None, "none", 0.0


def get_faq_context_for_gpt(query: str, top_k: int = 3) -> str:
    """
    Get relevant FAQ context to provide to GPT when no strong match is found.
    Useful for GPT fallback scenarios.
    """
    try:
        results = search_faqs(query, top_k=top_k, min_similarity=0.3)  # Lower threshold for context
        
        if not results:
            return ""
        
        context_lines = ["Relevant FAQ context:"]
        for faq, similarity in results[:top_k]:
            if faq and "question" in faq and "answer" in faq:
                context_lines.append(f"Q: {faq['question']}")
                context_lines.append(f"A: {faq['answer']}")
                context_lines.append("")  # Blank line between FAQs
        
        return "\n".join(context_lines)
    except Exception as e:
        print(f"Error in get_faq_context_for_gpt: {e}")
        return ""


# Initialize on module load (non-blocking)
# We'll load on first use instead to avoid blocking server startup
def _initialize_on_first_use():
    """Initialize FAQ embeddings on first use rather than module load."""
    global _faq_cache, _embeddings_cache
    if _faq_cache is None or _embeddings_cache is None:
        try:
            load_or_generate_embeddings()
        except Exception as e:
            print(f"Warning: Could not initialize FAQ embeddings: {e}")
            # Don't block - will retry on first search

# Don't initialize on import - do it lazily

