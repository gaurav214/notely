# Quick Start Guide

## For the Impatient 🚀

### Windows Users:
1. **Install Tesseract OCR**
   - Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
   - Choose the default installation path

2. **Get Groq API Key**
   - Go to: https://console.groq.com/keys
   - Sign up (free, no credit card)
   - Create API key

3. **Setup Project**
   ```cmd
   cd blackboard-notes
   copy .env.example .env
   # Edit .env and paste your API key
   set GROQ_API_KEY=your_key_here
   start.bat
   ```

4. **Open Browser**
   - Go to: http://localhost:8501
   - Upload a blackboard photo
   - Done! 📸→📝

### macOS/Linux Users:
1. **Install Tesseract**
   ```bash
   # macOS
   brew install tesseract
   
   # Linux
   sudo apt-get install tesseract-ocr
   ```

2. **Get Groq API Key**
   - Go to: https://console.groq.com/keys
   - Sign up and create key

3. **Setup Project**
   ```bash
   cd blackboard-notes
   cp .env.example .env
   # Edit .env and paste your API key
   export GROQ_API_KEY="your_key_here"
   chmod +x start.sh
   ./start.sh
   ```

4. **Open Browser**
   - Go to: http://localhost:8501
   - Start uploading images!

---

## Verify Everything Works

Once the app starts, you should see:
```
Backend:  http://localhost:8000   ✅ FastAPI
Frontend: http://localhost:8501   ✅ Streamlit
```

Try the test endpoints:
```bash
# Check backend health
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

---

## Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'pytesseract'"
**Fix**: Run `pip install -r requirements.txt`

### Issue: "pytesseract.TesseractNotFoundError"
**Fix**: Install Tesseract OCR (see installation guides above)

### Issue: "GROQ_API_KEY not set"
**Fix**: 
- Check `.env` file exists
- Check API key is correct
- Restart the backend

### Issue: Backend not responding
**Fix**: 
- Check if `main.py` is running
- Check for port conflicts (8000)
- Try: `python main.py` directly

### Issue: Frontend can't connect to backend
**Fix**:
- Start backend FIRST
- Wait 3 seconds, then start frontend
- Check http://localhost:8000/health responds

---

## File Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI backend server |
| `ocr.py` | Text extraction from images |
| `llm.py` | Groq API integration |
| `frontend.py` | Streamlit web interface |
| `requirements.txt` | Python dependencies |
| `.env` | Your API key (create from .env.example) |
| `start.bat` | Windows quick start |
| `start.sh` | macOS/Linux quick start |

---

## What Happens When You Upload?

1. **Upload** 📸
   - File validated (type, size)
   - Saved temporarily

2. **Extract** 🔤
   - Image preprocessed (grayscale, threshold)
   - Tesseract extracts text (5-10 seconds)

3. **Process** 🤖
   - Text sent to Groq API
   - LLM fixes OCR errors
   - Creates structured notes (15-25 seconds)

4. **Display** 📋
   - Raw extracted text shown
   - Cleaned notes displayed
   - Summary generated

5. **Cleanup** 🗑️
   - Temporary files deleted
   - Ready for next image

---

## Free Tier Limits

- **Groq API**: Free tier typically allows:
  - ~14 requests/minute
  - 2000 tokens per request
  - No payment required

- **Tesseract OCR**: Completely free, open-source

- **Streamlit**: Free deployment available (not needed for local use)

---

## Tips for Success

✅ **DO:**
- Take clear photos with good lighting
- Hold camera straight (not angled)
- Use high resolution if possible
- Upload one board/section at a time
- Check raw text for OCR quality

❌ **DON'T:**
- Upload blurry photos
- Take photos at extreme angles
- Include shadows or reflections
- Upload non-image files
- Expect perfect OCR (it's AI-powered)

---

## Need Help?

1. Check the **README.md** for detailed documentation
2. See **troubleshooting** section in README
3. Check backend terminal for error messages
4. Verify Tesseract and Groq API setup

---

## Next Steps

Once it works:
- Try different types of content (math, programming, diagrams)
- Test image preprocessing quality
- Download and save your notes
- Integrate into your study workflow

Happy note-taking! 📚✨
