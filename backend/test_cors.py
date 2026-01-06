"""
Quick script to test if backend is running and CORS is configured
"""
import requests

def test_backend():
    try:
        # Test if backend is running
        response = requests.get("http://localhost:8000/")
        print("✅ Backend is running!")
        print(f"Response: {response.json()}")
        
        # Test CORS headers
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
        
        # Test OPTIONS request (preflight)
        options_response = requests.options("http://localhost:8000/auth/register", headers=headers)
        print(f"\n✅ OPTIONS Request Status: {options_response.status_code}")
        print(f"CORS Headers in response:")
        for key, value in options_response.headers.items():
            if 'access-control' in key.lower():
                print(f"  {key}: {value}")
        
        if 'access-control-allow-origin' in options_response.headers:
            print("\n✅ CORS is properly configured!")
        else:
            print("\n❌ CORS headers not found. Backend may need to be restarted.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is NOT running!")
        print("Please start it with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_backend()


