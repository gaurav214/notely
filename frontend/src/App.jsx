import { useState, useEffect, useCallback, useRef } from 'react';
import { marked } from 'marked';
import renderMathInElement from 'katex/contrib/auto-render';

marked.setOptions({ breaks: true, gfm: true });

const KATEX_OPTS = {
  delimiters: [
    { left: '$$', right: '$$', display: true },
    { left: '$',  right: '$',  display: false },
    { left: '\\(', right: '\\)', display: false },
    { left: '\\[', right: '\\]', display: true },
  ],
  throwOnError: false,
  errorColor: '#ef4444',
};

function MarkdownBody({ content }) {
  const ref = useRef();
  useEffect(() => {
    if (ref.current && content) renderMathInElement(ref.current, KATEX_OPTS);
  }, [content]);
  return (
    <div ref={ref} className="markdown-body"
      dangerouslySetInnerHTML={{ __html: marked.parse(content) }} />
  );
}

const API_BASE = import.meta.env.VITE_API_URL ?? '';

const api = {
  async post(path, body) {
    const r = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Something went wrong');
    return data;
  },
  async get(path) {
    const r = await fetch(`${API_BASE}${path}`);
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Request failed');
    return data;
  },
  async upload(path, formData) {
    const r = await fetch(`${API_BASE}${path}`, { method: 'POST', body: formData });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Upload failed');
    return data;
  },
};

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch { return false; }
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}

function displayName(username) {
  if (!username) return '';
  const at = username.indexOf('@');
  return at > 0 ? username.slice(0, at) : username;
}

/* ── Icons (Lucide-style, inlined) ───────────────────────────────────────────── */

const iconProps = { xmlns: 'http://www.w3.org/2000/svg', width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round' };

const Icon = {
  FileText: (p = {}) => <svg {...iconProps} {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><line x1="10" y1="9" x2="8" y2="9" /></svg>,
  Layers: (p = {}) => <svg {...iconProps} {...p}><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></svg>,
  Upload: (p = {}) => <svg {...iconProps} {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>,
  ArrowLeft: (p = {}) => <svg {...iconProps} {...p}><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>,
  ArrowRight: (p = {}) => <svg {...iconProps} {...p}><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>,
  Check: (p = {}) => <svg {...iconProps} {...p}><polyline points="20 6 9 17 4 12" /></svg>,
  X: (p = {}) => <svg {...iconProps} {...p}><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>,
  Info: (p = {}) => <svg {...iconProps} {...p}><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>,
  Play: (p = {}) => <svg {...iconProps} {...p}><polygon points="6 3 20 12 6 21 6 3" fill="currentColor" /></svg>,
  File: (p = {}) => <svg {...iconProps} {...p}><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><polyline points="13 2 13 9 20 9" /></svg>,
  Archive: (p = {}) => <svg {...iconProps} {...p}><polyline points="21 8 21 21 3 21 3 8" /><rect x="1" y="3" width="22" height="5" /><line x1="10" y1="12" x2="14" y2="12" /></svg>,
  CheckCircle: (p = {}) => <svg {...iconProps} {...p}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>,
  Pencil: (p = {}) => <svg {...iconProps} {...p}><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>,
  Download: (p = {}) => <svg {...iconProps} {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>,
};

/* ── Utility components ──────────────────────────────────────────────────────── */

function Spinner({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="spinner" fill="none">
      <circle cx="12" cy="12" r="10" strokeWidth="2.5" stroke="currentColor"
        strokeDasharray="32" strokeDashoffset="12" strokeLinecap="round" />
    </svg>
  );
}

function useToast() {
  const [toasts, setToasts] = useState([]);
  const show = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 3500);
  }, []);
  return { toasts, show };
}

function ToastStack({ toasts }) {
  return (
    <div className="toast-stack">
      {toasts.map(t => {
        const I = t.type === 'success' ? Icon.Check : t.type === 'error' ? Icon.X : Icon.Info;
        return (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span className="toast-icon"><I width={14} height={14} /></span>
            {t.message}
          </div>
        );
      })}
    </div>
  );
}

/* ── Logo mark (flat, single color) ──────────────────────────────────────────── */

function LogoMark({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none" aria-hidden="true">
      <rect width="28" height="28" rx="7" fill="var(--c-accent)" />
      <path d="M8 9h12M8 14h8M8 19h10" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/* ── Header ─────────────────────────────────────────────────────────────────── */

function Header({ user, onNavigate, view, onFeedback }) {
  return (
    <header className="header">
      <button className="header-logo" onClick={() => onNavigate('dashboard')}>
        <LogoMark size={22} />
        <span className="header-brand">Notely</span>
      </button>

      <nav className="header-nav">
        {[['notes', 'Notes'], ['flashcards', 'Flashcards'], ['history', 'History']].map(([v, label]) => (
          <button key={v} className={`header-nav-item ${view === v ? 'active' : ''}`} onClick={() => onNavigate(v)}>
            {label}
          </button>
        ))}
      </nav>

      <div className="header-user">
        <div className="usage-pill">
          <div className="usage-dots">
            {Array.from({ length: user.daily_limit }, (_, i) => (
              <span key={i} className={`usage-dot ${i < user.daily_used ? 'used' : ''}`} />
            ))}
          </div>
          <span className="usage-text">{user.daily_used}/{user.daily_limit}</span>
        </div>
        <button className="btn btn-ghost btn-sm feedback-header-btn" onClick={onFeedback}>Feedback</button>
        <div className="user-avatar">{displayName(user.username)[0]?.toUpperCase() ?? '?'}</div>
        <button className="btn btn-ghost" onClick={() => onNavigate('logout')}>Sign out</button>
      </div>
    </header>
  );
}

/* ── Feedback modal ──────────────────────────────────────────────────────────── */

const FEEDBACK_OPTIONS = [
  { id: 'dsa',       label: 'Help with DSA' },
  { id: 'capstone',  label: 'Capstone Project for college' },
  { id: 'workshop',  label: 'Workshop lecture on a topic' },
  { id: 'limit',     label: 'Need more daily limit' },
];

function FeedbackModal({ user, onClose, toast }) {
  const [selected, setSelected] = useState(new Set());
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  function toggle(id) {
    setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  async function handleSubmit() {
    setLoading(true);
    try {
      await api.post('/api/feedback', { token: user.token, options: [...selected], message: message.trim() });
      setDone(true);
      setTimeout(onClose, 2000);
    } catch {
      toast.show('Could not send — try again', 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">Send feedback</h2>
          <button className="modal-close" onClick={onClose}><Icon.X width={16} height={16} /></button>
        </div>

        {done ? (
          <div className="modal-done">
            <Icon.CheckCircle width={40} height={40} />
            <p>Thanks! We'll work on it.</p>
          </div>
        ) : (
          <>
            <p className="modal-sub">What would you like from Notely? Pick all that apply.</p>
            <div className="feedback-options">
              {FEEDBACK_OPTIONS.map(opt => (
                <button key={opt.id}
                  className={`feedback-chip ${selected.has(opt.id) ? 'selected' : ''}`}
                  onClick={() => toggle(opt.id)}>
                  {selected.has(opt.id) && <Icon.Check width={12} height={12} />}
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="form-group" style={{ marginTop: 18 }}>
              <label className="form-label">Anything else? <span className="form-label-opt">(optional)</span></label>
              <textarea className="input" rows={3}
                style={{ height: 'auto', resize: 'vertical' }}
                placeholder="Tell us what you need…"
                value={message} onChange={e => setMessage(e.target.value)} />
            </div>
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmit}
                disabled={loading || (selected.size === 0 && !message.trim())}>
                {loading ? <><Spinner size={13} /> Sending…</> : 'Send feedback'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Landing page ───────────────────────────────────────────────────────────── */

function LandingPage({ onGetStarted }) {
  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-brand">
            <LogoMark size={26} />
            <span>Notely</span>
          </div>
          <div className="landing-nav-links">
            <button onClick={() => scrollTo('features')}>Features</button>
            <button onClick={() => scrollTo('how')}>How it works</button>
            <button onClick={() => scrollTo('faq')}>FAQ</button>
          </div>
          <div className="landing-nav-actions">
            <button className="btn btn-ghost" onClick={onGetStarted}>Sign in</button>
            <button className="btn btn-primary" onClick={onGetStarted}>Get started</button>
          </div>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-inner">
          <div className="hero-content">
            <span className="hero-eyebrow">
              <span className="hero-eyebrow-dot" /> AI study companion
            </span>
            <h1 className="hero-title">
              Turn messy notes into<br />
              <span className="hero-title-accent">clear study guides.</span>
            </h1>
            <p className="hero-sub">
              Snap a photo of your handwritten notes or upload a PDF. Notely turns them into
              structured markdown and flashcards in seconds — so you can study smarter, not harder.
            </p>
            <div className="hero-cta">
              <button className="btn btn-primary btn-lg" onClick={onGetStarted}>
                Get started — free
              </button>
              <button className="btn btn-secondary btn-lg" onClick={() => scrollTo('how')}>
                See how it works
              </button>
            </div>
            <p className="hero-meta">Free forever · No credit card · Any subject</p>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="mockup-notes">
              <div className="mockup-chrome">
                <span className="mockup-dot" />
                <span className="mockup-dot" />
                <span className="mockup-dot" />
                <span className="mockup-tab">Data Structures.pdf</span>
              </div>
              <div className="mockup-body">
                <div className="mockup-h1"># Binary Search Trees</div>
                <div className="mockup-p">A hierarchical data structure where each node has at most two children — a left and a right subtree.</div>
                <div className="mockup-h2">## Properties</div>
                <ul className="mockup-ul">
                  <li>Left subtree values &lt; node</li>
                  <li>Right subtree values &gt; node</li>
                  <li>In-order traversal is sorted</li>
                </ul>
                <div className="mockup-code">
                  <span className="mockup-code-kw">function</span> <span className="mockup-code-fn">insert</span>(node, val) {'{'}
                </div>
              </div>
            </div>

            <div className="mockup-card-front">
              <div className="mockup-card-label">CARD 01</div>
              <div className="mockup-card-q">What is the time complexity of insertion in a balanced BST?</div>
              <div className="mockup-card-hint">tap to flip</div>
            </div>

            <div className="mockup-card-back">
              <div className="mockup-card-label accent">ANSWER</div>
              <div className="mockup-card-a">O(log n)</div>
            </div>

            <div className="hero-blob hero-blob-1" />
            <div className="hero-blob hero-blob-2" />
          </div>
        </div>
      </section>

      <section id="features" className="landing-section">
        <div className="section-inner">
          <span className="landing-eyebrow">Features</span>
          <h2 className="landing-h2">Everything you need to actually learn.</h2>
          <p className="landing-lede">
            One photo in, structured study material out. Built with Claude for accuracy across any subject.
          </p>

          <div className="features-grid">
            <LandingFeature
              icon={<Icon.FileText width={20} height={20} />}
              title="Study notes"
              desc="Handwritten pages become clean markdown — headings, bullet points, formulas, code."
              color="note"
            />
            <LandingFeature
              icon={<Icon.Layers width={20} height={20} />}
              title="Flashcards"
              desc="Flip cards generated from your material. Keyboard-friendly, spaced by difficulty."
              color="card"
            />
            <LandingFeature
              icon={<Icon.Play width={20} height={20} />}
              title="Study mode"
              desc="Focused review with keyboard shortcuts, progress tracking, and mastery marking."
              color="play"
            />
            <LandingFeature
              icon={<Icon.Archive width={20} height={20} />}
              title="History"
              desc="Every generation saved. Revisit, re-study, and export anytime."
              color="arch"
            />
            <LandingFeature
              icon={<Icon.File width={20} height={20} />}
              title="PDF & photo"
              desc="JPG, PNG, BMP, PDF — anything you've got. Drag, drop, done."
              color="file"
            />
            <LandingFeature
              icon={<Icon.CheckCircle width={20} height={20} />}
              title="Any subject"
              desc="Math proofs, bio diagrams, history timelines, code snippets — all handled."
              color="check"
            />
          </div>
        </div>
      </section>

      <section id="how" className="landing-section how-section">
        <div className="section-inner">
          <span className="landing-eyebrow">How it works</span>
          <h2 className="landing-h2">From photo to study-ready in three steps.</h2>

          <div className="how-grid">
            <div className="how-step">
              <div className="how-step-num">01</div>
              <h3>Upload</h3>
              <p>Snap a photo of your notes or drop in a PDF. Works on anything legible.</p>
            </div>
            <div className="how-connector" />
            <div className="how-step">
              <div className="how-step-num">02</div>
              <h3>AI extracts</h3>
              <p>Claude reads the handwriting and organizes it into structured, readable content.</p>
            </div>
            <div className="how-connector" />
            <div className="how-step">
              <div className="how-step-num">03</div>
              <h3>Study</h3>
              <p>Review notes, flip flashcards, track progress. Come back anytime from history.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="faq" className="landing-section faq-section">
        <div className="section-inner faq-inner">
          <div>
            <span className="landing-eyebrow">FAQ</span>
            <h2 className="landing-h2">Questions, answered.</h2>
          </div>
          <div className="faq-list">
            <details className="faq-item">
              <summary>Is Notely free?</summary>
              <p>Yes. Every student gets a daily quota of generations at no cost. No card required.</p>
            </details>
            <details className="faq-item">
              <summary>Which subjects does it work for?</summary>
              <p>Anything legible — sciences, engineering, humanities, languages. Claude adapts the notes to the subject.</p>
            </details>
            <details className="faq-item">
              <summary>What file types can I upload?</summary>
              <p>JPG, PNG, BMP, GIF, and PDF. Photos from your phone work great.</p>
            </details>
            <details className="faq-item">
              <summary>Do you store my notes?</summary>
              <p>Only in your own history, so you can come back to past generations. You can delete them any time.</p>
            </details>
          </div>
        </div>
      </section>

      <section className="final-cta">
        <div className="section-inner final-cta-inner">
          <h2>Ready to study smarter?</h2>
          <p>Turn your next photo of notes into a study guide in seconds.</p>
          <button className="btn btn-primary btn-lg" onClick={onGetStarted}>
            Get started — free
          </button>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="section-inner footer-inner">
          <div className="landing-brand">
            <LogoMark size={22} />
            <span>Notely</span>
          </div>
          <p className="footer-meta">© 2026 Notely · Built for students.</p>
        </div>
      </footer>
    </div>
  );
}

function LandingFeature({ icon, title, desc, color }) {
  return (
    <div className={`landing-feature landing-feature-${color}`}>
      <div className="landing-feature-icon">{icon}</div>
      <h3 className="landing-feature-title">{title}</h3>
      <p className="landing-feature-desc">{desc}</p>
    </div>
  );
}

/* ── Auth page (minimal — form only) ─────────────────────────────────────────── */

function AuthPage({ onLogin, onBack }) {
  const [tab, setTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [googleEnabled, setGoogleEnabled] = useState(false);

  useEffect(() => {
    api.get('/api/google-oauth-enabled').then(d => setGoogleEnabled(d.enabled)).catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (tab === 'register') {
        await api.post('/api/register', { username: email, password });
      }
      const data = await api.post('/api/login', { username: email, password });
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function switchTab(t) { setTab(t); setError(''); }

  return (
    <div className="auth-layout">
      {onBack && (
        <button className="auth-back" onClick={onBack}>
          <Icon.ArrowLeft width={13} height={13} /> Home
        </button>
      )}
      <div className="auth-card">
        <div className="auth-logo">
          <LogoMark size={24} />
          <span>Notely</span>
        </div>
        <p className="auth-welcome">
          {tab === 'login' ? 'Sign in to continue.' : 'Create an account to get started.'}
        </p>

        <div className="auth-tabs">
          <button className={`auth-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => switchTab('login')}>Sign in</button>
          <button className={`auth-tab ${tab === 'register' ? 'active' : ''}`} onClick={() => switchTab('register')}>Create account</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="input" type="email" placeholder="you@example.com"
              value={email} onChange={e => setEmail(e.target.value)}
              required autoComplete="email" />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="input" type="password" placeholder="••••••••"
              value={password} onChange={e => setPassword(e.target.value)}
              required autoComplete={tab === 'login' ? 'current-password' : 'new-password'} />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
            {loading && <Spinner size={14} />}
            {tab === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        {googleEnabled && (
          <>
            <div className="auth-divider"><span>or</span></div>
            <a href={`${API_BASE}/auth/google`} className="btn btn-google btn-full">
              <svg width="15" height="15" viewBox="0 0 18 18" aria-hidden="true">
                <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
                <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"/>
                <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 0 1 0-3.04V5.41H1.83a8 8 0 0 0 0 7.18l2.67-2.07z"/>
                <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.4L4.5 7.49a4.77 4.77 0 0 1 4.48-3.3z"/>
              </svg>
              Continue with Google
            </a>
          </>
        )}

        <p className="auth-footer">
          {tab === 'login' ? 'No account yet? ' : 'Already have one? '}
          <button type="button" onClick={() => switchTab(tab === 'login' ? 'register' : 'login')}
            style={{ color: 'var(--c-text-1)', textDecoration: 'underline', textUnderlineOffset: 3 }}>
            {tab === 'login' ? 'Create one' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
}

/* ── Dashboard ──────────────────────────────────────────────────────────────── */

function FeatureCard({ icon, title, description, tag, onClick, disabled }) {
  return (
    <button className={`feature-card ${disabled ? 'disabled' : ''}`}
      onClick={onClick} disabled={disabled}>
      <div className="feature-card-icon">{icon}</div>
      <div className="feature-card-content">
        <div className="feature-card-top">
          <h3 className="feature-card-title">{title}</h3>
          {tag && <span className="feature-card-tag">{tag}</span>}
        </div>
        <p className="feature-card-desc">{description}</p>
      </div>
      <span className="feature-card-arrow"><Icon.ArrowRight width={14} height={14} /></span>
    </button>
  );
}

function NoteModal({ entry, onClose }) {
  const isNotes = entry.type === 'notes' || entry.type === 'btech_notes';
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card note-modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">{entry.name || entry.filename}</span>
          <div style={{ display: 'flex', gap: 8 }}>
            {isNotes && entry.notes && (
              <button className="btn-secondary btn-sm" onClick={() => downloadNotesPDF(entry)}>
                <Icon.Download /> PDF
              </button>
            )}
            <button className="modal-close" onClick={onClose}><Icon.X /></button>
          </div>
        </div>
        <div className="note-modal-body">
          {isNotes && entry.notes && <MarkdownBody content={entry.notes} />}
          {entry.type === 'competitive_flashcards' && entry.flashcards && (
            <div className="cards-grid">
              {entry.flashcards.map((c, i) => <FlipCard key={i} index={i} question={c.question} answer={c.answer} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Dashboard({ user, onNavigate }) {
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [previewEntry, setPreviewEntry] = useState(null);
  const remaining = user.daily_limit - user.daily_used;

  useEffect(() => {
    api.get(`/api/history?token=${user.token}`)
      .then(d => setHistory(d.history.slice(0, 5)))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  }, [user.token]);

  const pct = (user.daily_used / user.daily_limit) * 100;

  return (
    <div className="page">
      <div className="container">
        <div className="dashboard-header">
          <div>
            <p className="dashboard-greeting">Good {getTimeOfDay()}</p>
            <h1 className="dashboard-username">{displayName(user.username)}</h1>
          </div>

          <div className="usage-card">
            <div className="usage-ring">
              <svg viewBox="0 0 36 36" fill="none">
                <circle cx="18" cy="18" r="15.9" stroke="var(--c-border)" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.9" stroke="var(--c-text-1)" strokeWidth="3"
                  strokeDasharray={`${pct} 100`} strokeLinecap="round"
                  transform="rotate(-90 18 18)" />
              </svg>
              <div className="usage-ring-text">{user.daily_used}/{user.daily_limit}</div>
            </div>
            <div className="usage-info">
              <p className="usage-title">Daily usage</p>
              <p className="usage-sub">{remaining > 0 ? `${remaining} left today` : 'Limit reached'}</p>
            </div>
          </div>
        </div>

        <section className="section">
          <p className="section-title" style={{ marginBottom: 12 }}>Generate</p>
          <div className="feature-grid">
            <FeatureCard
              icon={<Icon.FileText width={16} height={16} />}
              title="Study Notes"
              description="One photo of your notes becomes a structured markdown study guide with key concepts and explanations."
              tag="Notes"
              onClick={() => onNavigate('notes')}
              disabled={remaining <= 0}
            />
            <FeatureCard
              icon={<Icon.Layers width={16} height={16} />}
              title="Flashcards"
              description="Turn any content into flip cards. Study with keyboard shortcuts and mark what you've mastered."
              tag="Recall"
              onClick={() => onNavigate('flashcards')}
              disabled={remaining <= 0}
            />
          </div>
          {remaining <= 0 && (
            <p className="limit-notice">Daily limit reached. Back tomorrow for {user.daily_limit} more.</p>
          )}
        </section>

        <section className="section">
          <div className="section-header">
            <p className="section-title">Recent</p>
            <button className="btn btn-ghost" onClick={() => onNavigate('history')}>View all</button>
          </div>
          {loadingHistory ? (
            <div className="loading-row"><Spinner /> Loading…</div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <Icon.Archive width={22} height={22} />
              <p>No generations yet.</p>
            </div>
          ) : (
            <div className="history-list">
              {history.map(entry => (
                <HistoryItem key={entry.id} entry={entry} compact user={user}
                  onRename={(action, e) => {
                    if (action === 'open') { setPreviewEntry(e); return; }
                    setHistory(h => h.map(x => x.id === action ? { ...x, name: e } : x));
                  }}
                />
              ))}
            </div>
          )}
        </section>
      </div>
      {previewEntry && <NoteModal entry={previewEntry} onClose={() => setPreviewEntry(null)} />}
    </div>
  );
}

/* ── Notes page ─────────────────────────────────────────────────────────────── */

function NotesPage({ user, onNavigate, onUsageUpdate, toast }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  function handleFile(f) {
    if (!f) return;
    setFile(f);
    if (!name) setName(f.name.replace(/\.[^/.]+$/, ''));
    setError('');
    setResult(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('token', user.token);
      fd.append('name', name || file.name);
      const data = await api.upload('/api/generate-notes', fd);
      setResult(data);
      onUsageUpdate(data.daily_used);
      toast.show('Notes generated', 'success');
    } catch (err) {
      setError(err.message);
      toast.show(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (await copyText(result.notes)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.show('Copied', 'success');
    }
  }

  const keyConcepts = result?.key_concepts
    ? result.key_concepts.split('\n').filter(l => l.trim().startsWith('-')).map(l => l.replace(/^-\s*/, '').trim()).filter(Boolean)
    : [];

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <button className="back-btn" onClick={() => onNavigate('dashboard')}>
            <Icon.ArrowLeft width={13} height={13} /> Back
          </button>
          <div>
            <h1 className="page-title">Study Notes</h1>
            <p className="page-sub">Upload a photo or PDF of your notes.</p>
          </div>
        </div>

        <div className="split-layout">
          <div className="upload-section">
            <div className="upload-card">
              <h2 className="card-title">Upload</h2>
              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div
                  className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                  onClick={() => fileRef.current?.click()}
                  onDragOver={e => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
                >
                  <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.bmp,.gif,.pdf"
                    onChange={e => handleFile(e.target.files[0])} style={{ display: 'none' }} />
                  {file ? (
                    <div className="drop-zone-file">
                      <div className="drop-zone-file-icon"><Icon.File width={22} height={22} /></div>
                      <p className="drop-zone-filename">{file.name}</p>
                      <p className="drop-zone-filesize">{(file.size / 1024).toFixed(0)} KB</p>
                    </div>
                  ) : (
                    <>
                      <div className="drop-zone-icon"><Icon.Upload width={22} height={22} /></div>
                      <p className="drop-zone-text">Drop image or PDF</p>
                      <p className="drop-zone-sub">JPG, PNG, PDF · max 25 MB</p>
                    </>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label">Name <span className="form-label-opt">(optional)</span></label>
                  <input className="input" type="text"
                    placeholder="DSA Lecture 5"
                    value={name} onChange={e => setName(e.target.value)} />
                </div>

                {error && <div className="form-error">{error}</div>}

                <button className="btn btn-primary btn-full" type="submit"
                  disabled={!file || loading || user.daily_used >= user.daily_limit}>
                  {loading ? <><Spinner size={14} /> Generating…</> : 'Generate notes'}
                </button>

                {user.daily_used >= user.daily_limit && (
                  <p className="limit-notice">Daily limit reached.</p>
                )}
              </form>
            </div>
          </div>

          {result ? (
            <div className="result-section">
              {keyConcepts.length > 0 && (
                <div className="concept-card">
                  <h3 className="card-title" style={{ marginBottom: 12 }}>Key concepts</h3>
                  <div className="concept-tags">
                    {keyConcepts.map((c, i) => <span key={i} className="concept-tag">{c}</span>)}
                  </div>
                </div>
              )}
              <div className="notes-card">
                <div className="notes-card-header">
                  <h3 className="card-title" style={{ margin: 0 }}>Notes</h3>
                  <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
                    {copied ? <><Icon.Check width={12} height={12} /> Copied</> : 'Copy'}
                  </button>
                </div>
                <MarkdownBody content={result.notes} />
              </div>
            </div>
          ) : loading ? (
            <div className="result-placeholder">
              <Spinner size={24} />
              <p>Analyzing…</p>
              <p className="placeholder-sub">15–30 seconds</p>
            </div>
          ) : (
            <div className="result-placeholder">
              <div className="placeholder-icon"><Icon.FileText width={22} height={22} /></div>
              <p>Notes will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Flip card ──────────────────────────────────────────────────────────────── */

function FlipCard({ index, question, answer }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <div className={`flip-card ${flipped ? 'flipped' : ''}`} onClick={() => setFlipped(f => !f)}>
      <div className="flip-inner">
        <div className="flip-front">
          <span className="flip-num">Q{String(index + 1).padStart(2, '0')}</span>
          <p className="flip-text">{question}</p>
          <span className="flip-hint">Tap to reveal</span>
        </div>
        <div className="flip-back">
          <span className="flip-num accent">ANSWER</span>
          <p className="flip-text">{answer}</p>
          <span className="flip-hint">Tap to flip back</span>
        </div>
      </div>
    </div>
  );
}

/* ── Study mode ─────────────────────────────────────────────────────────────── */

function StudyMode({ cards, onExit }) {
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [mastered, setMastered] = useState(new Set());
  const [skipped, setSkipped] = useState(new Set());
  const [done, setDone] = useState(false);

  const card = cards[current];

  const goNext = useCallback(() => {
    if (current < cards.length - 1) { setCurrent(c => c + 1); setFlipped(false); }
    else setDone(true);
  }, [current, cards.length]);

  const goPrev = useCallback(() => {
    if (current > 0) { setCurrent(c => c - 1); setFlipped(false); }
  }, [current]);

  useEffect(() => {
    function onKey(e) {
      if (e.key === ' ' || e.key === 'ArrowDown') { e.preventDefault(); setFlipped(f => !f); }
      if (e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowLeft') goPrev();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [goNext, goPrev]);

  function markMastered() { setMastered(m => new Set([...m, current])); goNext(); }
  function markSkipped() { setSkipped(s => new Set([...s, current])); goNext(); }

  if (done) {
    return (
      <div className="study-mode">
        <div className="study-complete">
          <div className="study-complete-icon"><Icon.CheckCircle width={44} height={44} /></div>
          <h2>Session complete</h2>
          <p className="study-complete-sub">Nice work. Here's how it went.</p>
          <div className="study-stats">
            <div className="study-stat">
              <span className="study-stat-num" style={{ color: 'var(--c-success)' }}>{mastered.size}</span>
              <span className="study-stat-label">Mastered</span>
            </div>
            <div className="study-stat">
              <span className="study-stat-num" style={{ color: 'var(--c-warning)' }}>{skipped.size}</span>
              <span className="study-stat-label">Review</span>
            </div>
            <div className="study-stat">
              <span className="study-stat-num">{cards.length}</span>
              <span className="study-stat-label">Total</span>
            </div>
          </div>
          <div className="study-complete-actions">
            <button className="btn btn-primary"
              onClick={() => { setCurrent(0); setFlipped(false); setDone(false); setMastered(new Set()); setSkipped(new Set()); }}>
              Study again
            </button>
            <button className="btn btn-secondary" onClick={onExit}>Back to cards</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="study-mode">
      <div className="study-header">
        <button className="btn btn-ghost" onClick={onExit}><Icon.ArrowLeft width={13} height={13} /> Exit</button>
        <div className="study-progress-wrap">
          <div className="study-progress-bar">
            <div className="study-progress-fill" style={{ width: `${(current / cards.length) * 100}%` }} />
          </div>
          <span className="study-progress-text">{current + 1} / {cards.length}</span>
        </div>
        <div className="study-mastery">{mastered.size} mastered</div>
      </div>

      <div className="study-card-wrap">
        <div className={`study-flip-card flip-card ${flipped ? 'flipped' : ''}`}
          onClick={() => setFlipped(f => !f)}>
          <div className="flip-inner">
            <div className="flip-front study-flip-face">
              <span className="study-flip-label">Question</span>
              <p className="study-flip-text">{card.question}</p>
              <span className="flip-hint">Space or tap to reveal</span>
            </div>
            <div className="flip-back study-flip-face">
              <span className="study-flip-label accent">Answer</span>
              <p className="study-flip-text">{card.answer}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="study-actions">
        <button className="btn btn-secondary" onClick={goPrev} disabled={current === 0}>
          <Icon.ArrowLeft width={13} height={13} /> Prev
        </button>
        {flipped ? (
          <>
            <button className="btn btn-success" onClick={markMastered}><Icon.Check width={13} height={13} /> Got it</button>
            <button className="btn btn-warn" onClick={markSkipped}>Review later</button>
          </>
        ) : (
          <button className="btn btn-primary" onClick={() => setFlipped(true)}>Reveal answer</button>
        )}
        <button className="btn btn-secondary" onClick={goNext}>
          Next <Icon.ArrowRight width={13} height={13} />
        </button>
      </div>

      <div className="study-keyboard-hint">
        <kbd>Space</kbd> flip <kbd>→</kbd> next <kbd>←</kbd> prev
      </div>
    </div>
  );
}

/* ── Flashcards page ─────────────────────────────────────────────────────────── */

function FlashcardsPage({ user, onNavigate, onUsageUpdate, toast }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [flashcards, setFlashcards] = useState(null);
  const [error, setError] = useState('');
  const [studyMode, setStudyMode] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileRef = useRef();

  async function handleCopyCards() {
    if (!flashcards) return;
    const text = flashcards.map((c, i) => `Q${i + 1}: ${c.question}\nA: ${c.answer}`).join('\n\n');
    if (await copyText(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.show('Flashcards copied', 'success');
    }
  }

  function handleFile(f) {
    if (!f) return;
    setFile(f);
    if (!name) setName(f.name.replace(/\.[^/.]+$/, ''));
    setError('');
    setFlashcards(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('token', user.token);
      fd.append('name', name || file.name);
      const data = await api.upload('/api/generate-competitive-flashcards', fd);
      setFlashcards(data.flashcards);
      onUsageUpdate(data.daily_used);
      toast.show(`${data.count} flashcards generated`, 'success');
    } catch (err) {
      setError(err.message);
      toast.show(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  if (studyMode && flashcards) {
    return <StudyMode cards={flashcards} onExit={() => setStudyMode(false)} />;
  }

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <button className="back-btn" onClick={() => onNavigate('dashboard')}>
            <Icon.ArrowLeft width={13} height={13} /> Back
          </button>
          <div>
            <h1 className="page-title">Flashcards</h1>
            <p className="page-sub">Flip cards for quick recall.</p>
          </div>
        </div>

        <div className="upload-card" style={{ maxWidth: 460, marginBottom: 28 }}>
          <h2 className="card-title">Upload</h2>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div
              className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
            >
              <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.bmp,.gif,.pdf"
                onChange={e => handleFile(e.target.files[0])} style={{ display: 'none' }} />
              {file ? (
                <div className="drop-zone-file">
                  <div className="drop-zone-file-icon"><Icon.File width={22} height={22} /></div>
                  <p className="drop-zone-filename">{file.name}</p>
                  <p className="drop-zone-filesize">{(file.size / 1024).toFixed(0)} KB</p>
                </div>
              ) : (
                <>
                  <div className="drop-zone-icon"><Icon.Upload width={22} height={22} /></div>
                  <p className="drop-zone-text">Drop image or PDF</p>
                  <p className="drop-zone-sub">JPG, PNG, PDF · max 25 MB</p>
                </>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Name <span className="form-label-opt">(optional)</span></label>
              <input className="input" type="text" placeholder="Chemistry Chapter 5"
                value={name} onChange={e => setName(e.target.value)} />
            </div>

            {error && <div className="form-error">{error}</div>}

            <button className="btn btn-primary btn-full" type="submit"
              disabled={!file || loading || user.daily_used >= user.daily_limit}>
              {loading ? <><Spinner size={14} /> Generating…</> : 'Generate flashcards'}
            </button>

            {user.daily_used >= user.daily_limit && (
              <p className="limit-notice">Daily limit reached.</p>
            )}
          </form>
        </div>

        {loading && (
          <div className="result-placeholder">
            <Spinner size={24} />
            <p>Generating…</p>
          </div>
        )}

        {flashcards && (
          <>
            <div className="cards-header">
              <h2 className="cards-title">{flashcards.length} flashcards</h2>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-secondary btn-sm" onClick={handleCopyCards}>
                  {copied ? <><Icon.Check width={12} height={12} /> Copied</> : 'Copy all'}
                </button>
                <button className="btn btn-primary" onClick={() => setStudyMode(true)}>
                  <Icon.Play width={12} height={12} /> Study mode
                </button>
              </div>
            </div>
            <div className="cards-grid">
              {flashcards.map((c, i) => <FlipCard key={i} index={i} question={c.question} answer={c.answer} />)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── History ────────────────────────────────────────────────────────────────── */

function downloadNotesPDF(entry) {
  const html = marked.parse(entry.notes || '');
  const win = window.open('', '_blank');
  win.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${entry.name || entry.filename}</title>
  <style>
    body{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:0 24px;color:#1a1a1a;line-height:1.75;}
    h1,h2,h3{color:#1a1a1a;margin-top:1.5em;}
    h1{font-size:1.8em;border-bottom:2px solid #e11d48;padding-bottom:8px;}
    code{background:#f4f4f4;padding:2px 6px;border-radius:4px;font-size:.88em;font-family:monospace;}
    pre{background:#f4f4f4;padding:16px;border-radius:8px;overflow-x:auto;}
    pre code{background:none;padding:0;}
    blockquote{border-left:4px solid #e11d48;margin:0;padding-left:16px;color:#555;}
    table{border-collapse:collapse;width:100%;}
    td,th{border:1px solid #ddd;padding:8px 12px;}
    th{background:#f9f9f9;}
    @media print{body{margin:0;}}
  </style>
</head>
<body>
  <h1>${entry.name || entry.filename}</h1>
  ${html}
  <script>window.onload=()=>{window.print();}<\/script>
</body>
</html>`);
  win.document.close();
}

function HistoryItem({ entry, compact, expanded, onToggle, user, onRename }) {
  const isNotes = entry.type === 'notes' || entry.type === 'btech_notes';
  const typeLabel = isNotes ? 'NOTES' : 'CARDS';
  const badgeClass = isNotes ? 'badge-notes' : 'badge-cards';
  const [renaming, setRenaming] = useState(false);
  const [nameVal, setNameVal] = useState(entry.name || entry.filename);
  const inputRef = useRef();

  useEffect(() => { if (renaming) inputRef.current?.focus(); }, [renaming]);

  async function submitRename() {
    const trimmed = nameVal.trim();
    if (!trimmed || trimmed === (entry.name || entry.filename)) { setRenaming(false); return; }
    try {
      await api.post('/api/rename-history', { token: user.token, id: entry.id, name: trimmed });
      onRename(entry.id, trimmed);
    } catch { setNameVal(entry.name || entry.filename); }
    setRenaming(false);
  }

  if (compact) {
    return (
      <div className="history-item clickable" onClick={!renaming ? () => onRename?.('open', entry) : undefined}>
        <span className={`badge ${badgeClass}`}>{typeLabel}</span>
        {renaming ? (
          <input
            ref={inputRef}
            className="rename-input"
            value={nameVal}
            onChange={e => setNameVal(e.target.value)}
            onBlur={submitRename}
            onKeyDown={e => { if (e.key === 'Enter') submitRename(); if (e.key === 'Escape') { setNameVal(entry.name || entry.filename); setRenaming(false); } }}
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <span className="history-name">{entry.name || entry.filename}</span>
        )}
        <span className="history-date">{formatDate(entry.created_at)}</span>
        {user && (
          <button className="icon-btn" title="Rename" onClick={e => { e.stopPropagation(); setRenaming(true); }}>
            <Icon.Pencil />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`history-item expandable ${expanded ? 'expanded' : ''}`}>
      <div className="history-item-header" onClick={!renaming ? onToggle : undefined} style={{ cursor: renaming ? 'default' : 'pointer' }}>
        <span className={`badge ${badgeClass}`}>{typeLabel}</span>
        {renaming ? (
          <input
            ref={inputRef}
            className="rename-input"
            value={nameVal}
            onChange={e => setNameVal(e.target.value)}
            onBlur={submitRename}
            onKeyDown={e => { if (e.key === 'Enter') submitRename(); if (e.key === 'Escape') { setNameVal(entry.name || entry.filename); setRenaming(false); } }}
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <span className="history-name">{entry.name || entry.filename}</span>
        )}
        <span className="history-date">{formatDate(entry.created_at)}</span>
        <button className="icon-btn" title="Rename" onClick={e => { e.stopPropagation(); setRenaming(true); }}>
          <Icon.Pencil />
        </button>
        <span className="history-chevron">{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div className="history-content">
          {isNotes && entry.notes && (
            <>
              <div className="history-actions">
                <button className="btn-secondary btn-sm" onClick={() => downloadNotesPDF(entry)}>
                  <Icon.Download /> Download PDF
                </button>
              </div>
              <MarkdownBody content={entry.notes} />
            </>
          )}
          {entry.type === 'competitive_flashcards' && entry.flashcards && (
            <div className="cards-grid" style={{ marginTop: 10 }}>
              {entry.flashcards.map((c, i) => <FlipCard key={i} index={i} question={c.question} answer={c.answer} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function HistoryPage({ user, onNavigate, toast }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    api.get(`/api/history?token=${user.token}`)
      .then(d => setHistory(d.history))
      .catch(() => toast.show('Failed to load history', 'error'))
      .finally(() => setLoading(false));
  }, [user.token]);

  function handleRename(id, newName) {
    setHistory(h => h.map(e => e.id === id ? { ...e, name: newName } : e));
  }

  return (
    <div className="page">
      <div className="container">
        <div className="page-header">
          <button className="back-btn" onClick={() => onNavigate('dashboard')}>
            <Icon.ArrowLeft width={13} height={13} /> Back
          </button>
          <div>
            <h1 className="page-title">History</h1>
            <p className="page-sub">{loading ? '' : `${history.length} generation${history.length !== 1 ? 's' : ''}`}</p>
          </div>
        </div>

        {loading ? (
          <div className="loading-row"><Spinner /> Loading…</div>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <Icon.Archive width={22} height={22} />
            <p>No history yet.</p>
          </div>
        ) : (
          <div className="history-list">
            {history.map(entry => (
              <HistoryItem key={entry.id} entry={entry}
                expanded={expanded === entry.id}
                onToggle={() => setExpanded(expanded === entry.id ? null : entry.id)}
                user={user} onRename={handleRename} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Root App ────────────────────────────────────────────────────────────────── */

export default function App() {
  const [view, setView] = useState('loading');
  const [user, setUser] = useState(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const toast = useToast();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const username = params.get('username');
    const authError = params.get('auth_error');

    if (token && username) {
      window.history.replaceState({}, '', window.location.pathname);
      localStorage.setItem('bn_token', token);
      localStorage.setItem('bn_username', username);
      api.get(`/api/usage?token=${token}`)
        .then(data => {
          setUser({ token, username: data.username, daily_used: data.daily_used, daily_limit: data.daily_limit });
          setView('dashboard');
        })
        .catch(() => setView('auth'));
      return;
    }

    if (authError) {
      window.history.replaceState({}, '', window.location.pathname);
      toast.show(`Google sign-in failed: ${authError.replace(/_/g, ' ')}`, 'error');
      setView('auth');
      return;
    }

    const savedToken = localStorage.getItem('bn_token');
    const savedUsername = localStorage.getItem('bn_username');
    if (savedToken && savedUsername) {
      api.get(`/api/usage?token=${savedToken}`)
        .then(data => {
          setUser({ token: savedToken, username: data.username, daily_used: data.daily_used, daily_limit: data.daily_limit });
          setView('dashboard');
        })
        .catch(() => {
          localStorage.removeItem('bn_token');
          localStorage.removeItem('bn_username');
          setView('landing');
        });
    } else {
      setView('landing');
    }
  }, []);

  function handleLogin(data) {
    localStorage.setItem('bn_token', data.token);
    localStorage.setItem('bn_username', data.username);
    setUser({ token: data.token, username: data.username, daily_used: data.daily_used ?? 0, daily_limit: data.daily_limit ?? 2 });
    setView('dashboard');
    toast.show(`Welcome, ${displayName(data.username)}`, 'success');
  }

  function handleLogout() {
    if (user) api.post('/api/logout', { token: user.token }).catch(() => {});
    localStorage.removeItem('bn_token');
    localStorage.removeItem('bn_username');
    setUser(null);
    setView('landing');
  }

  function handleNavigate(v) {
    if (v === 'logout') { handleLogout(); return; }
    setView(v);
  }

  function handleUsageUpdate(daily_used) {
    setUser(u => u ? { ...u, daily_used } : u);
  }

  if (view === 'loading') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: 'var(--c-text-3)' }}>
        <Spinner size={20} />
      </div>
    );
  }

  return (
    <>
      <ToastStack toasts={toast.toasts} />
      {feedbackOpen && user && <FeedbackModal user={user} onClose={() => setFeedbackOpen(false)} toast={toast} />}
      {view !== 'auth' && view !== 'landing' && user && <Header user={user} onNavigate={handleNavigate} view={view} onFeedback={() => setFeedbackOpen(true)} />}
      <main className="main-content">
        {view === 'landing' && <LandingPage onGetStarted={() => setView('auth')} />}
        {view === 'auth' && <AuthPage onLogin={handleLogin} onBack={() => setView('landing')} />}
        {view === 'dashboard' && user && <Dashboard user={user} onNavigate={handleNavigate} />}
        {view === 'notes' && user && <NotesPage user={user} onNavigate={handleNavigate} onUsageUpdate={handleUsageUpdate} toast={toast} />}
        {view === 'flashcards' && user && <FlashcardsPage user={user} onNavigate={handleNavigate} onUsageUpdate={handleUsageUpdate} toast={toast} />}
        {view === 'history' && user && <HistoryPage user={user} onNavigate={handleNavigate} toast={toast} />}
      </main>
    </>
  );
}
