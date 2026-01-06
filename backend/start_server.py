#!/usr/bin/env python
"""
Simple Python script to start the FastAPI server with uvicorn
This script ensures the virtual environment and dependencies are available
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    print("=" * 50)
    print("Starting Dog Health AI Backend Server...")
    print("=" * 50)
    print()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if uvicorn is available
    try:
        import uvicorn
        print("✅ uvicorn is available")
    except ImportError:
        print("❌ uvicorn not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
        print("✅ uvicorn installed successfully")
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ ERROR: main.py not found!")
        print(f"   Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("Starting server on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    print()
    
    # Start uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["."]
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



