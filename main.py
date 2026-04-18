"""
FastAPI Backend: Smart Learning Notes Generator v4.0
Auth, daily limits (2 images/day), history, optimised API calls
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import base64
import hashlib
import httpx
import json
import logging
import os
import secrets
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
import PyPDF2

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Smart Learning Notes Generator", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Directories ───────────────────────────────────────────────────────────────

UPLOAD_DIR = Path(tempfile.gettempdir()) / "learning_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR = DATA_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
USAGE_FILE = DATA_DIR / "usage.json"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".pdf"}
MAX_FILE_SIZE = 25 * 1024 * 1024
DAILY_LIMIT = 2

# In-memory sessions: token -> username (cleared on restart)
active_sessions: dict[str, str] = {}

# Google OAuth config
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:5173")

_google_states: dict[str, bool] = {}  # state -> True (pending)


# ── User management ───────────────────────────────────────────────────────────

def load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return pw_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pw_hash, _ = hash_password(password, salt)
    return pw_hash == stored_hash


# ── Session management ────────────────────────────────────────────────────────

def create_session(username: str) -> str:
    token = secrets.token_hex(32)
    active_sessions[token] = username
    return token


def validate_token(token: str) -> str | None:
    return active_sessions.get(token)


# ── Daily usage tracking ──────────────────────────────────────────────────────

def get_daily_usage(username: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    if not USAGE_FILE.exists():
        return 0
    with open(USAGE_FILE) as f:
        usage = json.load(f)
    return usage.get(username, {}).get(today, 0)


def increment_daily_usage(username: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    usage = {}
    if USAGE_FILE.exists():
        with open(USAGE_FILE) as f:
            usage = json.load(f)
    usage.setdefault(username, {})[today] = usage.get(username, {}).get(today, 0) + 1
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)
    return usage[username][today]


# ── History ───────────────────────────────────────────────────────────────────

def save_to_history(username: str, entry: dict):
    history_file = HISTORY_DIR / f"{username}.json"
    history = []
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
    history.insert(0, entry)
    with open(history_file, "w") as f:
        json.dump(history[:50], f, indent=2)


def get_history(username: str) -> list:
    history_file = HISTORY_DIR / f"{username}.json"
    if history_file.exists():
        with open(history_file) as f:
            return json.load(f)
    return []


# ── Anthropic ─────────────────────────────────────────────────────────────────

def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)


# ── Content processing ────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        for page in PyPDF2.PdfReader(f).pages:
            text += page.extract_text() + "\n"
    return text.strip()


def extract_content_from_image(client, image_data: str, media_type: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": "Extract ALL written content, text, diagrams, formulas, and information from this image. Be thorough and preserve everything exactly as shown."}
            ],
        }],
    )
    return response.content[0].text.strip()


def generate_notes(client, content: str) -> dict:
    """Single API call — notes + key concepts together (optimised from 2 calls to 1)."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        temperature=0.7,
        system="""You are an expert educator creating student study notes.
Write comprehensive markdown notes: concept explanations, examples, formulas, definitions, diagrams where useful.
Adapt to the subject (sciences, engineering, humanities, languages, etc.) based on the input.

End your response with EXACTLY this section (no extra text after):
## KEY_CONCEPTS_LIST
- concept 1
- concept 2
(5-7 bullet points, very concise)""",
        messages=[{"role": "user", "content": f"Transform into structured study notes:\n\n{content}"}]
    )

    full_text = response.content[0].text.strip()
    if "## KEY_CONCEPTS_LIST" in full_text:
        notes, key_concepts = full_text.split("## KEY_CONCEPTS_LIST", 1)
        notes = notes.strip()
        key_concepts = key_concepts.strip()
    else:
        notes = full_text
        key_concepts = ""

    return {"success": True, "notes": notes, "key_concepts": key_concepts, "study_type": "Study Notes"}


def generate_competitive_exam_flashcards(client, content: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        temperature=0.5,
        system="""You are an exam preparation specialist. Create flashcards in this EXACT format:
Q: [question]
A: [answer, 1-3 sentences]
---
Arrange from basic to advanced. Focus on definitions, facts, quick recall.""",
        messages=[{"role": "user", "content": f"Create 8-12 flashcards from this content:\n\n{content}\n\nFormat each as Q: ... A: ... separated by ---"}]
    )

    flashcards_text = response.content[0].text.strip()
    flashcards = []
    for card in flashcards_text.split("---"):
        if "Q:" in card and "A:" in card:
            parts = card.split("\nA:")
            if len(parts) == 2:
                q = parts[0].replace("Q:", "").strip()
                a = parts[1].strip()
                if q and a:
                    flashcards.append({"question": q, "answer": a})

    return {"success": True, "flashcards": flashcards, "count": len(flashcards)}


def get_media_type(extension: str) -> str:
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "bmp": "image/bmp", "gif": "image/gif"}.get(extension, "image/jpeg")


def process_file(client, file_extension: str, temp_file_path: Path) -> str:
    if file_extension == ".pdf":
        return extract_text_from_pdf(str(temp_file_path))
    with open(temp_file_path, "rb") as img_file:
        image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
    return extract_content_from_image(client, image_data, get_media_type(file_extension.lstrip(".")))


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats():
    return {"version": "4.0.0"}


@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    users = load_users()
    if username in users:
        raise HTTPException(400, "Username already taken")

    pw_hash, salt = hash_password(password)
    users[username] = {"password_hash": pw_hash, "salt": salt, "created_at": datetime.now().isoformat()}
    save_users(users)
    logging.info(f"Registered: {username}")
    return {"success": True, "message": "Account created"}


@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    users = load_users()
    user = users.get(username)
    if not user or not verify_password(password, user["password_hash"], user["salt"]):
        raise HTTPException(401, "Invalid username or password")

    token = create_session(username)
    logging.info(f"Login: {username}")
    return {
        "success": True, "token": token, "username": username,
        "daily_used": get_daily_usage(username), "daily_limit": DAILY_LIMIT
    }


@app.post("/api/logout")
async def logout(request: Request):
    data = await request.json()
    active_sessions.pop(data.get("token"), None)
    return {"success": True}


@app.get("/api/usage")
async def get_usage(token: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    return {"username": username, "daily_used": get_daily_usage(username), "daily_limit": DAILY_LIMIT}


@app.get("/api/history")
async def get_user_history(token: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    return {"history": get_history(username)}


@app.get("/api/google-oauth-enabled")
async def google_oauth_enabled():
    return {"enabled": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)}


@app.get("/auth/google")
async def google_login():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        raise HTTPException(400, "Google OAuth not configured — add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env")
    state = secrets.token_hex(16)
    _google_states[state] = True
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/auth/google/callback")
async def google_callback(code: str = None, state: str = None, error: str = None):
    if error:
        return RedirectResponse(f"{FRONTEND_URL}/?auth_error={error}")
    if not code or not state or state not in _google_states:
        return RedirectResponse(f"{FRONTEND_URL}/?auth_error=invalid_state")
    del _google_states[state]

    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()
        if "error" in token_data:
            logging.error(f"Google token exchange error: {token_data}")
            return RedirectResponse(f"{FRONTEND_URL}/?auth_error=token_exchange_failed")

        profile_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        profile = profile_resp.json()

    email = profile.get("email", "")
    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/?auth_error=no_email")

    username = "g_" + email.split("@")[0].lower().replace(".", "_").replace("+", "_")[:24]

    users = load_users()
    if username not in users:
        users[username] = {
            "password_hash": None, "salt": None,
            "created_at": datetime.now().isoformat(),
            "email": email, "display_name": profile.get("name", ""),
            "auth": "google",
        }
        save_users(users)
        logging.info(f"Google OAuth new user: {username} ({email})")

    token = create_session(username)
    logging.info(f"Google OAuth login: {username}")
    return RedirectResponse(f"{FRONTEND_URL}/?{urlencode({'token': token, 'username': username})}")


@app.post("/api/rename-history")
async def rename_history(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")

    entry_id = data.get("entry_id", "")
    name = data.get("name", "").strip()

    history_file = HISTORY_DIR / f"{username}.json"
    if not history_file.exists():
        raise HTTPException(404, "No history found")

    with open(history_file) as f:
        history = json.load(f)

    for entry in history:
        if entry["id"] == entry_id:
            entry["name"] = name
            break
    else:
        raise HTTPException(404, "Entry not found")

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return {"success": True}


# ── Processing routes ─────────────────────────────────────────────────────────

def validate_upload(file_extension: str, contents: bytes):
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 25MB)")
    if len(contents) == 0:
        raise HTTPException(400, "Empty file")


@app.post("/api/generate-notes")
async def generate_notes_endpoint(file: UploadFile = File(...), token: str = Form(...), name: str = Form("")):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Please login first")
    if get_daily_usage(username) >= DAILY_LIMIT:
        raise HTTPException(429, f"Daily limit of {DAILY_LIMIT} images reached. Try again tomorrow.")

    try:
        file_extension = Path(file.filename).suffix.lower()
        contents = await file.read()
        validate_upload(file_extension, contents)

        temp_path = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}_{file.filename}"
        temp_path.write_bytes(contents)

        try:
            client = get_anthropic_client()
            extracted = process_file(client, file_extension, temp_path)
            if not extracted:
                return JSONResponse(status_code=400, content={"success": False, "error": "No content extracted"})

            result = generate_notes(client, extracted)
            result["filename"] = file.filename
            result["daily_used"] = increment_daily_usage(username)
            result["daily_limit"] = DAILY_LIMIT

            save_to_history(username, {
                "id": str(uuid.uuid4()), "type": "notes",
                "filename": file.filename, "name": name.strip() or file.filename,
                "created_at": datetime.now().isoformat(),
                "notes": result["notes"], "key_concepts": result["key_concepts"]
            })
            logging.info(f"Notes: {username} / {file.filename}")
            return result

        finally:
            temp_path.unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error in generate-notes for {username}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/generate-competitive-flashcards")
async def generate_competitive_flashcards_endpoint(file: UploadFile = File(...), token: str = Form(...), name: str = Form("")):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Please login first")
    if get_daily_usage(username) >= DAILY_LIMIT:
        raise HTTPException(429, f"Daily limit of {DAILY_LIMIT} images reached. Try again tomorrow.")

    try:
        file_extension = Path(file.filename).suffix.lower()
        contents = await file.read()
        validate_upload(file_extension, contents)

        temp_path = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}_{file.filename}"
        temp_path.write_bytes(contents)

        try:
            client = get_anthropic_client()
            extracted = process_file(client, file_extension, temp_path)
            if not extracted:
                return JSONResponse(status_code=400, content={"success": False, "error": "No content extracted"})

            result = generate_competitive_exam_flashcards(client, extracted)
            result["filename"] = file.filename
            result["daily_used"] = increment_daily_usage(username)
            result["daily_limit"] = DAILY_LIMIT

            save_to_history(username, {
                "id": str(uuid.uuid4()), "type": "competitive_flashcards",
                "filename": file.filename, "name": name.strip() or file.filename,
                "created_at": datetime.now().isoformat(),
                "flashcards": result["flashcards"]
            })
            logging.info(f"Flashcards: {username} / {file.filename}")
            return result

        finally:
            temp_path.unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Error in generate-competitive-flashcards for {username}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
