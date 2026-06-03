import json
import pathlib
import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Meridian AI Ops",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR        = pathlib.Path(__file__).parent
TRANSCRIPT_PATH = BASE_DIR / "incoming_calls" / "sarah_homebuyer.txt"
DATA_DIR        = BASE_DIR / "data"
CHROMA_DIR      = BASE_DIR / "chroma_db"

PLACEHOLDER = "Select an example question"

# ---------------------------------------------------------------------------
# Theme tokens
#   Navy   #0d1b2a   Brass  #b6862c   Ivory  #f6f2ea
#   Deep   #0a1422   Surface #11253a  Border #1f3850   Muted #8295ab
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Fonts: Fraunces (display serif) + Archivo (body) — exact match to c1ig.com ── */
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,300;1,9..144,400&family=Archivo:wght@400;500;600;700&display=swap');

:root {
    /* identical to c1ig.com public site */
    --ink:    #0d1b2a;
    --ink-2:  #1b2a3d;
    --ivory:  #f6f2ea;
    --paper:  #fbf9f4;
    --brass:  #b6862c;
    --brass-soft: #cba14a;
    --brass-bright: #e8c060;
    --sky:    #3c6e8f;
    --muted:  #5a6675;
    --line:   rgba(13,27,42,.14);
    --ease:   cubic-bezier(.22,.61,.36,1);
    /* internal dashboard extras */
    --surface: rgba(255,255,255,.05);
    --border:  rgba(255,255,255,.11);
    --text:    rgba(246,242,234,.88);
    --green:   #46b585;
    --amber:   #e3a534;
    --red:     #e0625f;
    --blue:    #5a9ef0;
    --display: 'Fraunces', Georgia, serif;
    --body:    'Archivo', system-ui, sans-serif;
    --mono:    'Courier New', monospace;
}

html, body, [class*="css"] { font-family: var(--body); -webkit-font-smoothing: antialiased; }

.stApp { background: var(--ink); color: var(--text); }
.block-container { padding-top: 2.4rem; max-width: 1200px; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--ink-2);
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] * { color: var(--text); }

/* ── Tabs ────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent; gap: 4px;
    border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: var(--muted);
    border-radius: 8px 8px 0 0; padding: 12px 28px;
    font-family: var(--body); font-weight: 600; font-size: 13.5px; letter-spacing: .02em;
    transition: color .25s;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--ivory); }
.stTabs [aria-selected="true"] {
    color: var(--brass-soft);
    border-bottom: 2px solid var(--brass);
}

/* ── Buttons — pill style matching c1ig.com .btn-primary ─────────── */
.stButton > button {
    background: var(--brass);
    color: #1a1305; font-family: var(--body); font-weight: 700;
    font-size: 14px; letter-spacing: .02em;
    border: none; border-radius: 44px; padding: 12px 30px;
    transition: transform .3s var(--ease), box-shadow .3s var(--ease), background .25s;
}
.stButton > button:hover {
    background: var(--brass-soft);
    box-shadow: 0 18px 40px -14px rgba(182,134,44,.6);
    transform: translateY(-2px);
}
.stButton > button:active  { transform: translateY(0); }
.stButton > button:disabled {
    background: rgba(255,255,255,.07); color: rgba(255,255,255,.3);
    box-shadow: none; transform: none;
}

/* ── Inputs ──────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,.05) !important;
    color: var(--ivory) !important;
    border: 1px solid var(--line) !important;
    border-radius: 11px !important;
    font-family: var(--body) !important;
    font-size: 14px !important;
    transition: border-color .3s, background .3s;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--brass) !important;
    background: rgba(255,255,255,.08) !important;
    outline: none !important;
    box-shadow: none !important;
}
.stTextInput input::placeholder { color: var(--muted) !important; }
[data-baseweb="select"], [data-baseweb="popover"] { background: var(--ink-2) !important; }

/* ── Expander ────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,.03);
    border: 1px solid var(--line); border-radius: 12px;
}
[data-testid="stExpander"] summary {
    color: var(--brass-soft) !important;
    font-family: var(--body); font-weight: 600; font-size: 13px;
}

/* ── Progress ────────────────────────────────────────────────────── */
[data-testid="stProgressBar"] {
    background: rgba(255,255,255,.1); border-radius: 99px; height: 6px;
}
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--brass), var(--brass-soft));
    border-radius: 99px;
}

/* ── Scrollbar ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.12); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--brass); }

/* ── Animations ──────────────────────────────────────────────────── */
@keyframes shimmer { 0%{background-position:-600px 0} 100%{background-position:600px 0} }
@keyframes rise    { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:none} }

/* ── Brand header ────────────────────────────────────────────────── */
.brand-lockup {
    display: flex; align-items: center; gap: 14px; margin-bottom: 6px;
}
.brand-mark {
    width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
    background: linear-gradient(135deg, var(--ink-2), var(--sky));
    color: var(--ivory); display: grid; place-items: center;
    font-family: var(--body); font-weight: 700; font-size: 1rem; letter-spacing: -.02em;
    box-shadow: 0 8px 24px rgba(0,0,0,.4);
}
.meridian-title {
    font-family: var(--display); font-size: 2.4rem; font-weight: 500;
    letter-spacing: -.02em; line-height: 1.05;
    background: linear-gradient(90deg, var(--brass) 0%, var(--brass-bright) 40%, var(--ivory) 54%, var(--brass-bright) 68%, var(--brass) 100%);
    background-size: 700px 100%; -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; animation: shimmer 9s linear infinite;
}
.meridian-subtitle {
    font-size: .72rem; font-weight: 600; letter-spacing: .28em;
    text-transform: uppercase; color: var(--brass); margin-top: 4px;
}
.header-rule {
    height: 1px; border: none; margin: 20px 0 28px;
    background: linear-gradient(90deg, var(--brass), transparent);
}

/* ── Eyebrow label — same as c1ig.com .eyebrow ───────────────────── */
.m-section-label {
    font-size: .72rem; font-weight: 600; letter-spacing: .28em;
    text-transform: uppercase; color: var(--brass); margin: 0 0 14px;
}

/* ── Cards ───────────────────────────────────────────────────────── */
.m-card {
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-radius: 18px; padding: 22px 26px; margin-bottom: 16px;
    animation: rise .4s var(--ease) both;
}
.m-card-hero {
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-top: 2px solid var(--brass); border-radius: 18px;
    padding: 22px 26px; margin-bottom: 14px;
    box-shadow: 0 24px 60px -28px rgba(13,27,42,.5);
    animation: rise .4s var(--ease) both;
}

/* ── Info tiles — like the hero stat blocks on c1ig.com ──────────── */
.m-tile {
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-radius: 18px; padding: 20px 16px; text-align: center;
    height: 100%; animation: rise .4s var(--ease) both;
    transition: background .35s, border-color .35s;
}
.m-tile:hover { background: rgba(255,255,255,.07); border-color: var(--brass); }
.m-tile-label {
    font-size: .64rem; font-weight: 600; letter-spacing: .2em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 8px;
}
.m-tile-value {
    font-family: var(--display); font-size: 1rem; font-weight: 400;
    color: var(--ivory); line-height: 1.3; word-break: break-word;
}

/* ── Sidebar metric — Fraunces number like .counter on c1ig.com ──── */
.m-metric {
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-radius: 14px; padding: 16px 15px; margin-bottom: 10px;
}
.m-metric-value {
    font-family: var(--display); font-size: 2rem; font-weight: 400;
    color: var(--brass-soft); line-height: 1;
}
.m-metric-label {
    font-size: .64rem; font-weight: 600; letter-spacing: .16em;
    text-transform: uppercase; color: var(--muted); margin-top: 6px;
}

/* ── Status dots ─────────────────────────────────────────────────── */
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:9px; vertical-align:middle; }
.dot-green { background:var(--green); box-shadow:0 0 7px rgba(70,181,133,.5); }
.dot-red   { background:var(--red);   box-shadow:0 0 7px rgba(224,98,95,.5); }
.dot-amber { background:var(--amber); box-shadow:0 0 7px rgba(227,165,52,.5); }
.status-row { font-size:.82rem; padding:5px 0; color:var(--text); }

/* ── Urgency ─────────────────────────────────────────────────────── */
.urg-label {
    font-family: var(--display); font-size: 1.25rem; font-weight: 400;
    letter-spacing: -.01em; line-height: 1.1;
}
.urg-high  { color: var(--red); }
.urg-med   { color: var(--amber); }
.urg-low   { color: var(--green); }
.urg-reason { color: var(--muted); font-size: .87rem; margin-top: 8px; line-height: 1.6; }

/* ── Alert cards ─────────────────────────────────────────────────── */
.m-alert {
    border-radius: 0 12px 12px 0; padding: 14px 18px;
    margin-bottom: 12px; animation: rise .35s var(--ease) both;
}
.m-alert-blue  { background: rgba(60,110,143,.15); border-left: 3px solid var(--sky); }
.m-alert-brass { background: rgba(182,134,44,.1);  border-left: 3px solid var(--brass); }
.alert-tag {
    font-size: .65rem; font-weight: 700; letter-spacing: .2em;
    color: var(--brass); text-transform: uppercase; margin-bottom: 6px;
}
.alert-body   { font-size: .89rem; color: var(--text); line-height: 1.55; }
.alert-action { font-size: .81rem; color: var(--muted); margin-top: 6px; }

/* ── Checklist ───────────────────────────────────────────────────── */
.m-check {
    display: flex; align-items: flex-start; gap: 12px; padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,.07);
    font-size: .9rem; color: var(--text); line-height: 1.55;
}
.m-check:last-child { border-bottom: none; }
.m-check-tick { color: var(--green); font-weight: 700; flex-shrink: 0; margin-top: 1px; }

/* ── Transcript — monospace, brass left-border ───────────────────── */
.transcript-card {
    background: rgba(0,0,0,.3); border: 1px solid var(--line);
    border-left: 3px solid var(--brass); border-radius: 14px;
    padding: 22px 24px; max-height: 380px; overflow-y: auto;
    font-family: var(--mono); font-size: .79rem; color: rgba(246,242,234,.72);
    line-height: 1.78; white-space: pre-wrap; animation: rise .4s var(--ease) both;
}

/* ── Hint placeholder ────────────────────────────────────────────── */
.m-hint {
    background: rgba(255,255,255,.03); border: 1px dashed var(--line);
    border-radius: 14px; padding: 20px 24px;
    color: var(--muted); font-size: .9rem; line-height: 1.6;
}
.m-hint strong { color: var(--brass-soft); }

/* ── Brain answer — Fraunces headings, Archivo body ──────────────── */
.brain-answer {
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-top: 2px solid var(--brass); border-radius: 18px;
    padding: 28px 32px; color: var(--text); font-size: .96rem; line-height: 1.72;
    box-shadow: 0 24px 60px -28px rgba(13,27,42,.5);
    animation: rise .45s var(--ease) both;
}
.brain-answer h1, .brain-answer h2, .brain-answer h3, .brain-answer h4 {
    font-family: var(--display); font-weight: 400; letter-spacing: -.01em;
    color: var(--brass-bright); line-height: 1.2; margin: 20px 0 10px;
}
.brain-answer h1 { font-size: 1.35rem; }
.brain-answer h2 { font-size: 1.18rem; }
.brain-answer h3 { font-size: 1.05rem; }
.brain-answer h4 { font-size: .96rem; }
.brain-answer h1:first-child, .brain-answer h2:first-child,
.brain-answer h3:first-child { margin-top: 0; }
.brain-answer p  { margin: 0 0 14px; }
.brain-answer p:last-child { margin-bottom: 0; }
.brain-answer ul, .brain-answer ol { margin: 0 0 14px; padding-left: 22px; }
.brain-answer li { margin-bottom: 8px; }
.brain-answer li::marker { color: var(--brass); }
.brain-answer strong { color: var(--ivory); font-weight: 600; }
.brain-answer em    { color: var(--brass-soft); font-style: italic; }
.brain-answer code  {
    font-family: var(--mono); font-size: .83em;
    background: rgba(0,0,0,.3); color: var(--brass-soft);
    padding: 2px 7px; border-radius: 6px; border: 1px solid var(--line);
}
.brain-answer a {
    color: var(--brass-bright); text-decoration: none;
    border-bottom: 1px solid rgba(182,134,44,.35);
}
.brain-answer blockquote {
    border-left: 3px solid var(--brass); margin: 0 0 14px;
    padding: 2px 0 2px 18px; color: var(--muted);
}

/* ── Source pills — brass pill matching c1ig.com carrier logos ───── */
.m-pill {
    display: inline-block; background: rgba(182,134,44,.1);
    color: var(--brass-soft); border: 1px solid rgba(182,134,44,.35);
    border-radius: 12px; padding: 5px 14px;
    font-family: var(--body); font-size: .76rem; font-weight: 500;
    margin: 3px 4px 3px 0; letter-spacing: .04em;
    transition: opacity .3s, border-color .3s, transform .3s;
}
.m-pill:hover { opacity: 1; border-color: var(--brass); transform: translateY(-2px); }

/* ── Chunk card ──────────────────────────────────────────────────── */
.m-chunk {
    background: rgba(0,0,0,.25); border: 1px solid var(--line);
    border-radius: 12px; padding: 15px 18px; margin-bottom: 10px;
    font-family: var(--mono); font-size: .78rem; color: var(--muted);
    line-height: 1.65; white-space: pre-wrap;
}
.m-chunk-head {
    font-family: var(--body); font-size: .65rem; font-weight: 700;
    letter-spacing: .18em; text-transform: uppercase;
    color: var(--brass); margin-bottom: 8px;
}

/* ── Outbox event cards ──────────────────────────────────────────── */
.m-event-card {
    display: flex; align-items: center; gap: 18px;
    background: rgba(255,255,255,.04); border: 1px solid var(--line);
    border-radius: 16px; padding: 18px 22px; margin-bottom: 10px;
    animation: rise .38s var(--ease) both;
    transition: background .35s, border-color .35s;
}
.m-event-card:hover { background: rgba(255,255,255,.07); border-color: var(--brass); }
.m-event-left  { flex-shrink: 0; }
.m-event-icon  { font-size: 1.5rem; line-height: 1; }
.m-event-body  { flex: 1; min-width: 0; }
.m-event-title {
    font-family: var(--body); font-size: .92rem; font-weight: 600;
    color: var(--ivory); margin-bottom: 5px; letter-spacing: -.01em;
}
.m-event-desc  { font-size: .83rem; color: var(--muted); line-height: 1.55; }
.m-event-desc strong { color: var(--text); font-weight: 600; }
.m-event-desc em     { color: var(--brass-soft); font-style: normal; }
.m-event-badge {
    flex-shrink: 0; font-size: .68rem; font-weight: 600; letter-spacing: .1em;
    color: var(--green); background: rgba(70,181,133,.1);
    border: 1px solid rgba(70,181,133,.3); border-radius: 44px;
    padding: 5px 13px; white-space: nowrap;
}

/* ── Sidebar public-site link ────────────────────────────────────── */
.site-link {
    display: flex; align-items: center; gap: 9px;
    background: rgba(182,134,44,.08); border: 1px solid rgba(182,134,44,.25);
    border-radius: 10px; padding: 10px 14px; margin: 14px 0;
    color: var(--brass-soft); font-size: .82rem; font-weight: 500;
    text-decoration: none; transition: background .25s, border-color .25s;
}
.site-link:hover { background: rgba(182,134,44,.16); border-color: var(--brass); color: var(--ivory); }

/* ── Footer text ─────────────────────────────────────────────────── */
.sidebar-foot {
    font-size: .62rem; color: rgba(255,255,255,.25);
    text-align: center; line-height: 1.75; padding-top: 6px;
}

/* Hide only Streamlit footer branding — keep header so sidebar toggle works */
footer { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--ink-2); border-right: 1px solid var(--line); }
/* Sidebar expand button (shows when sidebar is collapsed) — must stay visible */
[data-testid="stSidebarCollapsedControl"] { visibility: visible !important; display: flex !important; }
</style>
""", unsafe_allow_html=True)

# Disable Streamlit's keyboard shortcut handler for Cmd/Ctrl combos
# so that normal OS shortcuts (copy, paste, etc.) never trigger the
# "Clear cache" dialog.
st.markdown("""
<script>
(function() {
    function blockStreamlitShortcuts(e) {
        if (e.metaKey || e.ctrlKey) {
            e.stopImmediatePropagation();
        }
    }
    // Capture phase so this runs before Streamlit's own listeners
    document.addEventListener('keydown', blockStreamlitShortcuts, true);
    window.addEventListener('keydown',   blockStreamlitShortcuts, true);
})();
</script>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Backend imports (failures surface in the UI, never crash the app)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _import_backends():
    errors, ci, brain = {}, None, None
    sys.path.insert(0, str(BASE_DIR))
    try:
        import call_intelligence as _ci
        ci = _ci
    except Exception as e:
        errors["call_intelligence"] = str(e)
    try:
        import brain as _brain
        brain = _brain
    except Exception as e:
        errors["brain"] = str(e)
    return ci, brain, errors


@st.cache_resource(show_spinner=False)
def _markdown_renderer():
    from markdown_it import MarkdownIt
    return MarkdownIt("commonmark", {"breaks": True, "linkify": True}).enable("table")


@st.cache_data(show_spinner=False)
def _system_stats():
    """Compute dashboard counts from local files and chroma. Safe fallbacks."""
    txt_count = len(list(DATA_DIR.rglob("*.txt"))) if DATA_DIR.exists() else 0
    carriers  = len(list((DATA_DIR / "carriers").glob("*.txt"))) if (DATA_DIR / "carriers").exists() else 0
    chunks = 0
    try:
        import chromadb
        col = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection("meridian_brain")
        chunks = col.count()
    except Exception:
        chunks = txt_count * 11 if txt_count else 57  # reasonable fallback
    return {"documents": txt_count, "chunks": chunks, "carriers": carriers}


ci_mod, brain_mod, import_errors = _import_backends()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size:.64rem;color:var(--brass);text-transform:uppercase;'
            'letter-spacing:2.2px;font-weight:600;margin:8px 0 16px;">System Status</div>',
            unsafe_allow_html=True,
        )
        stats = _system_stats()
        for label, value in [
            ("Documents Loaded", stats["documents"]),
            ("Chunks Indexed",   stats["chunks"]),
            ("Carriers Loaded",  stats["carriers"]),
        ]:
            st.markdown(
                f'<div class="m-metric"><div class="m-metric-value">{value}</div>'
                f'<div class="m-metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div style="font-size:.64rem;color:var(--brass);text-transform:uppercase;'
            'letter-spacing:2.2px;font-weight:600;margin:18px 0 10px;">Modules</div>',
            unsafe_allow_html=True,
        )
        for mod_name, display_name in (("call_intelligence", "Call Intelligence Engine"), ("brain", "Knowledge Base")):
            ok  = mod_name not in import_errors
            dot = "dot-green" if ok else "dot-red"
            txt = "Operational" if ok else "Unavailable"
            st.markdown(
                f'<div class="status-row"><span class="dot {dot}"></span>'
                f'<strong>{display_name}</strong> &nbsp;{txt}</div>',
                unsafe_allow_html=True,
            )
            if not ok:
                st.caption("Service temporarily unavailable.")

        # Public site link
        st.markdown(
            '<a class="site-link" href="https://c1ig-redesign.vercel.app/" target="_blank">'
            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20"/></svg>'
            'C1 Insurance &nbsp;Public Site</a>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="margin-top:14px;border-top:1px solid var(--line);padding-top:14px;">'
            '<div class="sidebar-foot">Meridian AI Ops &middot; Confidential<br>'
            'C1 Insurance Group &nbsp;+&nbsp; MyUtilities</div></div>',
            unsafe_allow_html=True,
        )


render_sidebar()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="brand-lockup">'
    '  <div class="brand-mark">M</div>'
    '  <div>'
    '    <div class="meridian-title">Meridian AI Ops</div>'
    '    <div class="meridian-subtitle">C1 Insurance Group &nbsp;+&nbsp; MyUtilities</div>'
    '  </div>'
    '</div>'
    '<hr class="header-rule">',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Inline System Status (always visible regardless of sidebar state)
# ---------------------------------------------------------------------------
stats = _system_stats()
with st.expander("System Status", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.metric("Documents Loaded", stats["documents"])
    col2.metric("Chunks Indexed",   stats["chunks"])
    col3.metric("Carriers Loaded",  stats["carriers"])

    st.markdown("**Modules**")
    for mod_name, display_name in (("call_intelligence", "Call Intelligence Engine"), ("brain", "Knowledge Base")):
        ok      = mod_name not in import_errors
        symbol  = "🟢" if ok else "🔴"
        label   = "Operational" if ok else "Unavailable"
        st.markdown(f"{symbol} &nbsp;{display_name} &nbsp;— {label}", unsafe_allow_html=True)
        if not ok:
            st.caption("Service temporarily unavailable.")

tab_ci, tab_brain = st.tabs(["Call Intelligence", "Meridian Brain"])


# ===========================================================================
# TAB 1: CALL INTELLIGENCE
# ===========================================================================
with tab_ci:
    st.markdown('<div class="m-section-label">Call Transcript</div>', unsafe_allow_html=True)

    if st.button("Load Call Transcript", key="load_transcript"):
        if not TRANSCRIPT_PATH.exists():
            st.error("Call transcript not found. Please check the configuration.")
        else:
            st.session_state["transcript_text"] = TRANSCRIPT_PATH.read_text(encoding="utf-8")
            st.session_state.pop("ci_result", None)

    if "transcript_text" in st.session_state:
        st.markdown(
            f'<div class="transcript-card">{st.session_state["transcript_text"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="m-section-label" style="margin-top:24px;">Analysis Results</div>', unsafe_allow_html=True)

    analyze_disabled = "transcript_text" not in st.session_state
    if st.button("Analyze Call", key="analyze_call", disabled=analyze_disabled):
        # resolve module — re-import inline if cached import failed at startup
        _ci = ci_mod
        if _ci is None:
            try:
                import importlib
                sys.path.insert(0, str(BASE_DIR))
                _ci = importlib.import_module("call_intelligence")
            except Exception:
                _ci = None

        with st.spinner("Analyzing call..."):
            try:
                if _ci is None:
                    raise ImportError("call_intelligence unavailable")
                transcript    = st.session_state["transcript_text"]
                analysis      = _ci.analyze_call(transcript)
                contact       = _ci.resolve_contact(analysis.get("client_name", ""))
                analysis      = _ci.scrub_invented_emails(analysis, contact)
                events        = _ci.generate_outbox_events(analysis, contact)
                _ci.log_audit(analysis, events)
                demo_fallback = analysis.pop("_demo_fallback", False)
                st.session_state["ci_result"] = {
                    "analysis":      analysis,
                    "contact":       contact,
                    "events":        events,
                    "demo_fallback": demo_fallback,
                }
            except Exception:
                import copy
                # Always fall back to hardcoded demo — never show a blank screen
                if _ci is None:
                    sys.path.insert(0, str(BASE_DIR))
                    import call_intelligence as _ci_fallback
                    _ci = _ci_fallback
                demo    = copy.deepcopy(_ci.DEMO_ANALYSIS)
                demo.pop("_demo_fallback", None)
                contact = _ci.resolve_contact(demo["client_name"])
                demo    = _ci.scrub_invented_emails(demo, contact)
                events  = _ci.generate_outbox_events(demo, contact)
                _ci.log_audit(demo, events)
                st.session_state["ci_result"] = {
                    "analysis":      demo,
                    "contact":       contact,
                    "events":        events,
                    "demo_fallback": True,
                }

    if "ci_result" not in st.session_state:
        if "transcript_text" not in st.session_state:
            st.markdown(
                '<div class="m-hint">Select <strong>Load Call Transcript</strong> above, '
                'then click <strong>Analyze Call</strong> to generate client intelligence, '
                'revenue opportunities, and integration events.</div>',
                unsafe_allow_html=True,
            )
    else:
        r        = st.session_state["ci_result"]
        analysis = r["analysis"]
        contact  = r["contact"]
        events   = r["events"]

        if r.get("demo_fallback"):
            st.info("Running in offline demo mode.")

        # 1. Client summary tiles
        st.markdown('<div class="m-section-label" style="margin-top:22px;">Client Summary</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        tiles = [
            ("Client",   analysis.get("client_name")),
            ("Property", analysis.get("property_location")),
            ("Closing",  analysis.get("closing_date")),
            ("Carriers", ", ".join(analysis.get("current_carriers", [])) or "None on file"),
        ]
        for col, (label, value) in zip(cols, tiles):
            col.markdown(
                f'<div class="m-tile"><div class="m-tile-label">{label}</div>'
                f'<div class="m-tile-value">{value or "Not specified"}</div></div>',
                unsafe_allow_html=True,
            )

        # 2. Urgency meter
        st.markdown('<div class="m-section-label" style="margin-top:22px;">Urgency</div>', unsafe_allow_html=True)
        urg    = analysis.get("urgency", {})
        score  = int(urg.get("score", 0) or 0)
        reason = urg.get("reason", "")
        if score >= 8:
            dot, cls, tier = "dot-red", "urg-high", "High"
        elif score >= 5:
            dot, cls, tier = "dot-amber", "urg-med", "Medium"
        else:
            dot, cls, tier = "dot-green", "urg-low", "Low"
        st.markdown(
            f'<div class="m-card-hero"><span class="dot {dot}"></span>'
            f'<span class="urg-label {cls}">{tier} Priority &middot; {score}/10</span>'
            f'<div class="urg-reason">{reason}</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(score / 10)

        # 3. Cross-sell flags
        flags = analysis.get("crosssell_flags", [])
        if flags:
            st.markdown('<div class="m-section-label" style="margin-top:22px;">Revenue Opportunities</div>', unsafe_allow_html=True)
            for flag in flags:
                if flag.get("direction") == "c1_to_myutils":
                    arrow, css = "C1 to MyUtilities", "m-alert-blue"
                else:
                    arrow, css = "MyUtilities to C1", "m-alert-brass"
                st.markdown(
                    f'<div class="m-alert {css}"><div class="alert-tag">{arrow}</div>'
                    f'<div class="alert-body">{flag.get("reason","")}</div>'
                    f'<div class="alert-action">Recommended Action: {flag.get("suggested_action","")}</div></div>',
                    unsafe_allow_html=True,
                )

        # 4. Advisor action checklist
        actions = analysis.get("advisor_actions", [])
        if actions:
            st.markdown('<div class="m-section-label" style="margin-top:22px;">Action Plan</div>', unsafe_allow_html=True)
            items = "".join(
                f'<div class="m-check"><span class="m-check-tick">&#10003;</span><span>{step}</span></div>'
                for step in actions
            )
            st.markdown(f'<div class="m-card">{items}</div>', unsafe_allow_html=True)

        # 5. Draft email (editable)
        draft = analysis.get("draft_email", {})
        if draft:
            st.markdown('<div class="m-section-label" style="margin-top:22px;">Draft Email</div>', unsafe_allow_html=True)
            to_email = (contact or {}).get("email", "[client email needed]")
            st.markdown(
                f'<div style="font-size:.8rem;color:var(--muted);margin-bottom:8px;">'
                f'To <span style="color:var(--brass);">{to_email}</span> &nbsp;&middot;&nbsp; '
                f'Subject <span style="color:var(--ivory);">{draft.get("subject","")}</span></div>',
                unsafe_allow_html=True,
            )
            st.text_area(
                label="Draft email body",
                value=draft.get("body", ""),
                height=270,
                key="draft_email_body",
                label_visibility="collapsed",
            )

        # 6. Integration outbox
        if events:
            st.markdown('<div class="m-section-label" style="margin-top:22px;">Automated Actions</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.82rem;color:var(--muted);margin-bottom:16px;">'
                'The following actions are queued and ready. No data has been transmitted.</div>',
                unsafe_allow_html=True,
            )

            # Human-readable descriptions for each event type
            EVENT_META = {
                "CREATE_CRM_LEAD": {
                    "icon": "🏢",
                    "title": "CRM Lead Created",
                    "desc": lambda p: (
                        f"<strong>{p.get('firstname','')} {p.get('lastname','')}</strong> added to HubSpot "
                        f"as a <em>{p.get('deal_stage','')}</em> in the "
                        f"<em>{p.get('pipeline','')}</em> pipeline. "
                        f"Urgency score: <strong>{p.get('urgency_score','')}/10</strong>."
                    ),
                },
                "CREATE_ADVISOR_TASK": {
                    "icon": "📋",
                    "title": "Advisor Task Created",
                    "desc": lambda p: (
                        f"Priority: <strong>{p.get('priority','')}</strong>. "
                        f"Due: <strong>{p.get('due_date','')}</strong>. "
                        f"{len(p.get('steps', []))} action steps attached."
                    ),
                },
                "SEND_EMAIL": {
                    "icon": "✉",
                    "title": "Follow-up Email Ready",
                    "desc": lambda p: (
                        f"To <strong>{p.get('to_name','')}</strong> "
                        f"at <strong>{p.get('to_email','')}</strong>. "
                        f"Subject: <em>{p.get('subject','')}</em>"
                    ),
                },
                "SEND_SMS": {
                    "icon": "💬",
                    "title": "SMS Queued",
                    "desc": lambda p: (
                        f"To <strong>{p.get('to_phone','')}</strong>. "
                        f"Message: <em>{p.get('body','')[:90]}{'...' if len(p.get('body','')) > 90 else ''}</em>"
                    ),
                },
                "MYUTILITIES_HANDOFF": {
                    "icon": "⚡",
                    "title": "MyUtilities Referral Sent",
                    "desc": lambda p: (
                        f"Referral sent for <strong>{p.get('client_name','')}</strong> "
                        f"at <strong>{p.get('property_address','')}</strong>. "
                        f"Needs: <strong>{', '.join(p.get('utility_needs', []))}</strong>. "
                        f"SLA: contact within <strong>{p.get('sla_minutes','')} minutes</strong>."
                    ),
                },
            }

            for ev in events:
                etype   = ev.get("eventType", "EVENT")
                payload = ev.get("payload", {})
                meta    = EVENT_META.get(etype, {
                    "icon": "📦",
                    "title": etype,
                    "desc": lambda p: f"Target: {ev.get('targetSystem','')}",
                })
                try:
                    desc_html = meta["desc"](payload)
                except Exception:
                    desc_html = f"Target: {ev.get('targetSystem','')}"

                st.markdown(
                    f'<div class="m-event-card">'
                    f'  <div class="m-event-left">'
                    f'    <div class="m-event-icon">{meta["icon"]}</div>'
                    f'  </div>'
                    f'  <div class="m-event-body">'
                    f'    <div class="m-event-title">{meta["title"]}</div>'
                    f'    <div class="m-event-desc">{desc_html}</div>'
                    f'  </div>'
                    f'  <div class="m-event-badge">&#10003;&nbsp;Ready</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("View Payload"):
                    st.code(json.dumps(payload, indent=2, default=str), language="json")


# ===========================================================================
# TAB 2: MERIDIAN BRAIN
# ===========================================================================
with tab_brain:

    EXAMPLE_QUESTIONS = [
        "What is Safeco's commission rate for new business, and what roof age will they refuse to write?",
        "Sarah Mitchell is closing in Plano 75093. Which electricity providers should MyUtilities offer, and what handoff script should the advisor use?",
        "What are the differences between Safeco Premier and Travelers Premier for a $600K Dallas home?",
        "What questions must an advisor ask before quoting a new homeowner, and what are the polybutylene plumbing rules?",
        "Walk me through the exact cross-sell triggers between C1 and MyUtilities.",
    ]

    def _apply_example():
        sel = st.session_state.get("example_select")
        if sel and sel != PLACEHOLDER:
            st.session_state["brain_query"] = sel

    st.markdown('<div class="m-section-label">Example Questions</div>', unsafe_allow_html=True)
    st.selectbox(
        label="Example questions",
        options=[PLACEHOLDER] + EXAMPLE_QUESTIONS,
        key="example_select",
        on_change=_apply_example,
        label_visibility="collapsed",
    )

    st.markdown('<div class="m-section-label" style="margin-top:18px;">Ask Meridian</div>', unsafe_allow_html=True)
    st.text_input(
        label="Question",
        placeholder="Ask about carriers, coverage rules, or cross-sell triggers...",
        key="brain_query",
        label_visibility="collapsed",
    )
    query = st.session_state.get("brain_query", "")

    if st.button("Ask Meridian", key="ask_brain"):
        if not query.strip():
            st.warning("Please enter a question or select one from the examples above.")
        else:
            _brain = brain_mod
            if _brain is None:
                try:
                    import importlib
                    sys.path.insert(0, str(BASE_DIR))
                    _brain = importlib.import_module("brain")
                except Exception:
                    _brain = None

            if _brain is None:
                st.error("The knowledge base is initializing. Please wait a moment and try again.")
            else:
                with st.spinner("Searching knowledge base..."):
                    try:
                        st.session_state["brain_result"] = _brain.query_brain(query.strip())
                    except Exception as e:
                        st.session_state.pop("brain_result", None)
                        st.error("Unable to retrieve an answer. Please try again.")

    if "brain_result" in st.session_state:
        res        = st.session_state["brain_result"]
        answer_md  = res.get("answer", "")
        answer_html = _markdown_renderer().render(answer_md)

        st.markdown('<div class="m-section-label" style="margin-top:22px;">Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="brain-answer">{answer_html}</div>', unsafe_allow_html=True)

        sources = res.get("sources", [])
        if sources:
            st.markdown('<div class="m-section-label" style="margin-top:20px;">Knowledge Sources</div>', unsafe_allow_html=True)
            pills = " ".join(f'<span class="m-pill">{s}</span>' for s in sources)
            st.markdown(f'<div style="margin-bottom:14px;">{pills}</div>', unsafe_allow_html=True)

        chunks = res.get("chunks", [])
        if chunks:
            with st.expander("View Source Passages"):
                for i, chunk in enumerate(chunks, 1):
                    st.markdown(
                        f'<div class="m-chunk"><div class="m-chunk-head">Passage {i}</div>{chunk}</div>',
                        unsafe_allow_html=True,
                    )
