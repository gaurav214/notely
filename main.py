"""
Notely Backend v5.0
Supabase (Postgres) for persistent storage — users, history, usage, feedback.
"""

from contextlib import contextmanager
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
import psycopg2
import psycopg2.extras
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

app = FastAPI(title="Notely", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ─────────────────────────────────────────────────────────────────────

UPLOAD_DIR = Path(tempfile.gettempdir()) / "notely_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".pdf"}
MAX_FILE_SIZE = 25 * 1024 * 1024
DAILY_LIMIT = 10

DATABASE_URL          = os.getenv("DATABASE_URL", "")
GOOGLE_CLIENT_ID      = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET  = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI   = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL          = os.getenv("FRONTEND_URL", "http://localhost:5175")

# In-memory sessions (token → username). Cleared on restart — acceptable.
active_sessions: dict[str, str] = {}
_google_states:  dict[str, bool] = {}
_reset_tokens:   dict[str, dict] = {}   # token → {username, expires}
_reg_attempts:   dict[str, list] = {}   # ip → [timestamps]


# ── Database ───────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username        TEXT PRIMARY KEY,
                password_hash   TEXT,
                salt            TEXT,
                email           TEXT,
                display_name    TEXT,
                auth            TEXT DEFAULT 'email',
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS daily_usage (
                username TEXT NOT NULL,
                date     TEXT NOT NULL,
                count    INTEGER DEFAULT 0,
                PRIMARY KEY (username, date)
            );

            CREATE TABLE IF NOT EXISTS history (
                id           TEXT PRIMARY KEY,
                username     TEXT NOT NULL,
                type         TEXT NOT NULL,
                filename     TEXT,
                name         TEXT,
                notes        TEXT,
                key_concepts TEXT,
                flashcards   JSONB,
                created_at   TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id         TEXT PRIMARY KEY,
                username   TEXT NOT NULL,
                options    JSONB,
                message    TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    logging.info("Database tables ready.")


# ── User management ────────────────────────────────────────────────────────────

def user_exists(username: str) -> bool:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        return cur.fetchone() is not None


def get_user(username: str) -> dict | None:
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str | None, salt: str | None,
                email: str = "", display_name: str = "", auth: str = "email"):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password_hash, salt, email, display_name, auth)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (username, password_hash, salt, email, display_name, auth))


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return pw_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pw_hash, _ = hash_password(password, salt)
    return pw_hash == stored_hash


# ── Session management ─────────────────────────────────────────────────────────

def create_session(username: str) -> str:
    token = secrets.token_hex(32)
    active_sessions[token] = username
    return token


def validate_token(token: str) -> str | None:
    return active_sessions.get(token)


# ── Daily usage ────────────────────────────────────────────────────────────────

def get_daily_usage(username: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count FROM daily_usage WHERE username = %s AND date = %s", (username, today))
        row = cur.fetchone()
        return row[0] if row else 0


def increment_daily_usage(username: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO daily_usage (username, date, count) VALUES (%s, %s, 1)
            ON CONFLICT (username, date) DO UPDATE SET count = daily_usage.count + 1
            RETURNING count
        """, (username, today))
        return cur.fetchone()[0]


# ── History ────────────────────────────────────────────────────────────────────

def save_to_history(username: str, entry: dict):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO history (id, username, type, filename, name, notes, key_concepts, flashcards, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            entry["id"], username, entry["type"],
            entry.get("filename"), entry.get("name"),
            entry.get("notes"), entry.get("key_concepts"),
            json.dumps(entry["flashcards"]) if entry.get("flashcards") else None,
            entry.get("created_at", datetime.now().isoformat()),
        ))


def get_history(username: str) -> list:
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, type, filename, name, notes, key_concepts, flashcards,
                   created_at AT TIME ZONE 'UTC' AS created_at
            FROM history WHERE username = %s
            ORDER BY created_at DESC LIMIT 50
        """, (username,))
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["created_at"] = d["created_at"].isoformat() if d["created_at"] else ""
            if d["flashcards"] is None:
                d["flashcards"] = None
            result.append(d)
        return result


# ── Anthropic ──────────────────────────────────────────────────────────────────

def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)


# ── File processing ────────────────────────────────────────────────────────────

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
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        temperature=0.7,
        system="""You are an expert educator creating student study notes.
Write comprehensive markdown notes: concept explanations, examples, formulas, definitions.
Use LaTeX math notation: inline with $...$ and display with $$...$$
Adapt to the subject (sciences, engineering, humanities, languages) based on the input.

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


# ── Startup ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    if DATABASE_URL:
        try:
            init_db()
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            logging.warning("Server starting without database — check DATABASE_URL")
    else:
        logging.warning("DATABASE_URL not set — database features disabled")


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats():
    return {"version": "5.0.0"}


@app.post("/api/register")
async def register(request: Request):
    import time
    data = await request.json()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    # Rate limit: max 3 registrations per IP per hour
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in _reg_attempts.get(ip, []) if now - t < 3600]
    if len(attempts) >= 3:
        raise HTTPException(429, "Too many accounts created. Try again later.")
    _reg_attempts[ip] = attempts + [now]

    if len(username) < 3:
        raise HTTPException(400, "Email too short")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if user_exists(username):
        raise HTTPException(400, "Account already exists")

    pw_hash, salt = hash_password(password)
    create_user(username, pw_hash, salt, email=username)
    logging.info(f"Registered: {username}")
    return {"success": True, "message": "Account created"}


@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    user = get_user(username)
    if not user or not user.get("password_hash") or not verify_password(password, user["password_hash"], user["salt"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_session(username)
    logging.info(f"Login: {username}")
    return {
        "success": True, "token": token, "username": username,
        "display_name": user.get("display_name") or "",
        "daily_used": get_daily_usage(username), "daily_limit": DAILY_LIMIT
    }


@app.post("/api/logout")
async def logout(request: Request):
    data = await request.json()
    active_sessions.pop(data.get("token"), None)
    return {"success": True}


@app.post("/api/forgot-password")
async def forgot_password(request: Request):
    import smtplib, time
    from email.mime.text import MIMEText
    data = await request.json()
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "Email required")
    user = get_user(email)
    # Always return success to avoid user enumeration
    if user and user.get("password_hash"):
        token = secrets.token_urlsafe(32)
        _reset_tokens[token] = {"username": email, "expires": time.time() + 3600}
        reset_url = f"{FRONTEND_URL}?reset_token={token}"
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")
        if smtp_user and smtp_pass:
            try:
                msg = MIMEText(f"Hi,\n\nClick the link below to reset your Notely password (expires in 1 hour):\n\n{reset_url}\n\nIf you didn't request this, ignore this email.")
                msg["Subject"] = "Reset your Notely password"
                msg["From"] = smtp_user
                msg["To"] = email
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                    s.login(smtp_user, smtp_pass)
                    s.send_message(msg)
                logging.info(f"Password reset email sent to {email}")
            except Exception as e:
                logging.warning(f"Reset email failed: {e}")
    return {"success": True, "message": "If that email exists, a reset link has been sent."}


@app.post("/api/reset-password")
async def reset_password(request: Request):
    import time
    data = await request.json()
    token = data.get("token", "")
    new_password = data.get("password", "")
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    entry = _reset_tokens.get(token)
    if not entry or time.time() > entry["expires"]:
        raise HTTPException(400, "Reset link is invalid or expired")
    pw_hash, salt = hash_password(new_password)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash=%s, salt=%s WHERE username=%s",
                    (pw_hash, salt, entry["username"]))
    _reset_tokens.pop(token, None)
    return {"success": True}


@app.post("/api/change-password")
async def change_password(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    current = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user = get_user(username)
    if not user or not verify_password(current, user["password_hash"], user["salt"]):
        raise HTTPException(400, "Current password is incorrect")
    pw_hash, salt = hash_password(new_pw)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash=%s, salt=%s WHERE username=%s",
                    (pw_hash, salt, username))
    return {"success": True}


@app.post("/api/update-email")
async def update_email(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    new_email = data.get("email", "").strip().lower()
    if not new_email or "@" not in new_email:
        raise HTTPException(400, "Valid email required")
    if new_email == username:
        return {"success": True}  # no change
    if user_exists(new_email):
        raise HTTPException(400, "An account with this email already exists")
    with get_db() as conn:
        cur = conn.cursor()
        # Update username (login credential), email field, and migrate all user data
        cur.execute("UPDATE history SET username=%s WHERE username=%s", (new_email, username))
        cur.execute("UPDATE daily_usage SET username=%s WHERE username=%s", (new_email, username))
        cur.execute("UPDATE feedback SET username=%s WHERE username=%s", (new_email, username))
        cur.execute("UPDATE users SET username=%s, email=%s WHERE username=%s", (new_email, new_email, username))
    # Update session to use new username
    for token, u in list(active_sessions.items()):
        if u == username:
            active_sessions[token] = new_email
    logging.info(f"Email changed: {username} → {new_email}")
    return {"success": True, "new_username": new_email}


@app.delete("/api/delete-account")
async def delete_account(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    password = data.get("password", "")
    user = get_user(username)
    if not user or not verify_password(password, user["password_hash"], user["salt"]):
        raise HTTPException(400, "Incorrect password")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM history WHERE username=%s", (username,))
        cur.execute("DELETE FROM daily_usage WHERE username=%s", (username,))
        cur.execute("DELETE FROM feedback WHERE username=%s", (username,))
        cur.execute("DELETE FROM users WHERE username=%s", (username,))
    active_sessions.pop(data.get("token"), None)
    logging.info(f"Account deleted: {username}")
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


@app.post("/api/feedback")
async def submit_feedback(request: Request):
    import smtplib
    from email.mime.text import MIMEText

    data = await request.json()
    token = data.get("token", "")
    username = validate_token(token) or "anonymous"
    options = data.get("options", [])
    message = data.get("message", "")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO feedback (id, username, options, message) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), username, json.dumps(options), message)
        )

    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    notify_email = os.getenv("NOTIFY_EMAIL", "frakz321@gmail.com")
    if smtp_user and smtp_pass:
        try:
            body = f"From: {username}\n\nSelected:\n" + "\n".join(f"  • {o}" for o in options)
            if message:
                body += f"\n\nMessage:\n{message}"
            msg = MIMEText(body)
            msg["Subject"] = f"[Notely Feedback] {', '.join(options) or 'Message only'}"
            msg["From"] = smtp_user
            msg["To"] = notify_email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            logging.info(f"Feedback email sent for {username}")
        except Exception as e:
            logging.warning(f"Feedback email failed: {e}")

    logging.info(f"Feedback from {username}: {options}")
    return {"success": True}


@app.get("/auth/google")
async def google_login():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        raise HTTPException(400, "Google OAuth not configured")
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
            "code": code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI, "grant_type": "authorization_code",
        })
        token_data = token_resp.json()
        if "error" in token_data:
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
    if not user_exists(username):
        create_user(username, None, None,
                    email=email, display_name=profile.get("name", ""), auth="google")
        logging.info(f"Google OAuth new user: {username} ({email})")

    token = create_session(username)
    logging.info(f"Google OAuth login: {username}")
    return RedirectResponse(f"{FRONTEND_URL}/?{urlencode({'token': token, 'username': username})}")


@app.post("/api/rename-history")
async def rename_history_entry(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    entry_id = data.get("id") or data.get("entry_id", "")
    name = data.get("name", "").strip()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE history SET name = %s WHERE id = %s AND username = %s",
                    (name, entry_id, username))
        if cur.rowcount == 0:
            raise HTTPException(404, "Entry not found")
    return {"success": True}


@app.post("/api/update-display-name")
async def update_display_name(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    name = data.get("display_name", "").strip()
    if not name:
        raise HTTPException(400, "Name cannot be empty")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET display_name = %s WHERE username = %s", (name, username))
    return {"success": True, "display_name": name}


# ── Processing routes ──────────────────────────────────────────────────────────

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
        raise HTTPException(429, f"Daily limit of {DAILY_LIMIT} reached. Try again tomorrow.")

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
        raise HTTPException(429, f"Daily limit of {DAILY_LIMIT} reached. Try again tomorrow.")

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
        logging.exception(f"Error in generate-flashcards for {username}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
