"""
Quick script to check if backend server is running and CORS is configured
"""
import requests
import sys

def check_backend():
    try:
        print("Checking if backend server is running...")
        print("=" * 50)
        
        # Test if backend is running
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✅ Backend is running!")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test CORS headers with preflight request
        print("\n" + "=" * 50)
        print("Testing CORS configuration...")
        
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
        
        # Test OPTIONS request (preflight)
        options_response = requests.options(
            "http://localhost:8000/auth/register", 
            headers=headers,
            timeout=5
        )
        
        print(f"OPTIONS Request Status: {options_response.status_code}")
        print("\nCORS Headers in response:")
        
        cors_headers_found = False
        for key, value in options_response.headers.items():
            if 'access-control' in key.lower():
                print(f"  ✅ {key}: {value}")
                cors_headers_found = True
        
        if not cors_headers_found:
            print("  ❌ No CORS headers found!")
            print("\n⚠️  WARNING: CORS headers not found.")
            print("   Make sure:")
            print("   1. Backend server was restarted after CORS changes")
            print("   2. CORS middleware is properly configured in main.py")
            return False
        
        print("\n✅ CORS is properly configured!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is NOT running!")
        print("\nPlease start the backend server:")
        print("  cd backend")
        print("  python start_server.py")
        print("  OR")
        print("  start_server.bat")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend server timeout - may not be responding")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_backend()
    sys.exit(0 if success else 1)


