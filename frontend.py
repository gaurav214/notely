"""
Smart Learning Notes Generator - Frontend v6.0
Design system: Inter · 8px grid · Indigo primary · Slate neutrals
"""

import streamlit as st
import requests
from PIL import Image
import json

st.set_page_config(
    page_title="NoteAI — Smart Study",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Design System ─────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#f8fafc;--surface:#fff;--border:#e2e8f0;--border-h:#cbd5e1;--t1:#0f172a;--t2:#475569;--t3:#94a3b8;--t4:#cbd5e1;--indigo:#4f46e5;--indigo-h:#4338ca;--indigo-s:#eef2ff;--green:#059669;--green-s:#ecfdf5;--red:#dc2626;--red-s:#fef2f2;--amber:#d97706;--amber-s:#fffbeb;--r6:6px;--r10:10px;--r14:14px;--r20:20px;--sh:0 1px 3px rgba(15,23,42,.07),0 1px 2px rgba(15,23,42,.04);--shm:0 4px 16px rgba(15,23,42,.08),0 2px 6px rgba(15,23,42,.04);--ease:140ms ease;}


*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--bg) !important;
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

[data-testid="stHeader"]  { display: none !important; }
#MainMenu                 { visibility: hidden !important; }
footer                    { visibility: hidden !important; }
.block-container          { padding: 0 !important; max-width: 100% !important; }


::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }


hr { border: none !important; border-top: 1px solid var(--border) !important;
     margin: 1.5rem 0 !important; }


/* BUTTONS                                                                      */


/* Base reset for all Streamlit buttons */
[data-testid="stButton"] > button {
  font-family: 'Inter', sans-serif !important;
  font-size: .875rem !important;
  font-weight: 500 !important;
  letter-spacing: -.01em !important;
  border-radius: var(--r10) !important;
  padding: 0 .875rem !important;
  height: 36px !important;
  line-height: 1 !important;
  background: var(--surface) !important;
  color: var(--t1) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--sh) !important;
  transition: background var(--ease), border-color var(--ease), box-shadow var(--ease) !important;
  cursor: pointer !important;
}
[data-testid="stButton"] > button:hover {
  background: var(--bg) !important;
  border-color: var(--border-h) !important;
  box-shadow: var(--sh) !important;
}
[data-testid="stButton"] > button:active {
  background: #f1f5f9 !important;
}

/* Form submit — solid indigo */
[data-testid="stFormSubmitButton"] > button {
  font-family: 'Inter', sans-serif !important;
  font-size: .9rem !important;
  font-weight: 600 !important;
  letter-spacing: -.01em !important;
  border-radius: var(--r10) !important;
  height: 42px !important;
  width: 100% !important;
  background: var(--indigo) !important;
  color: #ffffff !important;
  border: 1px solid var(--indigo) !important;
  box-shadow: 0 1px 2px rgba(79,70,229,.2) !important;
  transition: background var(--ease) !important;
  cursor: pointer !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
  background: var(--indigo-h) !important;
  border-color: var(--indigo-h) !important;
}

/* Link button */
[data-testid="stLinkButton"] > a {
  font-family: 'Inter', sans-serif !important;
  font-size: .875rem !important;
  font-weight: 500 !important;
  border-radius: var(--r10) !important;
  height: 36px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: .4rem !important;
  text-decoration: none !important;
  background: var(--surface) !important;
  color: var(--t1) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--sh) !important;
  transition: background var(--ease), border-color var(--ease) !important;
}
[data-testid="stLinkButton"] > a:hover {
  background: var(--bg) !important;
  border-color: var(--border-h) !important;
}


.btn-primary button {
  background: var(--indigo) !important;
  color: #fff !important;
  border-color: var(--indigo) !important;
  font-weight: 600 !important;
  box-shadow: 0 1px 2px rgba(79,70,229,.2) !important;
}
.btn-primary button:hover {
  background: var(--indigo-h) !important;
  border-color: var(--indigo-h) !important;
}

.btn-ghost button {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  color: var(--t2) !important;
  font-size: .82rem !important;
}
.btn-ghost button:hover {
  background: #f1f5f9 !important;
  color: var(--t1) !important;
}

.btn-danger-ghost button {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
  color: var(--t3) !important;
  font-size: .82rem !important;
  height: 32px !important;
  padding: 0 .65rem !important;
}
.btn-danger-ghost button:hover {
  background: var(--red-s) !important;
  color: var(--red) !important;
  border-color: #fca5a5 !important;
}

.btn-switch button {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
  color: var(--indigo) !important;
  font-weight: 600 !important;
  font-size: .85rem !important;
}
.btn-switch button:hover { background: var(--indigo-s) !important; }

.know-btn button {
  background: var(--green-s) !important;
  color: var(--green) !important;
  border: 1px solid #6ee7b7 !important;
  font-weight: 600 !important;
  border-radius: var(--r10) !important;
  height: 44px !important;
}
.know-btn button:hover { background: #d1fae5 !important; }

.dontknow-btn button {
  background: var(--red-s) !important;
  color: var(--red) !important;
  border: 1px solid #fca5a5 !important;
  font-weight: 600 !important;
  border-radius: var(--r10) !important;
  height: 44px !important;
}
.dontknow-btn button:hover { background: #fee2e2 !important; }

.reveal-btn button {
  background: var(--indigo) !important;
  color: #fff !important;
  border: none !important;
  font-weight: 600 !important;
  border-radius: var(--r10) !important;
  height: 44px !important;
}
.reveal-btn button:hover { background: var(--indigo-h) !important; }

.google-btn a {
  background: var(--surface) !important;
  color: #374151 !important;
  border: 1px solid var(--border) !important;
  height: 42px !important;
  font-size: .9rem !important;
  gap: .5rem !important;
}
.google-btn a:hover {
  background: var(--bg) !important;
  border-color: var(--border-h) !important;
}


/* INPUTS                                                                       */


[data-testid="stTextInput"] label { display: none !important; }
[data-testid="stTextInput"] input {
  font-family: 'Inter', sans-serif !important;
  font-size: .9rem !important;
  color: var(--t1) !important;
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r10) !important;
  height: 40px !important;
  padding: 0 .75rem !important;
  transition: border-color var(--ease), box-shadow var(--ease) !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--indigo) !important;
  box-shadow: 0 0 0 3px rgba(79,70,229,.1) !important;
  outline: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--t3) !important; }


/* FORM CARD                                                                    */


[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r14) !important;
  padding: 2rem 1.75rem 1.75rem !important;
  box-shadow: var(--shm) !important;
}


/* FILE UPLOADER                                                                */


[data-testid="stFileUploader"] {
  border: 1.5px dashed var(--border) !important;
  border-radius: var(--r14) !important;
  background: var(--surface) !important;
  transition: border-color var(--ease) !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--indigo) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] * {
  font-family: 'Inter', sans-serif !important;
  color: var(--t2) !important;
}


/* EXPANDER                                                                     */


[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--r10) !important;
  background: var(--surface) !important;
  box-shadow: none !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Inter', sans-serif !important;
  font-size: .875rem !important;
  font-weight: 500 !important;
  color: var(--t1) !important;
}


/* PROGRESS                                                                     */


[data-testid="stProgress"] > div {
  background: var(--indigo-s) !important;
  border-radius: 99px !important;
  height: 6px !important;
}
[data-testid="stProgress"] > div > div {
  background: var(--indigo) !important;
  border-radius: 99px !important;
}


/* ALERTS                                                                       */


[data-testid="stAlert"] {
  border-radius: var(--r10) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .875rem !important;
}


/* AUTH PAGE                                                                    */


.hero-eyebrow {
  display: inline-flex; align-items: center; gap: .4rem;
  background: var(--indigo-s); color: var(--indigo);
  font-size: .75rem; font-weight: 600; letter-spacing: .03em;
  text-transform: uppercase; padding: 4px 10px;
  border-radius: 99px; margin-bottom: 1.25rem;
}
.hero-title {
  font-size: 2.5rem; font-weight: 800;
  color: var(--t1); line-height: 1.15;
  letter-spacing: -.035em; margin-bottom: 1rem;
}
.hero-title em { font-style: normal; color: var(--indigo); }
.hero-sub {
  font-size: .95rem; color: var(--t2); line-height: 1.7;
  margin-bottom: 2rem; max-width: 380px;
}
.hero-feature {
  display: flex; align-items: center; gap: .6rem;
  font-size: .875rem; color: var(--t2); margin-bottom: .55rem;
}
.hero-check {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--green-s); color: var(--green);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: .6rem; font-weight: 800; flex-shrink: 0;
}

.auth-logo {
  width: 42px; height: 42px; background: var(--indigo);
  border-radius: 11px; display: flex; align-items: center;
  justify-content: center; font-size: 1.3rem;
  margin: 0 auto 1.1rem;
}
.auth-title {
  font-size: 1.2rem; font-weight: 700; color: var(--t1);
  text-align: center; letter-spacing: -.02em; margin-bottom: .2rem;
}
.auth-sub {
  font-size: .83rem; color: var(--t3); text-align: center; margin-bottom: 1.4rem;
}
.auth-divider {
  display: flex; align-items: center; gap: .75rem;
  color: var(--t3); font-size: .78rem; margin: .9rem 0;
}
.auth-divider::before, .auth-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}
.auth-switch {
  text-align: center; font-size: .82rem; color: var(--t3); margin-top: .9rem;
}


/* APP HEADER                                                                   */


.app-header {
  background: rgba(248,250,252,.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0 2rem;
  height: 52px;
  display: flex; align-items: center; justify-content: space-between;
  position: sticky; top: 0; z-index: 100;
}
.app-logo {
  display: flex; align-items: center; gap: .45rem;
  font-size: .9rem; font-weight: 700; color: var(--t1); letter-spacing: -.02em;
}
.app-logo-mark {
  width: 26px; height: 26px; background: var(--indigo);
  border-radius: 7px; display: inline-flex; align-items: center;
  justify-content: center; font-size: .75rem;
}
.app-sep { color: var(--t4); font-weight: 400; margin: 0 .1rem; }
.app-user { font-size: .83rem; color: var(--t2); font-weight: 500; }
.usage-pill {
  display: inline-flex; align-items: center; gap: .3rem;
  font-size: .76rem; font-weight: 600;
  padding: 3px 10px; border-radius: 99px; border: 1px solid;
}


/* PAGE LAYOUT                                                                  */


.page      { max-width: 920px;  margin: 0 auto; padding: 2.5rem 2rem 5rem; }
.page-wide { max-width: 1080px; margin: 0 auto; padding: 2.5rem 2rem 5rem; }

.section-label {
  font-size: .7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: var(--t3); margin-bottom: .75rem;
}


/* DASHBOARD                                                                    */


.dash-title {
  font-size: 1.5rem; font-weight: 700; color: var(--t1);
  letter-spacing: -.025em; margin-bottom: .25rem;
}
.dash-sub { font-size: .88rem; color: var(--t2); }

.mode-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r14); padding: 1.5rem;
  transition: border-color var(--ease), box-shadow var(--ease), transform var(--ease);
}
.mode-card:hover {
  border-color: var(--border-h);
  box-shadow: var(--shm);
  transform: translateY(-1px);
}
.mode-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem; margin-bottom: .875rem;
}
.mode-icon-blue  { background: var(--indigo-s); }
.mode-icon-green { background: var(--green-s); }
.mode-title { font-size: .95rem; font-weight: 600; color: var(--t1); margin-bottom: .3rem; }
.mode-desc  { font-size: .82rem; color: var(--t2); line-height: 1.55; }


/* HISTORY                                                                      */


.hist-row {
  display: flex; align-items: center; gap: .75rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r10); padding: .875rem 1.1rem;
  margin-bottom: .4rem;
  transition: border-color var(--ease);
}
.hist-row:hover { border-color: var(--border-h); }
.hist-icon {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: .85rem; flex-shrink: 0;
}
.hist-name { font-size: .875rem; font-weight: 500; color: var(--t1); }
.hist-meta { font-size: .75rem; color: var(--t3); margin-top: 2px; }


/* PAGE HEADER (back + title)                                                   */


.page-hd { display: flex; align-items: center; gap: .65rem; margin-bottom: 2rem; }
.page-hd-title {
  font-size: 1.2rem; font-weight: 700; color: var(--t1); letter-spacing: -.02em;
}


/* UPLOAD CARD                                                                  */


.upload-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r14); padding: 1.5rem;
}
.upload-card-title {
  font-size: .8rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--t3); margin-bottom: 1rem;
}
.limit-bar {
  background: var(--red-s); border: 1px solid #fecaca;
  border-radius: var(--r10); padding: .7rem 1rem;
  font-size: .84rem; color: var(--red); margin-bottom: 1rem;
}


/* NOTES OUTPUT                                                                 */


.notes-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r14); padding: 1.5rem;
  height: 100%;
}
.notes-card-title {
  font-size: .8rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--t3); margin-bottom: 1rem;
}
.key-concepts-box {
  background: var(--indigo-s); border: 1px solid #c7d2fe;
  border-radius: var(--r10); padding: 1rem 1.1rem; margin-bottom: 1.25rem;
}
.key-concepts-label {
  font-size: .7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: var(--indigo); margin-bottom: .5rem;
}
.empty-panel {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; text-align: center;
  padding: 3.5rem 1rem; gap: .5rem;
}
.empty-icon { font-size: 1.75rem; opacity: .4; }
.empty-text { font-size: .875rem; color: var(--t3); max-width: 200px; line-height: 1.5; }


/* FLASHCARD STUDY                                                              */


.study-shell { max-width: 620px; margin: 0 auto; }

.mastery-strip {
  display: flex; align-items: center; justify-content: center;
  gap: .75rem; margin-bottom: 1.25rem; flex-wrap: wrap;
}
.mp {
  display: inline-flex; align-items: center; gap: .3rem;
  font-size: .75rem; font-weight: 600;
  padding: 3px 11px; border-radius: 99px; border: 1px solid;
}
.mp-new      { background: #f1f5f9; color: #64748b; border-color: var(--border); }
.mp-learning { background: var(--amber-s); color: var(--amber); border-color: #fde68a; }
.mp-mastered { background: var(--green-s); color: var(--green); border-color: #6ee7b7; }

.remain-count {
  text-align: center; font-size: .8rem; color: var(--t3); margin-bottom: 1.25rem;
}

.fc-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r20); padding: 3rem 2.5rem;
  min-height: 210px; display: flex; align-items: center;
  justify-content: center; text-align: center;
  position: relative; box-shadow: var(--sh);
  margin-bottom: 1.25rem;
  transition: border-color var(--ease);
}
.fc-card-answer {
  background: #fafbff; border-color: #c4b5fd;
}
.fc-chip {
  position: absolute; top: 1rem; left: 50%; transform: translateX(-50%);
  font-size: .65rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .12em; color: var(--t3);
}
.fc-chip-ans { color: var(--indigo); }
.fc-q {
  font-size: 1.25rem; font-weight: 600; color: var(--t1);
  line-height: 1.5; max-width: 500px;
}
.fc-divider {
  width: 36px; height: 2px; background: var(--indigo);
  border-radius: 99px; margin: .875rem auto;
}
.fc-a {
  font-size: .975rem; color: var(--t2); line-height: 1.7; max-width: 500px;
}
.fc-hint {
  position: absolute; bottom: .875rem; left: 50%; transform: translateX(-50%);
  font-size: .7rem; color: var(--t4); white-space: nowrap;
}


/* SESSION COMPLETE                                                             */


.complete-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r20); padding: 3rem 2rem;
  text-align: center; box-shadow: var(--sh); margin: .5rem 0;
}
.complete-title {
  font-size: 1.35rem; font-weight: 700; color: var(--green);
  letter-spacing: -.02em; margin: .75rem 0 .3rem;
}
.complete-sub { font-size: .875rem; color: var(--t2); }
.complete-stats {
  display: inline-flex; gap: 1.5rem; margin-top: .75rem;
  font-size: .82rem; color: var(--t3);
}


/* FLASHCARD LIST (all cards view)                                              */


.fc-row {
  display: flex; align-items: flex-start; gap: .75rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r10); padding: .875rem 1.1rem;
  margin-bottom: .4rem;
}
.fc-num {
  font-size: .75rem; color: var(--t3); font-weight: 600;
  padding-top: .1rem; flex-shrink: 0; width: 1.4rem;
}
.fc-body { flex: 1; min-width: 0; }
.fc-q-text { font-size: .875rem; font-weight: 600; color: var(--t1); margin-bottom: .35rem; }
.fc-a-text {
  font-size: .83rem; color: var(--t2); line-height: 1.6;
  background: var(--bg); border-radius: var(--r6);
  padding: .5rem .75rem;
}

</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("token", None), ("username", None), ("daily_used", 0), ("daily_limit", 2),
    ("mode", None), ("result", None), ("auth_mode", "login"),
    ("card_flipped", False), ("study_queue", []), ("mastery", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Google OAuth redirect handler ─────────────────────────────────────────────
_qp = st.query_params
if "token" in _qp and not st.session_state.token:
    try:
        _r = requests.get(f"{API_BASE_URL}/api/usage", params={"token": _qp["token"]}, timeout=5)
        _d = _r.json()
        if _r.status_code == 200 and _d.get("username"):
            st.session_state.token     = _qp["token"]
            st.session_state.username  = _d["username"]
            st.session_state.daily_used  = _d.get("daily_used", 0)
            st.session_state.daily_limit = _d.get("daily_limit", 2)
            st.query_params.clear()
            st.rerun()
    except Exception:
        pass

if "auth_error" in _qp:
    st.error(f"Google sign-in failed: {_qp['auth_error'].replace('_', ' ')}")
    st.query_params.clear()


# ── API helpers ───────────────────────────────────────────────────────────────

def api_post(endpoint, json_data=None, files=None, data=None):
    try:
        r = requests.post(f"{API_BASE_URL}{endpoint}",
                          json=json_data, files=files, data=data, timeout=90)
        return r.status_code, r.json() if r.content else {}
    except requests.exceptions.Timeout:
        return 408, {"detail": "Request timed out. Try again."}
    except Exception as e:
        return 500, {"detail": str(e)}


def api_get(endpoint, params=None):
    try:
        r = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        return r.status_code, r.json() if r.content else {}
    except Exception as e:
        return 500, {"detail": str(e)}


def upload_and_process(file, endpoint, name=""):
    files  = {"file": (file.name, file.getvalue(), "application/octet-stream")}
    data   = {"token": st.session_state.token, "name": name}
    status, result = api_post(endpoint, files=files, data=data)
    if status == 200:
        return result
    if status == 429:
        return {"success": False, "error": f"Daily limit reached ({st.session_state.daily_limit} images/day). Come back tomorrow."}
    if status == 401:
        return {"success": False, "error": "Session expired. Please sign in again."}
    return {"success": False, "error": result.get("detail", f"Server error {status}")}


# ── Header bar ────────────────────────────────────────────────────────────────

def show_header():
    c1, c2, c3 = st.columns([3, 1.4, 0.6])
    with c1:
        st.markdown(
            f'<div class="app-header" style="position:relative;border:none;padding:.75rem 0">'
            f'<div class="app-logo">'
            f'<span class="app-logo-mark">📚</span>'
            f'NoteAI'
            f'<span class="app-sep">·</span>'
            f'<span class="app-user">{st.session_state.username}</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )
    with c2:
        used, limit = st.session_state.daily_used, st.session_state.daily_limit
        remaining = limit - used
        if remaining == 0:
            color, bg, bc = "var(--red)",   "var(--red-s)",   "#fca5a5"
        elif remaining == 1:
            color, bg, bc = "var(--amber)", "var(--amber-s)", "#fde68a"
        else:
            color, bg, bc = "var(--green)", "var(--green-s)", "#6ee7b7"
        st.markdown(
            f'<div style="padding:.75rem 0">'
            f'<span class="usage-pill" style="background:{bg};color:{color};border-color:{bc}">'
            f'{used}/{limit} uses today'
            f'</span></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown('<div class="btn-danger-ghost">', unsafe_allow_html=True)
        if st.button("Sign out", key="logout_top"):
            api_post("/api/logout", {"token": st.session_state.token})
            for k in ["token", "username", "mode", "result"]:
                st.session_state[k] = None
            st.session_state.daily_used   = 0
            st.session_state.daily_limit  = 2
            st.session_state.study_queue  = []
            st.session_state.mastery      = {}
            st.session_state.card_flipped = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:var(--border);margin:0 0 .5rem'></div>",
                unsafe_allow_html=True)


# ── Auth page ─────────────────────────────────────────────────────────────────

def show_auth_page():
    is_login = st.session_state.auth_mode == "login"
    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown("""
        <div style="padding:4rem 1.5rem 2rem">
          <div class="hero-eyebrow">✦ AI-Powered Study Tool</div>
          <div class="hero-title">
            Study smarter.<br>Learn <em>faster</em>.
          </div>
          <div class="hero-sub">
            Upload your blackboard notes, textbooks, or PDFs.
            Get structured B.Tech notes and exam-ready flashcards instantly.
          </div>
          <div class="hero-feature">
            <span class="hero-check">✓</span>
            AI notes from any blackboard photo or PDF
          </div>
          <div class="hero-feature">
            <span class="hero-check">✓</span>
            Flip-card study sessions with mastery tracking
          </div>
          <div class="hero-feature">
            <span class="hero-check">✓</span>
            B.Tech CS notes &amp; competitive exam flashcards
          </div>
          <div class="hero-feature">
            <span class="hero-check">✓</span>
            History saved — revisit any session anytime
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("<div style='padding-top:3.5rem'>", unsafe_allow_html=True)

        # Google OAuth button
        try:
            _geo = requests.get(f"{API_BASE_URL}/api/google-oauth-enabled", timeout=3).json()
            _google_on = _geo.get("enabled", False)
        except Exception:
            _google_on = False

        if _google_on:
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            st.link_button("G   Continue with Google",
                           f"{API_BASE_URL}/auth/google",
                           use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)

        # Auth form
        with st.form("login_form" if is_login else "reg_form"):
            st.markdown(f"""
            <div class="auth-logo">📚</div>
            <div class="auth-title">{"Welcome back" if is_login else "Create your account"}</div>
            <div class="auth-sub">{"Sign in to continue studying" if is_login else "Start studying smarter today"}</div>
            """, unsafe_allow_html=True)

            u = st.text_input("u",
                              placeholder="Username" if is_login else "Username (min 3 chars)",
                              label_visibility="collapsed")
            p = st.text_input("p",
                              type="password",
                              placeholder="Password" if is_login else "Password (min 6 chars)",
                              label_visibility="collapsed")
            submitted = st.form_submit_button(
                "Sign in →" if is_login else "Create account →",
                use_container_width=True
            )
            if submitted:
                if u and p:
                    if is_login:
                        s, d = api_post("/api/login", {"username": u, "password": p})
                        if s == 200:
                            st.session_state.token       = d["token"]
                            st.session_state.username    = d["username"]
                            st.session_state.daily_used  = d["daily_used"]
                            st.session_state.daily_limit = d["daily_limit"]
                            st.rerun()
                        else:
                            st.error(d.get("detail", "Invalid username or password"))
                    else:
                        s, d = api_post("/api/register", {"username": u, "password": p})
                        if s == 200:
                            st.success("Account created! Signing you in…")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(d.get("detail", "Registration failed"))
                else:
                    st.warning("Please fill in both fields.")

        st.markdown('<div class="auth-switch">', unsafe_allow_html=True)
        if is_login:
            st.markdown("Don't have an account?", unsafe_allow_html=True)
            st.markdown('<div class="btn-switch">', unsafe_allow_html=True)
            if st.button("Create a free account →", use_container_width=True, key="goto_reg"):
                st.session_state.auth_mode = "register"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("Already have an account?", unsafe_allow_html=True)
            st.markdown('<div class="btn-switch">', unsafe_allow_html=True)
            if st.button("Sign in instead →", use_container_width=True, key="goto_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def show_landing():
    show_header()
    st.markdown('<div class="page">', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-bottom:2rem">
      <div class="dash-title">Good to see you, {st.session_state.username}.</div>
      <div class="dash-sub">What would you like to study today?</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("""
        <div class="mode-card">
          <div class="mode-icon mode-icon-blue">💻</div>
          <div class="mode-title">B.Tech CS Notes</div>
          <div class="mode-desc">Structured notes with algorithms, code snippets, definitions, and key concepts.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Open Notes →", key="btech_btn", use_container_width=True):
            st.session_state.mode   = "btech"
            st.session_state.result = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="mode-card">
          <div class="mode-icon mode-icon-green">🎯</div>
          <div class="mode-title">Competitive Flashcards</div>
          <div class="mode-desc">Flip-card sessions for SSC, JEE, GATE, UPSC — with Know / Don't Know mastery.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Open Flashcards →", key="fc_btn", use_container_width=True):
            st.session_state.mode         = "competitive"
            st.session_state.result       = None
            st.session_state.card_flipped = False
            st.session_state.study_queue  = []
            st.session_state.mastery      = {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # History
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Recent history</div>', unsafe_allow_html=True)
    status, data = api_get("/api/history", {"token": st.session_state.token})
    history = data.get("history", []) if status == 200 else []

    if not history:
        st.markdown("""
        <div style="background:var(--surface);border:1px solid var(--border);
             border-radius:var(--r10);padding:2.5rem 1rem;text-align:center">
          <div style="font-size:1.5rem;opacity:.3;margin-bottom:.5rem">📭</div>
          <div style="font-size:.875rem;color:var(--t3)">No history yet. Upload an image to get started.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for entry in history[:15]:
            created     = entry["created_at"][:16].replace("T", " ")
            icon        = "💻" if entry["type"] == "btech_notes" else "🎯"
            icon_bg     = "var(--indigo-s)" if entry["type"] == "btech_notes" else "var(--green-s)"
            display_name = entry.get("name") or entry["filename"]
            with st.expander(f"{icon}  {display_name}  ·  {created}"):
                rc, bc = st.columns([3, 1])
                with rc:
                    new_name = st.text_input("Name", value=display_name,
                                             key=f"name_{entry['id']}",
                                             label_visibility="visible")
                with bc:
                    st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
                    if st.button("Rename", key=f"rename_{entry['id']}"):
                        s, _ = api_post("/api/rename-history",
                                        {"token": st.session_state.token,
                                         "entry_id": entry["id"], "name": new_name})
                        if s == 200:
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                st.divider()
                if entry["type"] == "btech_notes":
                    if entry.get("key_concepts"):
                        st.markdown('<div class="key-concepts-label">Key Concepts</div>', unsafe_allow_html=True)
                        st.markdown(entry["key_concepts"])
                        st.divider()
                    st.markdown(entry.get("notes", ""))
                    st.download_button("Download notes (.md)",
                                       entry.get("notes", ""),
                                       f"{display_name}.md", "text/markdown",
                                       key=f"dl_{entry['id']}")
                else:
                    cards = entry.get("flashcards", [])
                    for i, card in enumerate(cards, 1):
                        st.markdown(
                            f'<div class="fc-row">'
                            f'<div class="fc-num">{i}</div>'
                            f'<div class="fc-body">'
                            f'<div class="fc-q-text">{card["question"]}</div>'
                            f'<div class="fc-a-text">{card["answer"]}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                    if cards:
                        txt = "\n---\n".join([f"Q: {c['question']}\nA: {c['answer']}" for c in cards])
                        st.download_button("Download flashcards (.txt)",
                                           txt, f"{display_name}.txt", "text/plain",
                                           key=f"dl_{entry['id']}")

    st.markdown('</div>', unsafe_allow_html=True)  # /page


# ── B.Tech Notes ──────────────────────────────────────────────────────────────

def show_btech():
    show_header()
    st.markdown('<div class="page-wide">', unsafe_allow_html=True)

    # Page header
    hc1, hc2 = st.columns([0.07, 1])
    with hc1:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("←", key="back_btech"):
            st.session_state.mode   = None
            st.session_state.result = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with hc2:
        st.markdown('<div class="page-hd-title">B.Tech CS Notes</div>', unsafe_allow_html=True)

    if st.session_state.daily_used >= st.session_state.daily_limit:
        st.markdown('<div class="limit-bar">Daily limit reached — come back tomorrow.</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    cu, cr = st.columns([1, 1.2], gap="large")

    with cu:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        st.markdown('<div class="upload-card-title">Upload material</div>', unsafe_allow_html=True)
        f = st.file_uploader("Upload", type=["jpg","jpeg","png","bmp","gif","pdf"],
                             label_visibility="collapsed")
        if f:
            if f.type.startswith("image"):
                st.image(Image.open(f), use_column_width=True)
            else:
                st.markdown(
                    '<div style="background:var(--indigo-s);border:1px solid #c7d2fe;'
                    'border-radius:var(--r10);padding:.875rem;text-align:center;'
                    'color:var(--indigo);font-size:.875rem;font-weight:500">'
                    '📄 PDF selected</div>',
                    unsafe_allow_html=True
                )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            name = st.text_input("note_name",
                                 placeholder="Name these notes (optional)",
                                 label_visibility="collapsed")
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Generate notes →", use_container_width=True, key="gen_btech"):
                with st.spinner("Processing…"):
                    result = upload_and_process(f, "/api/generate-btech-notes", name=name)
                    st.session_state.result = result
                    if result.get("success"):
                        st.session_state.daily_used = result.get("daily_used",
                                                                   st.session_state.daily_used)
                    else:
                        st.error(result.get("error"))
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cr:
        st.markdown('<div class="notes-card">', unsafe_allow_html=True)
        st.markdown('<div class="notes-card-title">Study notes</div>', unsafe_allow_html=True)
        r = st.session_state.result
        if not r:
            st.markdown("""
            <div class="empty-panel">
              <div class="empty-icon">📖</div>
              <div class="empty-text">Upload a photo or PDF to generate structured notes.</div>
            </div>
            """, unsafe_allow_html=True)
        elif not r.get("success"):
            st.error(r.get("error"))
        else:
            if r.get("key_concepts"):
                st.markdown("""
                <div class="key-concepts-box">
                  <div class="key-concepts-label">Key Concepts</div>
                """, unsafe_allow_html=True)
                st.markdown(r["key_concepts"])
                st.markdown('</div>', unsafe_allow_html=True)
            with st.expander("Full notes", expanded=True):
                st.markdown(r.get("notes", ""))
            dc1, dc2 = st.columns(2)
            with dc1:
                st.download_button("Download (.md)", r.get("notes", ""),
                                   "notes.md", "text/markdown")
            with dc2:
                combined = (f"# B.Tech CS Notes\n\n## Key Concepts\n"
                            f"{r.get('key_concepts','')}\n\n---\n\n{r.get('notes','')}")
                st.download_button("Download full (.txt)", combined,
                                   "notes_full.txt", "text/plain")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # /page-wide


# ── Flashcard study session ───────────────────────────────────────────────────

def show_flashcard_study():
    flashcards = st.session_state.result.get("flashcards", [])
    queue      = st.session_state.study_queue
    mastery    = st.session_state.mastery
    total      = len(flashcards)

    new_n      = sum(1 for v in mastery.values() if v == "new")
    learning_n = sum(1 for v in mastery.values() if v == "learning")
    mastered_n = sum(1 for v in mastery.values() if v == "mastered")

    # Back + title
    hc1, hc2 = st.columns([0.07, 1])
    with hc1:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("←", key="back_study"):
            st.session_state.mode         = None
            st.session_state.result       = None
            st.session_state.study_queue  = []
            st.session_state.mastery      = {}
            st.session_state.card_flipped = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with hc2:
        fname = st.session_state.result.get("filename", "Flashcards")
        st.markdown(f'<div class="page-hd-title">{fname}</div>', unsafe_allow_html=True)

    # Mastery strip
    st.markdown(
        f'<div class="mastery-strip">'
        f'<span class="mp mp-new">● New&nbsp;&nbsp;{new_n}</span>'
        f'<span class="mp mp-learning">● Learning&nbsp;&nbsp;{learning_n}</span>'
        f'<span class="mp mp-mastered">● Mastered&nbsp;&nbsp;{mastered_n}</span>'
        f'</div>'
        f'<div class="remain-count">{len(queue)} card{"s" if len(queue) != 1 else ""} remaining</div>',
        unsafe_allow_html=True
    )

    # ── Session complete ──────────────────────────────────────────────────────
    if not queue:
        st.markdown(f"""
        <div class="complete-card">
          <div style="font-size:2.5rem">🎉</div>
          <div class="complete-title">Session complete!</div>
          <div class="complete-sub">You worked through all {total} flashcards.</div>
          <div class="complete-stats">
            <span>Mastered: <strong>{mastered_n}</strong></span>
            <span>Still learning: <strong>{learning_n}</strong></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        col_r, col_m = st.columns(2)
        with col_r:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Restart all cards", use_container_width=True, key="restart"):
                st.session_state.study_queue  = list(range(total))
                st.session_state.mastery      = {i: "new" for i in range(total)}
                st.session_state.card_flipped = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m:
            if learning_n > 0:
                if st.button(f"Review {learning_n} learning cards", use_container_width=True,
                             key="review_learning"):
                    st.session_state.study_queue  = [i for i, v in mastery.items() if v == "learning"]
                    st.session_state.card_flipped = False
                    st.rerun()

        st.divider()
        txt = "\n---\n".join([f"Q: {c['question']}\nA: {c['answer']}" for c in flashcards])
        st.download_button("Download flashcards (.txt)", txt,
                           "flashcards.txt", "text/plain")
        return

    # ── Active card ───────────────────────────────────────────────────────────
    _, card_col, _ = st.columns([0.1, 0.8, 0.1])
    with card_col:
        current_idx = queue[0]
        card        = flashcards[current_idx]
        flipped     = st.session_state.get("card_flipped", False)

        if not flipped:
            st.markdown(f"""
            <div class="fc-card">
              <span class="fc-chip">Question</span>
              <div class="fc-q">{card['question']}</div>
              <span class="fc-hint">tap to reveal answer ↓</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="reveal-btn">', unsafe_allow_html=True)
            if st.button("Reveal answer", use_container_width=True, key="reveal"):
                st.session_state.card_flipped = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="fc-card fc-card-answer">
              <span class="fc-chip fc-chip-ans">Answer</span>
              <div>
                <div class="fc-q" style="color:#312e81">{card['question']}</div>
                <div class="fc-divider"></div>
                <div class="fc-a">{card['answer']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            col_dk, col_k = st.columns(2, gap="small")
            with col_dk:
                st.markdown('<div class="dontknow-btn">', unsafe_allow_html=True)
                if st.button("✗  Don't know", use_container_width=True, key="dontknow"):
                    mastery[current_idx] = "learning"
                    queue.pop(0)
                    queue.append(current_idx)
                    st.session_state.study_queue  = queue
                    st.session_state.mastery      = mastery
                    st.session_state.card_flipped = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_k:
                st.markdown('<div class="know-btn">', unsafe_allow_html=True)
                if st.button("✓  Know it", use_container_width=True, key="knowit"):
                    mastery[current_idx] = "mastered"
                    queue.pop(0)
                    st.session_state.study_queue  = queue
                    st.session_state.mastery      = mastery
                    st.session_state.card_flipped = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.progress(mastered_n / total if total else 0,
                    text=f"{mastered_n} of {total} mastered")

    # All cards reference
    st.divider()
    with st.expander(f"All {total} flashcards"):
        for i, c in enumerate(flashcards):
            s = mastery.get(i, "new")
            badge_cls = {"new": "mp-new", "learning": "mp-learning", "mastered": "mp-mastered"}[s]
            badge_lbl = s.capitalize()
            st.markdown(
                f'<div class="fc-row">'
                f'<div class="fc-num">{i+1}</div>'
                f'<div class="fc-body">'
                f'<div class="fc-q-text">{c["question"]}</div>'
                f'<div class="fc-a-text">{c["answer"]}</div>'
                f'</div>'
                f'<span class="mp {badge_cls}" style="align-self:flex-start;flex-shrink:0">{badge_lbl}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.divider()
        txt = "\n---\n".join([f"Q: {c['question']}\nA: {c['answer']}" for c in flashcards])
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("Download (.txt)", txt, "flashcards.txt", "text/plain", key="dl_txt")
        with dl2:
            st.download_button("Download (.json)", json.dumps(flashcards, indent=2),
                               "flashcards.json", "application/json", key="dl_json")


# ── Competitive mode ──────────────────────────────────────────────────────────

def show_competitive():
    if (st.session_state.result
            and st.session_state.result.get("success")
            and st.session_state.study_queue):
        show_header()
        st.markdown('<div class="page">', unsafe_allow_html=True)
        show_flashcard_study()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    show_header()
    st.markdown('<div class="page-wide">', unsafe_allow_html=True)

    hc1, hc2 = st.columns([0.07, 1])
    with hc1:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("←", key="back_fc"):
            st.session_state.mode   = None
            st.session_state.result = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with hc2:
        st.markdown('<div class="page-hd-title">Competitive Exam Flashcards</div>',
                    unsafe_allow_html=True)

    if st.session_state.daily_used >= st.session_state.daily_limit:
        st.markdown('<div class="limit-bar">Daily limit reached — come back tomorrow.</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    cu, cp = st.columns([1, 1], gap="large")

    with cu:
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        st.markdown('<div class="upload-card-title">Upload material</div>', unsafe_allow_html=True)
        f = st.file_uploader("Upload", type=["jpg","jpeg","png","bmp","gif","pdf"],
                             label_visibility="collapsed", key="fc_uploader")
        if f:
            if f.type.startswith("image"):
                st.image(Image.open(f), use_column_width=True)
            else:
                st.markdown(
                    '<div style="background:var(--indigo-s);border:1px solid #c7d2fe;'
                    'border-radius:var(--r10);padding:.875rem;text-align:center;'
                    'color:var(--indigo);font-size:.875rem;font-weight:500">'
                    '📄 PDF selected</div>',
                    unsafe_allow_html=True
                )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            name = st.text_input("fc_name",
                                 placeholder="Name these flashcards (optional)",
                                 label_visibility="collapsed")
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Generate flashcards →", use_container_width=True, key="gen_fc"):
                with st.spinner("Generating flashcards…"):
                    result = upload_and_process(f, "/api/generate-competitive-flashcards",
                                                name=name)
                    if result.get("success"):
                        cards = result.get("flashcards", [])
                        st.session_state.result       = result
                        st.session_state.daily_used   = result.get("daily_used",
                                                                     st.session_state.daily_used)
                        st.session_state.study_queue  = list(range(len(cards)))
                        st.session_state.mastery      = {i: "new" for i in range(len(cards))}
                        st.session_state.card_flipped = False
                        st.rerun()
                    else:
                        st.error(result.get("error"))
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cp:
        st.markdown("""
        <div style="background:var(--surface);border:1px solid var(--border);
             border-radius:var(--r14);padding:1.5rem">
          <div class="upload-card-title">How it works</div>
          <div style="display:flex;flex-direction:column;gap:1rem;margin-top:.25rem">
            <div style="display:flex;gap:.875rem;align-items:flex-start">
              <div style="width:24px;height:24px;border-radius:6px;background:var(--indigo-s);
                   color:var(--indigo);font-size:.7rem;font-weight:700;display:flex;
                   align-items:center;justify-content:center;flex-shrink:0;margin-top:.1rem">1</div>
              <div>
                <div style="font-size:.875rem;font-weight:600;color:var(--t1);margin-bottom:.15rem">Upload</div>
                <div style="font-size:.82rem;color:var(--t2);line-height:1.5">Blackboard photo, textbook scan, or PDF</div>
              </div>
            </div>
            <div style="display:flex;gap:.875rem;align-items:flex-start">
              <div style="width:24px;height:24px;border-radius:6px;background:var(--indigo-s);
                   color:var(--indigo);font-size:.7rem;font-weight:700;display:flex;
                   align-items:center;justify-content:center;flex-shrink:0;margin-top:.1rem">2</div>
              <div>
                <div style="font-size:.875rem;font-weight:600;color:var(--t1);margin-bottom:.15rem">AI generates 8–12 flashcards</div>
                <div style="font-size:.82rem;color:var(--t2);line-height:1.5">Targeted Q&A ordered from basic to advanced</div>
              </div>
            </div>
            <div style="display:flex;gap:.875rem;align-items:flex-start">
              <div style="width:24px;height:24px;border-radius:6px;background:var(--indigo-s);
                   color:var(--indigo);font-size:.7rem;font-weight:700;display:flex;
                   align-items:center;justify-content:center;flex-shrink:0;margin-top:.1rem">3</div>
              <div>
                <div style="font-size:.875rem;font-weight:600;color:var(--t1);margin-bottom:.15rem">Study until mastered</div>
                <div style="font-size:.82rem;color:var(--t2);line-height:1.5">Know It removes a card · Don't Know keeps it cycling</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # /page-wide


# ── Router ────────────────────────────────────────────────────────────────────

if not st.session_state.token:
    try:
        healthy = requests.get(f"{API_BASE_URL}/health", timeout=3).status_code == 200
    except Exception:
        healthy = False
    if not healthy:
        st.markdown("<div style='height:35vh'></div>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.error("Backend is offline. Start the server and refresh.")
    else:
        show_auth_page()
elif st.session_state.mode is None:
    show_landing()
elif st.session_state.mode == "btech":
    show_btech()
elif st.session_state.mode == "competitive":
    show_competitive()
