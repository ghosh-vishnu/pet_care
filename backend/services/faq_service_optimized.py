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
    Returns None if OpenAI client is not available or quota exceeded.
    
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
        error_msg = str(e).lower()
        # Check if it's a quota/API error - don't spam logs for known issue
        if "429" in error_msg or "quota" in error_msg or "insufficient_quota" in error_msg:
            print(f"OpenAI quota exceeded - embeddings unavailable, will use keyword fallback")
        else:
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


def sanitize_faq_answer(answer: str) -> str:
    """
    Sanitize FAQ answer to ensure it follows style guidelines:
    - Short, clear, chat-friendly (3-5 lines max)
    - No excessive formatting
    - Professional, friendly tone
    """
    if not answer:
        return answer
    
    # Limit to ~500 chars (roughly 3-5 lines)
    lines = answer.split('\n')
    if len(lines) > 5:
        answer = '\n'.join(lines[:5])
    if len(answer) > 500:
        answer = answer[:497] + "..."
    
    # Trim whitespace
    answer = answer.strip()
    
    return answer


def search_faqs_keyword_fallback(
    db: Session,
    query: str,
    top_k: int = 3
) -> List[Tuple[Dict, float]]:
    """
    Fallback keyword-based FAQ search when OpenAI embeddings are unavailable.
    Uses improved text matching with question priority and better scoring.
    
    Args:
        db: Database session
        query: User's question
        top_k: Number of top results to return
    
    Returns:
        List of (faq_dict, similarity_score) tuples
    """
    try:
        from models.database_models import FAQ
        from sqlalchemy import or_, and_
        
        # Extract meaningful keywords from query (remove common stop words)
        query_lower = query.lower().strip()
        stop_words = {'the', 'is', 'are', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'should', 'can', 'my', 'i', 'me', 'how', 'why', 'when', 'where', 'do', 'does', 'did', 'will', 'would', 'could', 'may', 'might'}
        
        # Get meaningful words (longer than 2 chars, not stop words)
        words = [w.strip() for w in query_lower.split() if len(w) > 2 and w not in stop_words]
        
        if not words:
            # If no meaningful keywords, try exact question match
            faqs = db.query(FAQ).filter(FAQ.question.ilike(f"%{query_lower}%")).limit(top_k).all()
            if faqs:
                return [({
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }, 0.7) for faq in faqs]
            return []
        
        # Priority: Match words in question field first (more important than answer)
        # Use AND logic for better precision - at least 2 keywords should match
        conditions_question = []
        conditions_answer = []
        
        for word in words[:8]:  # Use up to 8 meaningful words
            conditions_question.append(FAQ.question.ilike(f"%{word}%"))
            conditions_answer.append(FAQ.answer.ilike(f"%{word}%"))
        
        # First try: Match keywords in QUESTION field (higher priority)
        faqs_question_match = db.query(FAQ).filter(or_(*conditions_question)).all()
        
        # If we found good matches in question, prioritize those
        if faqs_question_match:
            results = []
            for faq in faqs_question_match:
                question_lower = faq.question.lower()
                answer_lower = faq.answer.lower()
                
                # Count matches in question (weighted higher)
                question_matches = sum(1 for word in words if word in question_lower)
                answer_matches = sum(1 for word in words if word in answer_lower)
                
                # Question matches are worth 2x, answer matches 1x
                total_score = (question_matches * 2) + answer_matches
                similarity = min(total_score / max(len(words) * 2, 1), 0.85)
                
                # Boost similarity if multiple question words match
                if question_matches >= 2:
                    similarity = min(similarity + 0.1, 0.85)
                
                results.append(({
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }, similarity))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            if results[0][1] >= 0.3:  # Only return if best match is reasonable
                return results[:top_k]
        
        # Fallback: Match keywords in ANSWER field (lower priority)
        faqs_answer_match = db.query(FAQ).filter(or_(*conditions_answer)).limit(top_k * 2).all()
        
        if faqs_answer_match:
            results = []
            for faq in faqs_answer_match:
                question_lower = faq.question.lower()
                answer_lower = faq.answer.lower()
                
                # Count matches (lower weight for answer-only matches)
                question_matches = sum(1 for word in words if word in question_lower)
                answer_matches = sum(1 for word in words if word in answer_lower)
                
                total_score = (question_matches * 2) + answer_matches
                similarity = min(total_score / max(len(words) * 2, 1), 0.75)  # Lower cap for answer matches
                
                results.append(({
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }, similarity))
            
            results.sort(key=lambda x: x[1], reverse=True)
            if results and results[0][1] >= 0.3:
                return results[:top_k]
        
        return []
        
    except Exception as e:
        print(f"Error in keyword fallback search: {e}")
        import traceback
        traceback.print_exc()
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
    3. If embedding fails (quota error), use keyword fallback
    4. Return best match with confidence level
    
    Args:
        db: Database session
        query: User's question (can be Hinglish, informal, with typos)
        top_k: Number of top results to consider
    
    Returns:
        Tuple of (answer, best_faq, confidence_level, similarity_score)
    """
    if client is None:
        # Try keyword fallback if OpenAI client not available
        print("OpenAI client not available, using keyword fallback")
        results = search_faqs_keyword_fallback(db, query, top_k)
        if results:
            best_faq, similarity = results[0]
            sanitized_answer = sanitize_faq_answer(best_faq["answer"])
            # Use "medium" confidence for keyword fallback to ensure direct return (no GPT call)
            confidence = "medium"
            return sanitized_answer, best_faq, confidence, similarity
        return None, None, "none", 0.0
    
    try:
        # Step 1: Generate embedding ONCE
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            # Try keyword fallback if embedding generation failed (likely quota exceeded)
            print("Embedding generation failed, trying keyword fallback")
            results = search_faqs_keyword_fallback(db, query, top_k)
            if results:
                best_faq, similarity = results[0]
                sanitized_answer = sanitize_faq_answer(best_faq["answer"])
                # Use "medium" confidence for keyword fallback to ensure direct return (no GPT call)
                confidence = "medium"
                return sanitized_answer, best_faq, confidence, similarity
            return None, None, "none", 0.0
        
        # Step 2: Single database query for similarity search
        results = search_faqs_vector_db(db, query_embedding, top_k, LOW_CONFIDENCE_THRESHOLD)
        
        if not results:
            # Try keyword fallback if vector search returned no results
            print("Vector search returned no results, trying keyword fallback")
            results = search_faqs_keyword_fallback(db, query, top_k)
            if results:
                best_faq, similarity = results[0]
                sanitized_answer = sanitize_faq_answer(best_faq["answer"])
                # Use "medium" confidence for keyword fallback to ensure direct return
                confidence = "medium"
                return sanitized_answer, best_faq, confidence, similarity
            return None, None, "none", 0.0
        
        # Step 3: Get best match
        best_faq, similarity = results[0]
        
        # Ensure best_faq has required fields
        if not best_faq or "answer" not in best_faq:
            return None, None, "none", 0.0
        
        # Step 4: Sanitize answer to ensure style compliance
        sanitized_answer = sanitize_faq_answer(best_faq["answer"])
        
        # Step 5: Determine confidence level
        if similarity >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = "high"
            return sanitized_answer, best_faq, confidence, similarity
        elif similarity >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "medium"
            return sanitized_answer, best_faq, confidence, similarity
        elif similarity >= LOW_CONFIDENCE_THRESHOLD:
            confidence = "low"
            return sanitized_answer, best_faq, confidence, similarity
        else:
            return None, None, "none", similarity
            
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a quota/API error
        if "429" in error_msg or "quota" in error_msg or "insufficient_quota" in error_msg:
            print(f"OpenAI quota exceeded, using keyword fallback: {e}")
            # Try keyword fallback when quota is exceeded
            try:
                results = search_faqs_keyword_fallback(db, query, top_k)
                if results:
                    best_faq, similarity = results[0]
                    sanitized_answer = sanitize_faq_answer(best_faq["answer"])
                    # Use "medium" confidence for keyword fallback to ensure direct return (no GPT call)
                    confidence = "medium"
                    return sanitized_answer, best_faq, confidence, similarity
            except Exception as fallback_error:
                print(f"Keyword fallback also failed: {fallback_error}")
                import traceback
                traceback.print_exc()
        
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
    Uses optimized database query with keyword fallback if embeddings fail.
    """
    if client is None:
        # Use keyword fallback
        results = search_faqs_keyword_fallback(db, query, top_k)
        if results:
            context_lines = ["Relevant FAQ context:"]
            for faq, similarity in results[:top_k]:
                if faq and "question" in faq and "answer" in faq:
                    context_lines.append(f"Q: {faq['question']}")
                    context_lines.append(f"A: {faq['answer']}")
                    context_lines.append("")  # Blank line
            return "\n".join(context_lines)
        return ""
    
    try:
        # Generate embedding
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            # Try keyword fallback if embedding generation failed
            results = search_faqs_keyword_fallback(db, query, top_k)
            if results:
                context_lines = ["Relevant FAQ context:"]
                for faq, similarity in results[:top_k]:
                    if faq and "question" in faq and "answer" in faq:
                        context_lines.append(f"Q: {faq['question']}")
                        context_lines.append(f"A: {faq['answer']}")
                        context_lines.append("")  # Blank line
                return "\n".join(context_lines)
            return ""
        
        # Get top FAQs (lower threshold for context)
        results = search_faqs_vector_db(db, query_embedding, top_k, min_similarity=0.3)
        
        if not results:
            # Try keyword fallback if vector search returned no results
            results = search_faqs_keyword_fallback(db, query, top_k)
            if results:
                context_lines = ["Relevant FAQ context:"]
                for faq, similarity in results[:top_k]:
                    if faq and "question" in faq and "answer" in faq:
                        context_lines.append(f"Q: {faq['question']}")
                        context_lines.append(f"A: {faq['answer']}")
                        context_lines.append("")  # Blank line
                return "\n".join(context_lines)
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
        error_msg = str(e).lower()
        # If quota error, try keyword fallback
        if "429" in error_msg or "quota" in error_msg or "insufficient_quota" in error_msg:
            print(f"OpenAI quota exceeded in context generation, using keyword fallback")
            try:
                results = search_faqs_keyword_fallback(db, query, top_k)
                if results:
                    context_lines = ["Relevant FAQ context:"]
                    for faq, similarity in results[:top_k]:
                        if faq and "question" in faq and "answer" in faq:
                            context_lines.append(f"Q: {faq['question']}")
                            context_lines.append(f"A: {faq['answer']}")
                            context_lines.append("")  # Blank line
                    return "\n".join(context_lines)
            except Exception as fallback_error:
                print(f"Keyword fallback failed in context generation: {fallback_error}")
        
        print(f"Error in get_faq_context_for_gpt_optimized: {e}")
        return ""

