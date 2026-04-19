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

            CREATE TABLE IF NOT EXISTS card_reviews (
                id           TEXT PRIMARY KEY,
                username     TEXT NOT NULL,
                history_id   TEXT NOT NULL,
                card_index   INTEGER NOT NULL,
                interval     INTEGER DEFAULT 1,
                ease_factor  REAL DEFAULT 2.5,
                repetitions  INTEGER DEFAULT 0,
                next_review  TEXT NOT NULL,
                UNIQUE(username, history_id, card_index)
            );

            CREATE TABLE IF NOT EXISTS folders (
                id         TEXT PRIMARY KEY,
                username   TEXT NOT NULL,
                name       TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS folder_items (
                folder_id  TEXT NOT NULL,
                history_id TEXT NOT NULL,
                username   TEXT NOT NULL,
                added_at   TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (folder_id, history_id)
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


# ── Spaced Repetition (SM-2) ───────────────────────────────────────────────────

def sm2(repetitions: int, ease_factor: float, interval: int, quality: int) -> tuple:
    """SM-2 algorithm. quality: 1=Again, 4=Good, 5=Easy"""
    if quality < 3:
        new_reps = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
        new_reps = repetitions + 1
    new_ef = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return new_reps, new_ef, new_interval


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
        cur.execute("UPDATE folder_items SET username=%s WHERE username=%s", (new_email, username))
        cur.execute("UPDATE folders SET username=%s WHERE username=%s", (new_email, username))
        cur.execute("UPDATE card_reviews SET username=%s WHERE username=%s", (new_email, username))
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
        cur.execute("DELETE FROM folder_items WHERE username=%s", (username,))
        cur.execute("DELETE FROM folders WHERE username=%s", (username,))
        cur.execute("DELETE FROM card_reviews WHERE username=%s", (username,))
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


# ── Folder routes ─────────────────────────────────────────────────────────────

@app.post("/api/folders")
async def create_folder(request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Folder name required")
    folder_id = str(uuid.uuid4())
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO folders (id, username, name) VALUES (%s, %s, %s)",
                    (folder_id, username, name))
    return {"success": True, "id": folder_id, "name": name}


@app.get("/api/folders")
async def list_folders(token: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT f.id, f.name, f.created_at AT TIME ZONE 'UTC' AS created_at,
                   COUNT(fi.history_id) AS item_count
            FROM folders f
            LEFT JOIN folder_items fi ON fi.folder_id = f.id
            WHERE f.username = %s
            GROUP BY f.id, f.name, f.created_at
            ORDER BY f.created_at DESC
        """, (username,))
        rows = cur.fetchall()
        folders = []
        for row in rows:
            d = dict(row)
            d["created_at"] = d["created_at"].isoformat() if d["created_at"] else ""
            folders.append(d)
    return {"folders": folders}


@app.patch("/api/folders/{folder_id}")
async def rename_folder(folder_id: str, request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Folder name required")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE folders SET name = %s WHERE id = %s AND username = %s",
                    (name, folder_id, username))
        if cur.rowcount == 0:
            raise HTTPException(404, "Folder not found")
    return {"success": True, "name": name}


@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: str, request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM folder_items WHERE folder_id = %s AND username = %s",
                    (folder_id, username))
        cur.execute("DELETE FROM folders WHERE id = %s AND username = %s",
                    (folder_id, username))
        if cur.rowcount == 0:
            raise HTTPException(404, "Folder not found")
    return {"success": True}


@app.get("/api/folders/{folder_id}/items")
async def get_folder_items(folder_id: str, token: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT name FROM folders WHERE id = %s AND username = %s",
                    (folder_id, username))
        folder = cur.fetchone()
        if not folder:
            raise HTTPException(404, "Folder not found")
        cur.execute("""
            SELECT h.id, h.type, h.filename, h.name, h.notes, h.key_concepts,
                   h.flashcards, h.created_at AT TIME ZONE 'UTC' AS created_at
            FROM history h
            JOIN folder_items fi ON fi.history_id = h.id
            WHERE fi.folder_id = %s AND fi.username = %s
            ORDER BY fi.added_at ASC
        """, (folder_id, username))
        rows = cur.fetchall()
        items = []
        for row in rows:
            d = dict(row)
            d["created_at"] = d["created_at"].isoformat() if d["created_at"] else ""
            items.append(d)
    return {"folder_name": folder["name"], "items": items}


@app.post("/api/folders/{folder_id}/items")
async def add_folder_items(folder_id: str, request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    history_ids = data.get("history_ids", [])
    if not history_ids:
        raise HTTPException(400, "No items specified")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM folders WHERE id = %s AND username = %s",
                    (folder_id, username))
        if not cur.fetchone():
            raise HTTPException(404, "Folder not found")
        for hid in history_ids:
            cur.execute("""
                INSERT INTO folder_items (folder_id, history_id, username)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
            """, (folder_id, hid, username))
    return {"success": True}


@app.delete("/api/folders/{folder_id}/items/{history_id}")
async def remove_folder_item(folder_id: str, history_id: str, request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM folder_items WHERE folder_id=%s AND history_id=%s AND username=%s",
                    (folder_id, history_id, username))
    return {"success": True}


@app.post("/api/contact")
async def contact(request: Request):
    import smtplib
    from email.mime.text import MIMEText
    data = await request.json()
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    message = data.get("message", "").strip()
    if not name or not email or not message:
        raise HTTPException(400, "Name, email and message are required")

    smtp_user  = os.getenv("SMTP_USER", "")
    smtp_pass  = os.getenv("SMTP_PASSWORD", "")
    notify_to  = os.getenv("NOTIFY_EMAIL", "frakz321@gmail.com")
    if smtp_user and smtp_pass:
        try:
            body = f"Name: {name}\nEmail: {email}\n\n{message}"
            msg = MIMEText(body)
            msg["Subject"] = f"[Notely Contact] {name}"
            msg["From"]    = smtp_user
            msg["To"]      = notify_to
            msg["Reply-To"] = email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        except Exception as e:
            logging.warning(f"Contact email failed: {e}")

    logging.info(f"Contact from {email}: {name}")
    return {"success": True}


@app.post("/api/folders/{folder_id}/generate")
async def generate_folder_summary(folder_id: str, request: Request):
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    if get_daily_usage(username) >= DAILY_LIMIT:
        raise HTTPException(429, f"Daily limit of {DAILY_LIMIT} reached. Try again tomorrow.")

    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT name FROM folders WHERE id = %s AND username = %s",
                    (folder_id, username))
        folder = cur.fetchone()
        if not folder:
            raise HTTPException(404, "Folder not found")
        folder_name = folder["name"]

        cur.execute("""
            SELECT h.type, h.name, h.notes, h.key_concepts, h.flashcards
            FROM history h
            JOIN folder_items fi ON fi.history_id = h.id
            WHERE fi.folder_id = %s AND fi.username = %s
            ORDER BY fi.added_at ASC
        """, (folder_id, username))
        items = [dict(r) for r in cur.fetchall()]

    if not items:
        raise HTTPException(400, "Folder has no items to generate from")

    # Build combined content from all items in the folder
    combined_parts = []
    for item in items:
        label = item.get("name") or "Untitled"
        if item.get("notes"):
            combined_parts.append(f"=== {label} ===\n{item['notes']}")
        if item.get("flashcards"):
            cards = item["flashcards"]
            if isinstance(cards, list):
                qa = "\n".join(f"Q: {c['question']}\nA: {c['answer']}" for c in cards)
                combined_parts.append(f"=== {label} (flashcards) ===\n{qa}")

    if not combined_parts:
        raise HTTPException(400, "Folder items have no extractable content")

    combined_text = "\n\n".join(combined_parts)

    client = get_anthropic_client()

    # Generate combined summary
    notes_resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3500,
        temperature=0.7,
        system="""You are an expert educator. Multiple sets of study notes or flashcards have been combined into one topic folder.
Synthesize all the material into ONE comprehensive, unified study guide in markdown.
Remove duplicates, link related concepts, and add a short introduction.
Use LaTeX math notation: inline with $...$ and display with $$...$$
End with EXACTLY:
## KEY_CONCEPTS_LIST
- concept 1
(5-8 bullet points)""",
        messages=[{"role": "user", "content": f"Folder: {folder_name}\n\n{combined_text}"}]
    )
    full_text = notes_resp.content[0].text.strip()
    if "## KEY_CONCEPTS_LIST" in full_text:
        notes_md, key_concepts = full_text.split("## KEY_CONCEPTS_LIST", 1)
        notes_md = notes_md.strip()
        key_concepts = key_concepts.strip()
    else:
        notes_md, key_concepts = full_text, ""

    # Generate master flashcard deck
    cards_resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        temperature=0.5,
        system="""You are an exam preparation specialist. From combined study material, create a master flashcard deck.
Format each as:
Q: [question]
A: [answer]
---
Cover all key concepts. Aim for 10-15 cards. No duplicates.""",
        messages=[{"role": "user", "content": f"Create master flashcards from:\n\n{combined_text}"}]
    )
    flashcards = []
    for card in cards_resp.content[0].text.strip().split("---"):
        if "Q:" in card and "A:" in card:
            parts = card.split("\nA:")
            if len(parts) == 2:
                q = parts[0].replace("Q:", "").strip()
                a = parts[1].strip()
                if q and a:
                    flashcards.append({"question": q, "answer": a})

    daily_used = increment_daily_usage(username)

    entry_id = str(uuid.uuid4())
    save_to_history(username, {
        "id": entry_id, "type": "folder_summary",
        "filename": folder_name, "name": f"{folder_name} — Master Summary",
        "created_at": datetime.now().isoformat(),
        "notes": notes_md, "key_concepts": key_concepts,
        "flashcards": flashcards,
    })

    logging.info(f"Folder summary: {username} / {folder_name} ({len(items)} items)")
    return {
        "success": True, "notes": notes_md, "key_concepts": key_concepts,
        "flashcards": flashcards, "daily_used": daily_used, "daily_limit": DAILY_LIMIT,
        "entry_id": entry_id,
    }


# ── Spaced repetition routes ───────────────────────────────────────────────────

@app.get("/api/due-cards-count")
async def due_cards_count(token: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM card_reviews WHERE username = %s AND next_review <= %s",
            (username, today)
        )
        count = cur.fetchone()[0]
    return {"due": count}


@app.get("/api/study-session")
async def study_session(token: str, history_id: str):
    username = validate_token(token)
    if not username:
        raise HTTPException(401, "Invalid session")
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT flashcards FROM history WHERE id = %s AND username = %s",
                    (history_id, username))
        row = cur.fetchone()
        if not row or not row["flashcards"]:
            raise HTTPException(404, "Deck not found or has no flashcards")
        flashcards = row["flashcards"]
        cur.execute("""
            SELECT card_index, interval, ease_factor, repetitions, next_review
            FROM card_reviews WHERE username = %s AND history_id = %s
        """, (username, history_id))
        reviews = {r["card_index"]: dict(r) for r in cur.fetchall()}

    session_cards = []
    for i, card in enumerate(flashcards):
        review = reviews.get(i)
        if review is None:
            session_cards.append({
                "card_index": i, "question": card["question"], "answer": card["answer"],
                "is_new": True, "interval": 0, "ease_factor": 2.5, "repetitions": 0,
            })
        elif review["next_review"] <= today:
            session_cards.append({
                "card_index": i, "question": card["question"], "answer": card["answer"],
                "is_new": False, "interval": review["interval"],
                "ease_factor": review["ease_factor"], "repetitions": review["repetitions"],
            })

    new_count = sum(1 for c in session_cards if c["is_new"])
    due_count = sum(1 for c in session_cards if not c["is_new"])
    return {"cards": session_cards, "total": len(flashcards), "due": due_count, "new_count": new_count}


@app.post("/api/review-card")
async def review_card(request: Request):
    from datetime import timedelta
    data = await request.json()
    username = validate_token(data.get("token", ""))
    if not username:
        raise HTTPException(401, "Invalid session")
    history_id = data.get("history_id", "")
    card_index = data.get("card_index")
    quality = data.get("quality", 1)  # 1=Again, 4=Good, 5=Easy
    if card_index is None:
        raise HTTPException(400, "card_index required")

    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT interval, ease_factor, repetitions FROM card_reviews
            WHERE username = %s AND history_id = %s AND card_index = %s
        """, (username, history_id, card_index))
        existing = cur.fetchone()
        if existing:
            interval, ease_factor, repetitions = existing["interval"], existing["ease_factor"], existing["repetitions"]
        else:
            interval, ease_factor, repetitions = 0, 2.5, 0

        new_reps, new_ef, new_interval = sm2(repetitions, ease_factor, interval, quality)
        next_review = (datetime.now() + timedelta(days=new_interval)).strftime("%Y-%m-%d")

        cur.execute("""
            INSERT INTO card_reviews (id, username, history_id, card_index, interval, ease_factor, repetitions, next_review)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username, history_id, card_index) DO UPDATE SET
                interval = EXCLUDED.interval, ease_factor = EXCLUDED.ease_factor,
                repetitions = EXCLUDED.repetitions, next_review = EXCLUDED.next_review
        """, (str(uuid.uuid4()), username, history_id, card_index, new_interval, new_ef, new_reps, next_review))

    return {"success": True, "next_review": next_review, "interval": new_interval}


# ── Processing routes ──────────────────────────────────────────────────────────

MAX_PDF_PAGES = 20

def validate_upload(file_extension: str, contents: bytes):
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 25MB)")
    if len(contents) == 0:
        raise HTTPException(400, "Empty file")
    if file_extension == ".pdf":
        import io
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(contents))
            pages = len(reader.pages)
            if pages > MAX_PDF_PAGES:
                raise HTTPException(400, f"PDF has {pages} pages — max is {MAX_PDF_PAGES}. Split it into smaller sections and upload each part separately.")
        except HTTPException:
            raise
        except Exception:
            pass  # let it proceed if page count check fails


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
