import os
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
import numpy as np

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

# Similarity thresholds (configurable)
HIGH_CONFIDENCE_THRESHOLD = float(os.getenv("FAQ_HIGH_THRESHOLD", "0.85"))
MEDIUM_CONFIDENCE_THRESHOLD = float(os.getenv("FAQ_MEDIUM_THRESHOLD", "0.70"))
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("FAQ_LOW_THRESHOLD", "0.55"))


def generate_embedding(text_input: str) -> Optional[np.ndarray]:
    """
    Generate embedding for text using OpenAI.
    Returns None if OpenAI client is not available.
    
    This is called ONCE per query.
    """
    if client is None:
        return None
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text_input,
        )
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def search_faqs_vector_db(
    db: Session,
    query_embedding: np.ndarray,
    top_k: int = 3,
    min_similarity: float = LOW_CONFIDENCE_THRESHOLD
) -> List[Tuple[Dict, float]]:
    try:
        # Check if pgvector extension is enabled
        try:
            db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.commit()
        except:
            pass  # Extension might already exist or not available
        
        # Convert numpy array to list for pgvector
        embedding_list = query_embedding.tolist()
        
        # Single vector similarity query using pgvector
        # Using cosine distance (<->) - lower is more similar
        # We convert to similarity: 1 - distance
        # Note: We cast the Python list directly to vector type
        query = text("""
            SELECT 
                id,
                question,
                answer,
                category,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM faqs
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> CAST(:query_embedding AS vector)) >= :min_similarity
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)
        
        # Convert list to string format for pgvector
        embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"
        
        result = db.execute(
            query,
            {
                "query_embedding": embedding_str,
                "min_similarity": min_similarity,
                "top_k": top_k
            }
        )
        
        results = []
        for row in result:
            faq_dict = {
                "id": row.id,
                "question": row.question,
                "answer": row.answer,
                "category": row.category
            }
            similarity = float(row.similarity)
            results.append((faq_dict, similarity))
        
        return results
        
    except Exception as e:
        # Fallback: If pgvector query fails, try in-memory fallback
        print(f"pgvector query failed, using fallback: {e}")
        return search_faqs_fallback(db, query_embedding, top_k, min_similarity)


def search_faqs_fallback(
    db: Session,
    query_embedding: np.ndarray,
    top_k: int = 3,
    min_similarity: float = LOW_CONFIDENCE_THRESHOLD
) -> List[Tuple[Dict, float]]:
    """
    Fallback FAQ search using cosine similarity in Python.
    Used when pgvector is not available or query fails.
    
    This loads ALL FAQs into memory (not ideal, but works as fallback).
    """
    from models.database_models import FAQ
    
    try:
        # Get all FAQs with embeddings
        faqs = db.query(FAQ).filter(FAQ.embedding.isnot(None)).all()
        
        if not faqs:
            return []
        
        similarities = []
        for faq in faqs:
            # Convert embedding to numpy array
            if isinstance(faq.embedding, list):
                faq_embedding = np.array(faq.embedding, dtype=np.float32)
            else:
                continue
            
            # Calculate cosine similarity
            dot_product = np.dot(query_embedding, faq_embedding)
            norm_query = np.linalg.norm(query_embedding)
            norm_faq = np.linalg.norm(faq_embedding)
            
            if norm_query == 0 or norm_faq == 0:
                similarity = 0.0
            else:
                similarity = float(dot_product / (norm_query * norm_faq))
            
            if similarity >= min_similarity:
                faq_dict = {
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }
                similarities.append((faq_dict, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
        
    except Exception as e:
        print(f"Error in fallback FAQ search: {e}")
        return []


def get_faq_answer_optimized(
    db: Session,
    query: str,
    top_k: int = 3
) -> Tuple[Optional[str], Optional[Dict], str, float]:
    """
    Get best FAQ answer using optimized database vector search.
    
    Process:
    1. Generate embedding ONCE for query
    2. Execute SINGLE database query for similarity search
    3. Return best match with confidence level
    
    Args:
        db: Database session
        query: User's question (can be Hinglish, informal, with typos)
        top_k: Number of top results to consider
    
    Returns:
        Tuple of (answer, best_faq, confidence_level, similarity_score)
    """
    if client is None:
        return None, None, "none", 0.0
    
    try:
        # Step 1: Generate embedding ONCE
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            return None, None, "none", 0.0
        
        # Step 2: Single database query for similarity search
        results = search_faqs_vector_db(db, query_embedding, top_k, LOW_CONFIDENCE_THRESHOLD)
        
        if not results:
            return None, None, "none", 0.0
        
        # Step 3: Get best match
        best_faq, similarity = results[0]
        
        # Ensure best_faq has required fields
        if not best_faq or "answer" not in best_faq:
            return None, None, "none", 0.0
        
        # Step 4: Determine confidence level
        if similarity >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = "high"
            return best_faq["answer"], best_faq, confidence, similarity
        elif similarity >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "medium"
            return best_faq["answer"], best_faq, confidence, similarity
        elif similarity >= LOW_CONFIDENCE_THRESHOLD:
            confidence = "low"
            return best_faq["answer"], best_faq, confidence, similarity
        else:
            return None, None, "none", similarity
            
    except Exception as e:
        print(f"Error in get_faq_answer_optimized: {e}")
        import traceback
        traceback.print_exc()
        return None, None, "none", 0.0


def get_faq_context_for_gpt_optimized(
    db: Session,
    query: str,
    top_k: int = 3
) -> str:
    """
    Get relevant FAQ context for GPT fallback.
    Uses optimized database query.
    """
    if client is None:
        return ""
    
    try:
        # Generate embedding
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            return ""
        
        # Get top FAQs (lower threshold for context)
        results = search_faqs_vector_db(db, query_embedding, top_k, min_similarity=0.3)
        
        if not results:
            return ""
        
        # Build context string
        context_lines = ["Relevant FAQ context:"]
        for faq, similarity in results[:top_k]:
            if faq and "question" in faq and "answer" in faq:
                context_lines.append(f"Q: {faq['question']}")
                context_lines.append(f"A: {faq['answer']}")
                context_lines.append("")  # Blank line
        
        return "\n".join(context_lines)
        
    except Exception as e:
        print(f"Error in get_faq_context_for_gpt_optimized: {e}")
        return ""

