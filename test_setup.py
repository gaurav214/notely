"""
Test Script: Verify all dependencies and configuration
Run this to check if everything is set up correctly before starting the app
"""

import sys
import os
from pathlib import Path

def print_status(item, success, details=""):
    """Print formatted status message"""
    status = "✅" if success else "❌"
    print(f"{status} {item:<40} {details}")
    return success

def test_python_version():
    """Check Python version"""
    version = sys.version_info
    success = version.major >= 3 and version.minor >= 8
    print_status("Python Version", success, f"({version.major}.{version.minor}.{version.micro})")
    return success

def test_imports():
    """Check if all required packages are installed"""
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'streamlit': 'Streamlit',
        'pytesseract': 'Tesseract',
        'PIL': 'Pillow',
        'requests': 'Requests',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'dotenv': 'Python-dotenv'
    }
    
    results = {}
    print("\nChecking Python packages:")
    for module, name in packages.items():
        try:
            __import__(module)
            results[module] = True
            print_status(f"  {name}", True)
        except ImportError:
            results[module] = False
            print_status(f"  {name}", False, "(Run: pip install -r requirements.txt)")
    
    return all(results.values())

def test_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        import pytesseract
        from pathlib import Path
        import subprocess
        
        # Try to detect tesseract
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                   capture_output=True, text=True, timeout=5)
            success = result.returncode == 0
            version_info = result.stdout.split('\n')[0] if success else ""
            print_status("Tesseract OCR", success, version_info)
            return success
        except FileNotFoundError:
            print_status("Tesseract OCR", False, "Not found in PATH")
            return False
    except Exception as e:
        print_status("Tesseract OCR", False, f"Error: {str(e)}")
        return False

def test_environment_vars():
    """Check environment variables"""
    print("\nChecking environment variables:")
    
    api_key = os.getenv("GROQ_API_KEY")
    has_api_key = bool(api_key)
    print_status("  GROQ_API_KEY", has_api_key, 
                "Set" if has_api_key else "(Set GROQ_API_KEY environment variable)")
    
    # Also check .env file
    env_file = Path(".env")
    has_env_file = env_file.exists()
    print_status("  .env file", has_env_file, 
                "Found" if has_env_file else "(Create from .env.example)")
    
    return has_api_key or has_env_file

def test_file_structure():
    """Check if all necessary files exist"""
    print("\nChecking project files:")
    
    required_files = {
        'main.py': 'FastAPI Backend',
        'ocr.py': 'OCR Module',
        'llm.py': 'LLM Integration',
        'frontend.py': 'Streamlit Frontend',
        'requirements.txt': 'Dependencies',
        'README.md': 'Documentation'
    }
    
    results = {}
    for filename, description in required_files.items():
        filepath = Path(filename)
        exists = filepath.exists()
        results[filename] = exists
        print_status(f"  {description:<30}", exists, filename)
    
    return all(results.values())

def test_api_connection():
    """Test if FastAPI backend is running"""
    print("\nChecking API connectivity:")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        success = response.status_code == 200
        print_status("  Backend API", success, "Running on port 8000")
        return True
    except requests.exceptions.ConnectionError:
        print_status("  Backend API", False, "Not running (Start with: python main.py)")
        return False
    except Exception as e:
        print_status("  Backend API", False, f"Error: {str(e)}")
        return False

def test_groq_api():
    """Test Groq API key and connectivity"""
    print("\nChecking Groq API:")
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        # Try loading from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
        except:
            pass
    
    has_key = bool(api_key)
    print_status("  API Key configured", has_key, 
                "Set in environment" if has_key else "Missing")
    
    if has_key:
        try:
            import requests
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "llama3-8b-8192", "messages": []},
                timeout=5
            )
            # Check for auth error vs other errors
            if response.status_code == 401:
                print_status("  API Authentication", False, "Invalid or expired key")
                return False
            elif response.status_code in [200, 400, 422]:
                print_status("  API Connectivity", True, "Connected to Groq")
                return True
            else:
                print_status("  API Connectivity", False, f"Response: {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            print_status("  API Connectivity", False, "Request timed out")
            return False
        except Exception as e:
            print_status("  API Connectivity", False, f"Error: {str(e)}")
            return False
    else:
        print("  ⓘ Cannot test API without key")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Blackboard Notes Generator - System Check")
    print("=" * 70)
    print()
    
    results = {
        "Python Version": test_python_version(),
        "Python Packages": test_imports(),
        "Tesseract OCR": test_tesseract(),
        "File Structure": test_file_structure(),
        "Environment Variables": test_environment_vars(),
    }
    
    # Optional tests
    api_running = test_api_connection()
    groq_ready = test_groq_api()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    critical_pass = all(results.values())
    
    if critical_pass:
        print("\n✅ All critical checks passed!")
        print("\nNext steps:")
        print("1. Make sure FastAPI backend is running: python main.py")
        print("2. Start Streamlit frontend: streamlit run frontend.py")
        print("3. Open browser to: http://localhost:8501")
    else:
        print("\n❌ Some checks failed. See above for details.")
        print("\nFix the following:")
        for check, passed in results.items():
            if not passed:
                print(f"  - {check}")
    
    if not api_running:
        print("\nℹ️  Backend API not running (this is normal if just starting)")
        print("   Start it with: python main.py")
    
    print("\n" + "=" * 70)
    
    return 0 if critical_pass else 1

if __name__ == "__main__":
    sys.exit(main())
