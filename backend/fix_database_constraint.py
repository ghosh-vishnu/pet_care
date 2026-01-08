"""
Script to fix the pet_id unique constraint issue
This removes the old unique constraint and adds a composite unique constraint
"""
from database import engine
from sqlalchemy import text

def fix_database():
    print("Fixing database constraint...")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Drop the old unique index if it exists
                print("1. Dropping old unique constraint on pet_id...")
                conn.execute(text("""
                    DROP INDEX IF EXISTS ix_pets_pet_id;
                """))
                
                # Create composite unique constraint
                print("2. Creating composite unique constraint on (user_id, pet_id)...")
                conn.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'uq_user_pet_id'
                        ) THEN
                            ALTER TABLE pets 
                            ADD CONSTRAINT uq_user_pet_id 
                            UNIQUE (user_id, pet_id);
                        END IF;
                    END $$;
                """))
                
                # Create index on pet_id for faster lookups
                print("3. Creating index on pet_id...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_pets_pet_id ON pets(pet_id);
                """))
                
                trans.commit()
                print("\n✅ Database constraint fixed successfully!")
                print("Now each user can have their own pet with the same pet_id.")
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ Error: {e}")
                raise
                
    except Exception as e:
        print(f"\n❌ Failed to fix database: {e}")
        print("\nYou may need to manually update the database:")
        print("1. Drop the unique constraint on pet_id")
        print("2. Add composite unique constraint on (user_id, pet_id)")

if __name__ == "__main__":
    fix_database()





