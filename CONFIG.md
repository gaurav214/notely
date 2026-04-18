"""
Configuration & Customization Guide
Modify these settings to customize the application
"""

# ============================================================================
# BACKEND CONFIGURATION (main.py)
# ============================================================================

# Server settings
API_HOST = "0.0.0.0"  # Listen on all interfaces
API_PORT = 8000       # Backend API port
API_RELOAD = True     # Auto-reload on file changes (dev only)

# File upload settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB max file size
UPLOAD_DIR = "temp_uploads"       # Temporary upload directory
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

# CORS settings (allow frontend domains)
CORS_ORIGINS = ["*"]  # Allow all origins (change to specific domains in production)


# ============================================================================
# OCR CONFIGURATION (ocr.py)  
# ============================================================================

# Image preprocessing
PREPROCESS_ENABLED = True  # Enable image preprocessing
THRESHOLD_VALUE = 150      # Binary threshold value (0-255)
DENOISE_STRENGTH = 10      # Denoising strength (higher = more denoising)

# Tesseract configuration
TESSERACT_PATH = None  # Set if not in system PATH
                       # Windows: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                       # macOS: '/usr/local/bin/tesseract'
                       # Linux: '/usr/bin/tesseract'


# ============================================================================
# LLM CONFIGURATION (llm.py)
# ============================================================================

# Groq API settings
GROQ_API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"  # Fast and free model

# Alternative models (commented out):
# GROQ_MODEL = "mixtral-8x7b-32768"    # Larger, more capable
# GROQ_MODEL = "gemma-7b-it"           # Smaller, faster

# Request settings
TEMPERATURE = 0.7           # 0.0-1.0 (lower = more focused, higher = more creative)
MAX_TOKENS = 2000          # Maximum response length
REQUEST_TIMEOUT = 30       # Seconds to wait for API response

# Note: You can adjust TEMPERATURE for different styles:
# 0.3-0.5 = Very focused, structured notes
# 0.7     = Balanced (recommended)
# 0.9+    = More creative, verbose explanations


# ============================================================================
# FRONTEND CONFIGURATION (frontend.py)
# ============================================================================

# Streamlit settings
STREAMLIT_HOST = "localhost"
STREAMLIT_PORT = 8501
STREAMLIT_THEME = "light"  # "light" or "dark"

# UI settings
MAX_IMAGE_WIDTH = 600  # Display width in pixels
SHOW_RAW_TEXT_BY_DEFAULT = False  # Show raw OCR text tab by default
ENABLE_DOWNLOAD_BUTTONS = True    # Show download options

# API settings
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 60  # Seconds to wait for API response


# ============================================================================
# SYSTEM INTEGRATION
# ============================================================================

# Environment variables to set
REQUIRED_ENV_VARS = {
    "GROQ_API_KEY": "Your Groq API key (get from: https://console.groq.com/keys)"
}

OPTIONAL_ENV_VARS = {
    "TESSERACT_PATH": "Path to tesseract executable (if not in PATH)",
    "API_HOST": "Backend API host (default: 0.0.0.0)",
    "API_PORT": "Backend API port (default: 8000)"
}


# ============================================================================
# EXAMPLE: HOW TO CUSTOMIZE
# ============================================================================

"""
Example 1: Make OCR more aggressive for better quality
================================================
File: ocr.py

Change line:
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

To:
    _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)

Lower threshold value = more aggressive (good for light text on dark background)
Higher threshold value = less aggressive (good for dark text on light background)


Example 2: Use a different Groq model
================================================
File: llm.py

Change:
    GROQ_MODEL = "llama3-8b-8192"

To:
    GROQ_MODEL = "mixtral-8x7b-32768"

Models available:
- llama3-8b-8192 (8B, fast, recommended)
- mixtral-8x7b-32768 (56B, powerful, slower)
- gemma-7b-it (7B, small, very fast)


Example 3: Increase file upload limit
================================================
File: main.py

Change:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

To:
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


Example 4: Change API response timeout
================================================
File: llm.py

Change:
    REQUEST_TIMEOUT = 30

To:
    REQUEST_TIMEOUT = 60  # Longer timeout for slower API


Example 5: Customize the Note Format
================================================
File: llm.py

Modify the system_prompt variable in generate_notes_and_summary()

Current asks for:
- Markdown formatting
- Key concepts as bullet points
- Main content organized
- Definitions
- Summary

You can change it to ask for:
- Different format (PDF-friendly, HTML, etc.)
- Specific structure (outline, mind map, etc.)
- Different language
- Custom style
"""


# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

"""
For faster performance:
1. Use smaller Groq model (gemma-7b-it)
2. Reduce TEMPERATURE (0.3-0.5)
3. Reduce MAX_TOKENS (1000)
4. Disable image preprocessing

For better quality:
1. Use larger Groq model (mixtral-8x7b-32768)
2. Increase MAX_TOKENS (2500)
3. Enable image preprocessing
4. Use TEMPERATURE 0.7-0.8

For production use:
1. Add request rate limiting
2. Add authentication
3. Use HTTPS
4. Set specific CORS origins
5. Add logging and monitoring
6. Set API_RELOAD = False
"""


# ============================================================================
# DEBUGGING
# ============================================================================

"""
Enable debug logging:

1. In main.py, add:
    import logging
    logging.basicConfig(level=logging.DEBUG)

2. In ocr.py, add:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing image: {image_path}")

3. In llm.py, add:
    logger.debug(f"API request: {payload}")
    logger.debug(f"API response: {response_data}")

4. In frontend.py, add:
    st.write(f"Debug: {result}")
"""


# ============================================================================
# DEPLOYMENT OPTIONS
# ============================================================================

"""
Local deployment (current):
- Run on localhost
- Access via http://localhost:8501
- Only accessible from your machine

Docker deployment:
- Create Dockerfile
- Run in container
- Easier distribution

Cloud deployment:
- Deploy backend to AWS/Azure/Google Cloud
- Deploy frontend to Vercel/Netlify
- Global accessibility

Streamlit Cloud (frontend only):
- Push code to GitHub
- Deploy via https://streamlit.io/cloud
- Works with public/private backends
"""


# ============================================================================
# ENVIRONMENT SETUP EXAMPLES
# ============================================================================

"""
Create .env file with custom config:

# Basic setup
GROQ_API_KEY=sk_live_xxx...

# With Tesseract path
GROQ_API_KEY=sk_live_xxx...
TESSERACT_PATH=/usr/local/bin/tesseract

# Full configuration
GROQ_API_KEY=sk_live_xxx...
TESSERACT_PATH=/usr/local/bin/tesseract
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=DEBUG
"""
