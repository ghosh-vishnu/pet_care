#!/usr/bin/env python3
"""
Migration script to populate FAQs from JSON to database.
Generates embeddings and stores in PostgreSQL with pgvector support.

Usage:
    python migrate_faqs_to_db.py [--file path/to/faqs.json] [--force]
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine, Base
from models.database_models import FAQ
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
    print("ERROR: OPENAI_API_KEY not set in .env file")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
EMBEDDING_MODEL = "text-embedding-3-small"


def generate_embedding(text: str) -> list:
    """Generate embedding using OpenAI."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        error_msg = str(e)
        # Re-raise with context for quota errors
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            raise Exception(f"OpenAI quota exceeded: {error_msg}")
        # Re-raise other errors
        raise Exception(f"OpenAI API error: {error_msg}")


def load_faqs_from_json(file_path: str) -> list:
    """Load FAQs from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)
    
    if not isinstance(faqs, list):
        raise ValueError("FAQ JSON must be an array")
    
    # Validate structure
    for faq in faqs:
        if "question" not in faq or "answer" not in faq:
            raise ValueError("Each FAQ must have 'question' and 'answer' fields")
    
    return faqs


def migrate_faqs(db: Session, faqs_json: list, force: bool = False):
    """
    Migrate FAQs from JSON to database.
    Generates embeddings and stores with pgvector support.
    """
    # Ensure pgvector extension is enabled
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
        print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"⚠ Warning: Could not enable pgvector extension: {e}")
        print("  Continuing with fallback ARRAY storage...")
        # Rollback any failed transaction
        try:
            db.rollback()
        except:
            pass
    
    total = len(faqs_json)
    print(f"\n📊 Processing {total} FAQs...")
    
    added = 0
    updated = 0
    skipped = 0
    errors = 0
    quota_errors = 0
    
    for i, faq_data in enumerate(faqs_json, 1):
        question = faq_data["question"].strip()
        answer = faq_data["answer"].strip()
        category = faq_data.get("category", None)
        
        if not question or not answer:
            print(f"⚠ [{i}/{total}] Skipping invalid FAQ (empty question/answer)")
            skipped += 1
            continue
        
        # Start fresh transaction for each FAQ
        try:
            # Check if FAQ already exists
            existing = db.query(FAQ).filter(FAQ.question == question).first()
            
            if existing:
                if not force:
                    print(f"⊘ [{i}/{total}] Skipping existing: {question[:50]}...")
                    skipped += 1
                    continue
                else:
                    # Update existing
                    print(f"↻ [{i}/{total}] Updating: {question[:50]}...")
                    
                    # Generate embedding with error handling
                    embedding = None
                    try:
                        embedding = generate_embedding(question)
                    except Exception as emb_error:
                        error_msg = str(emb_error)
                        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                            print(f"   ⚠ OpenAI quota exceeded. Saving FAQ without embedding.")
                            quota_errors += 1
                        else:
                            print(f"   ⚠ Could not generate embedding: {emb_error}")
                            # Continue without embedding
                    
                    existing.answer = answer
                    existing.category = category
                    if embedding:
                        existing.embedding = embedding
                    
                    db.commit()
                    updated += 1
            else:
                # Create new FAQ
                print(f"✓ [{i}/{total}] Adding: {question[:50]}...")
                
                # Generate embedding with error handling
                embedding = None
                try:
                    embedding = generate_embedding(question)
                except Exception as emb_error:
                    error_msg = str(emb_error)
                    if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                        print(f"   ⚠ OpenAI quota exceeded. Saving FAQ without embedding.")
                        quota_errors += 1
                    else:
                        print(f"   ⚠ Could not generate embedding: {emb_error}")
                        # Continue without embedding
                
                new_faq = FAQ(
                    question=question,
                    answer=answer,
                    category=category,
                    embedding=embedding if embedding else None
                )
                
                db.add(new_faq)
                db.commit()
                added += 1
            
            # Progress indicator
            if i % 10 == 0:
                print(f"   Progress: {i}/{total} processed...")
        
        except Exception as e:
            error_msg = str(e)
            # Check for transaction errors and rollback
            if "InFailedSqlTransaction" in error_msg or "current transaction is aborted" in error_msg.lower():
                try:
                    db.rollback()
                    print(f"✗ [{i}/{total}] Transaction error, rolling back: {question[:50]}...")
                except:
                    pass
            else:
                print(f"✗ [{i}/{total}] Error processing '{question[:50]}...': {e}")
                try:
                    db.rollback()
                except:
                    pass
            errors += 1
            continue
    
    print("\n" + "="*60)
    print("📈 Migration Summary:")
    print(f"   ✓ Added: {added}")
    print(f"   ↻ Updated: {updated}")
    print(f"   ⊘ Skipped: {skipped}")
    print(f"   ⚠ Quota Errors (no embeddings): {quota_errors}")
    print(f"   ✗ Errors: {errors}")
    print(f"   📊 Total: {total}")
    if quota_errors > 0:
        print("\n⚠ Note: Some FAQs were saved without embeddings due to OpenAI quota limits.")
        print("   You can regenerate embeddings later by running: python scripts/migrate_faqs_to_db.py --force")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Migrate FAQs from JSON to database")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to FAQ JSON file (default: refined_faqs.json in project root)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update existing FAQs"
    )
    
    args = parser.parse_args()
    
    # Find FAQ JSON file
    if args.file:
        faq_file = args.file
    else:
        # Try to find in project root
        project_root = Path(__file__).parent.parent.parent
        possible_paths = [
            project_root / "refined_faqs.json",
            project_root / "faqs_final.json",
            Path(__file__).parent.parent / "refined_faqs.json",
        ]
        
        faq_file = None
        for path in possible_paths:
            if path.exists():
                faq_file = str(path)
                break
        
        if not faq_file:
            print("ERROR: FAQ JSON file not found.")
            print("Please specify --file path/to/faqs.json")
            sys.exit(1)
    
    print(f"📂 Loading FAQs from: {faq_file}")
    
    # Load FAQs
    try:
        faqs = load_faqs_from_json(faq_file)
        print(f"✓ Loaded {len(faqs)} FAQs from JSON")
    except Exception as e:
        print(f"ERROR loading FAQs: {e}")
        sys.exit(1)
    
    # Ensure database tables exist
    print("🗄️  Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables ready")
    
    # Migrate FAQs
    db = next(get_db())
    try:
        migrate_faqs(db, faqs, force=args.force)
    finally:
        db.close()
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()

