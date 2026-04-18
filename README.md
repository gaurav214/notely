# 📚 Blackboard Notes Generator - MVP

A lightweight, free web application that converts blackboard photos into clean, structured study notes using OCR and AI.

## Features

✅ **Image Upload**: Upload photos of blackboards or handwritten notes  
✅ **OCR Extraction**: Extract text using Tesseract OCR with image preprocessing  
✅ **AI Processing**: Use Groq's free API to generate structured notes  
✅ **Multiple Outputs**:
  - Raw extracted text
  - Cleaned, structured notes with headings and bullet points
  - 5-7 line summary
✅ **User-Friendly UI**: Simple Streamlit interface  
✅ **Completely Free**: No paid services required  
✅ **Error Handling**: Graceful error handling for failures  

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **OCR**: Tesseract OCR + pytesseract
- **LLM**: Groq API (free tier, no credit card required)
- **Image Processing**: OpenCV, Pillow

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Internet connection (for Groq API)
- ~500MB disk space

## Installation & Setup

### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd blackboard-notes

# Create virtual environment (optional but recommended)
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR

**Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Download: `tesseract-ocr-w64-setup-v5.x.x.exe`
3. Run the installer and follow the default installation path
4. Add Tesseract to PATH or configure in code:
   ```python
   # Add this line at the top of ocr.py if needed
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

### Step 3: Get Groq API Key (Free)

1. Visit: https://console.groq.com/keys
2. Sign up for a free account (no credit card required)
3. Create a new API key
4. Copy the key

### Step 4: Set Environment Variable

**Windows (Command Prompt):**
```cmd
set GROQ_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

**macOS/Linux:**
```bash
export GROQ_API_KEY="your_api_key_here"
```

**Alternative: Create `.env` file**

Create a file named `.env` in the project root:
```
GROQ_API_KEY=your_api_key_here
```

### Step 5: Run the Application

**Terminal 1 - Start FastAPI Backend:**
```bash
# Make sure virtual environment is activated
python main.py
# or
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Start Streamlit Frontend:**
```bash
# Make sure virtual environment is activated
streamlit run frontend.py
```

You should see:
```
Local URL: http://localhost:8501
```

### Step 6: Access the Application

Open your browser and go to: **http://localhost:8501**

## Usage

1. **Upload Image**: Click the uploader and select a blackboard photo
2. **Preview**: See the uploaded image in the sidebar
3. **Process**: Click "🚀 Process Image" button
4. **Wait**: Processing takes 20-30 seconds
5. **View Results**:
   - **Cleaned Notes**: Structured Markdown format
   - **Summary**: 5-7 line concise summary
   - **Raw Text**: Original OCR output for reference
6. **Download**: Save notes, summary, or combined file as text/markdown

## Project Structure

```
blackboard-notes/
├── main.py              # FastAPI backend server
├── ocr.py               # OCR text extraction module
├── llm.py               # Groq API integration module
├── frontend.py          # Streamlit UI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create manually)
└── README.md           # This file
```

## File Descriptions

### main.py
- FastAPI server with endpoints for image processing
- Handles file uploads and image validation
- Coordinates OCR and LLM processing
- Implements error handling and CORS support

### ocr.py
- Tesseract OCR integration
- Image preprocessing (grayscale, thresholding, denoising)
- Text extraction with error handling

### llm.py
- Groq API integration
- Prompt engineering for note formatting
- Response parsing and summary extraction

### frontend.py
- Streamlit web interface
- File upload and preview
- Results display with tabbed interface
- Download options for notes and summaries

## API Endpoints

### Health Check
```
GET /health
```
Returns: `{"status": "healthy"}`

### Process Image
```
POST /api/process-image
Content-Type: multipart/form-data

Request: File upload
Response:
{
  "success": true,
  "raw_text": "...",
  "cleaned_notes": "...",
  "summary": "...",
  "filename": "image.jpg"
}
```

### Test OCR Only
```
POST /api/test-ocr
Content-Type: multipart/form-data

Request: File upload
Response:
{
  "success": true,
  "raw_text": "..."
}
```

## Troubleshooting

### "Tesseract not found" error
- **Solution**: Install Tesseract OCR (see Step 2)
- **Windows**: Verify installation path and add to system PATH
- **Or**: Modify `ocr.py` and add the pytesseract command path

### "GROQ_API_KEY not set" error
- **Solution**: Set environment variable (see Step 4)
- **Check**: 
  - Windows: `echo %GROQ_API_KEY%`
  - macOS/Linux: `echo $GROQ_API_KEY`

### Backend not responding
- **Check**: Is FastAPI server running? (Terminal should show `Uvicorn running on...`)
- **Solution**: Start backend with `python main.py`

### Image processing slow
- **Normal**: First request takes 30-60 seconds
- **Subsequent**: Usually 20-30 seconds
- **Reason**: Groq API initialization and LLM processing
- **Solution**: Be patient, server will respond

### Poor OCR Quality
- **Cause**: Low resolution or poor lighting in photo
- **Solution**:
  1. Take clearer photos with good lighting
  2. Use straight angle (not skewed)
  3. Minimize shadows and reflections
  4. Use test endpoint to check raw text quality

### Image upload fails
- **Check**: Is image format supported? (JPG, PNG, BMP, GIF)
- **Check**: Is file size under 10MB?
- **Solution**: Retry with different image or smaller file

## Tips for Best Results

1. **Photo Quality**
   - Use a smartphone camera with good lighting
   - Take photo from directly above the board
   - Avoid shadows and reflections
   - Ensure text is clearly visible

2. **Content Quality**
   - Legible handwriting or printed text
   - Even if handwriting is messy, OCR will try its best
   - Clear board background (white/light colored preferred)

3. **Large Documents**
   - Upload blackboard sections one at a time
   - Divide long content into multiple photos
   - Process separately to avoid token limits

## Performance

- **OCR Processing**: 5-10 seconds
- **LLM Processing**: 15-25 seconds
- **Total Time**: 20-35 seconds per image
- **Network**: Requires stable internet for Groq API

## Limitations

- File size limited to 10MB
- Groq API free tier has rate limits (depends on free plan)
- Tesseract OCR quality depends on photo clarity
- LLM processing limited by model token availability

## Future Enhancements

- Batch processing multiple images
- Custom prompt templates
- LaTeX formula recognition
- Diagram extraction
- Multi-language support
- Export to PDF format
- Cloud deployment

## License

This project is free to use and modify for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify Tesseract and Groq API are properly configured
3. Check API response in terminal output

## Credits

- **FastAPI**: Modern web framework
- **Streamlit**: Rapid UI development
- **Tesseract OCR**: Open-source text extraction
- **Groq API**: Fast, free LLM access
- **OpenCV & Pillow**: Image processing

---

**Happy note-taking! 📚✨**
