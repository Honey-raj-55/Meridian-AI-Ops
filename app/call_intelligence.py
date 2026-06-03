"""
call_intelligence.py  –  Meridian AI call analysis pipeline.

Stages:
  1. analyze_call()        – Gemini extracts structured intel from a transcript
  2. resolve_contact()     – CSV lookup for email / phone
  3. generate_outbox_events() – Mock integration event payloads (nothing is sent)
  4. log_audit()           – Persist everything to SQLite audit.db

Run:  python call_intelligence.py
"""

import csv
import json
import os
import pathlib
import re
import sqlite3
import textwrap
import unicodedata
import uuid
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Pull keys from Streamlit secrets when running on Streamlit Cloud
try:
    import streamlit as st
    for _k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "USE_LLM"):
        if _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = st.secrets[_k]
except Exception:
    pass

BASE_DIR     = pathlib.Path(__file__).parent
CONTACTS_CSV = BASE_DIR / "data" / "contacts.csv"
AUDIT_DB     = BASE_DIR / "audit.db"
GEMINI_MODEL = "gemini-2.5-flash"
USE_LLM      = os.getenv("USE_LLM", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Deterministic demo analysis (used when USE_LLM=false or Gemini fails)
# ---------------------------------------------------------------------------
DEMO_ANALYSIS = {
    "client_name":       "Sarah Mitchell",
    "property_location": "4817 Thornbury Drive, Plano, TX 75093",
    "closing_date":      "2026-06-12",
    "current_carriers":  ["State Farm"],
    "urgency": {
        "score":  9,
        "reason": "Client is closing on a new home in 9 days and needs proof of homeowners "
                  "insurance before closing. She explicitly stated she feels panicked and is "
                  "in a crunch.",
    },
    "coverage_interests": ["homeowners", "auto bundle"],
    "utility_needs":      ["electricity", "internet"],
    "crosssell_flags": [
        {
            "direction":        "c1_to_myutils",
            "reason":           "Client has not set up electricity or internet at the new "
                                "address and expressed confusion about Texas retail electricity "
                                "providers.",
            "suggested_action": "Warm-transfer or callback referral to MyUtilities within the "
                                "hour for electricity and internet setup at 4817 Thornbury Drive.",
        },
    ],
    "advisor_actions": [
        "Pull homeowners insurance quotes for 4817 Thornbury Drive, Plano TX 75093 "
        "($448,000 purchase price, 2019 roof, first-time buyer, no claims, golden retriever).",
        "Run bundled auto quotes with Safeco and Travelers to compare against current "
        "State Farm policy.",
        "Send all quotes to the client within 20 minutes.",
        "Check inspection report for Class 4 impact-resistant shingles "
        "(potential 8-12% discount).",
        "Submit MyUtilities referral for electricity and internet setup.",
        "Follow up with MyUtilities in 90 minutes to confirm client contact.",
        "Flag lender (Rocket Mortgage) in EZLynx for e-delivery of declarations page.",
        "Log realtor referral from Diane Kowalski, Keller Williams Plano, in HubSpot.",
    ],
    "draft_email": {
        "subject": "Your Home Insurance Quotes and Utility Setup for 4817 Thornbury Drive",
        "body": (
            "Hi Sarah,\n\n"
            "It was great speaking with you today! I completely understand the time pressure "
            "with your closing date on June 12th, and I want you to know we will have "
            "everything in place well before then.\n\n"
            "I am putting together homeowners insurance quotes for 4817 Thornbury Drive right "
            "now. I am also including options to bundle your auto insurance alongside the home "
            "policy. Bundling through a single carrier like Safeco or Travelers typically saves "
            "15 to 20 percent compared to keeping them separate, so it is worth a close look "
            "against your current State Farm rate.\n\n"
            "One quick note: if you can find the roof section in your inspection report, please "
            "let me know whether it lists Class 4 impact-resistant shingles. That detail could "
            "unlock an additional 8 to 12 percent discount.\n\n"
            "I have also referred you to our partners at MyUtilities, who will call you within "
            "the hour to get your electricity and internet set up at the new address. They "
            "compare all the retail providers for your zip code and handle the account setup "
            "for you at no charge.\n\n"
            "Expect the insurance quotes in your inbox shortly. Please do not hesitate to call "
            "or text me with any questions.\n\n"
            "Best regards,\n\n"
            "Marcus Webb\n"
            "C1 Insurance Group"
        ),
    },
    "_demo_fallback": False,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _gemini_client() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set in .env")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def _normalize_name(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = nfkd.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a possibly-wrapped Gemini response."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text.strip(), flags=re.MULTILINE)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in Gemini response:\n{text[:400]}")
    raw = match.group()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Replace invalid backslash escapes (anything not n t r b f " \ / uXXXX)
        repaired = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", raw)
        return json.loads(repaired)


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _scrub_emails(value, replacement: str):
    """Recursively replace invented email addresses in any JSON-like structure."""
    if isinstance(value, str):
        return _EMAIL_RE.sub(replacement, value)
    if isinstance(value, list):
        return [_scrub_emails(item, replacement) for item in value]
    if isinstance(value, dict):
        return {k: _scrub_emails(v, replacement) for k, v in value.items()}
    return value


def scrub_invented_emails(analysis: dict, contact: dict | None) -> dict:
    """
    Replace every invented email in the mutable fields of analysis with
    the resolved contact email (or '[client email needed]' if unknown).

    Fields scrubbed: advisor_actions, draft_email.subject, draft_email.body.
    The other fields (client_name, property_location, etc.) never contain emails.
    """
    replacement = contact.get("email") if contact else "[client email needed]"

    scrubbed = dict(analysis)
    scrubbed["advisor_actions"] = _scrub_emails(
        analysis.get("advisor_actions", []), replacement
    )
    if "draft_email" in analysis:
        scrubbed["draft_email"] = _scrub_emails(analysis["draft_email"], replacement)

    return scrubbed


# ---------------------------------------------------------------------------
# Stage 1: analyze_call
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """\
You are Meridian, an AI assistant for C1 Insurance Group and MyUtilities.
Analyze the following call transcript and return ONLY a valid JSON object —
no markdown, no explanation, just raw JSON.

The JSON must match this exact schema:
{
  "client_name":        string,
  "property_location":  string,
  "closing_date":       string  (e.g. "2026-06-12" or "unknown"),
  "current_carriers":   list of strings (insurance carriers the client currently uses),
  "urgency": {
    "score":  integer 1-10,
    "reason": string
  },
  "coverage_interests": list of strings,
  "utility_needs":      list of strings,
  "crosssell_flags": [
    {
      "direction":        "c1_to_myutils" | "myutils_to_c1",
      "reason":           string,
      "suggested_action": string
    }
  ],
  "advisor_actions": list of strings,
  "draft_email": {
    "subject": string,
    "body":    string
  }
}

Rules:
- urgency 9-10: closing within 7 days or client explicitly stressed/panicked
- urgency 7-8: closing within 14 days or clear time pressure
- urgency 5-6: needs service but no hard deadline mentioned
- urgency below 5: exploratory / renewal / no urgency signal
- coverage_interests: list specific coverages or policy types mentioned or implied
  (e.g. "homeowners", "auto bundle", "landlord/DP3", "umbrella")
- utility_needs: only services not yet set up (electricity, internet, gas, etc.)
- crosssell_flags: include one for EACH distinct cross-sell opportunity detected
- advisor_actions: concrete numbered next steps the advisor must take today
- draft_email: write it in a warm, professional insurance advisor voice; address
  the client by first name; reference specific details from the call (closing date,
  address if given, carriers mentioned); include a clear call-to-action.
  IMPORTANT: do NOT include any email addresses in the draft_email body or subject.
  The recipient's email is resolved from a separate system after analysis.

Transcript:
{transcript}
"""


def analyze_call(transcript_text: str) -> dict:
    """
    Extract structured intelligence from a call transcript.

    When USE_LLM=false (default) returns the deterministic demo analysis
    immediately without calling Gemini. When USE_LLM=true, calls Gemini
    and falls back to the demo analysis on any exception.
    """
    if not USE_LLM:
        return dict(DEMO_ANALYSIS)

    try:
        model    = _gemini_client()
        prompt   = ANALYSIS_PROMPT.replace("{transcript}", transcript_text)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return _extract_json(response.text)
    except Exception:
        result = dict(DEMO_ANALYSIS)
        result["_demo_fallback"] = True
        return result


# ---------------------------------------------------------------------------
# Stage 2: resolve_contact
# ---------------------------------------------------------------------------

def resolve_contact(client_name: str) -> dict | None:
    """
    Look up a client by name in data/contacts.csv.

    Returns {"name", "phone", "email", "source", "type"} or None.
    Matching is case-insensitive on the full name and also on first name only
    as a fallback.
    """
    if not CONTACTS_CSV.exists():
        return None

    needle_full  = _normalize_name(client_name)
    needle_first = needle_full.split()[0] if needle_full else ""

    with CONTACTS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            candidate = _normalize_name(row.get("name", ""))
            if candidate == needle_full:
                return dict(row)

    # Fallback: first-name-only match (returns first hit)
    if needle_first:
        with CONTACTS_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                candidate = _normalize_name(row.get("name", ""))
                if candidate.startswith(needle_first):
                    return dict(row)

    return None


# ---------------------------------------------------------------------------
# Stage 3: generate_outbox_events
# ---------------------------------------------------------------------------

def generate_outbox_events(analysis: dict, contact: dict | None) -> list[dict]:
    """
    Build mock integration event payloads — nothing is sent.

    Event types:
      CREATE_CRM_LEAD      → HubSpot
      CREATE_ADVISOR_TASK  → Internal task queue
      SEND_EMAIL           → Email provider (draft only)
      SEND_SMS             → SMS gateway (draft only)
      MYUTILITIES_HANDOFF  → MyUtilities partner API
    """
    events     = []
    call_ref   = str(uuid.uuid4())
    now_iso    = datetime.now(timezone.utc).isoformat()
    name       = analysis.get("client_name", "Unknown")
    location   = analysis.get("property_location", "")
    closing    = analysis.get("closing_date", "unknown")
    email      = contact.get("email") if contact else "[client email needed]"
    phone      = contact.get("phone")  if contact else None
    source     = contact.get("source") if contact else "inbound call"
    urgency    = analysis.get("urgency", {}).get("score", 5)

    # ── CREATE_CRM_LEAD ──────────────────────────────────────────────────
    events.append({
        "eventType":    "CREATE_CRM_LEAD",
        "targetSystem": "HubSpot",
        "status":       "READY_TO_SEND",
        "payload": {
            "call_ref":           call_ref,
            "firstname":          name.split()[0] if name else "",
            "lastname":           " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "email":              email,
            "phone":              phone,
            "lead_source":        source,
            "property_address":   location,
            "closing_date":       closing,
            "pipeline":           "New Homeowner",
            "deal_stage":         "Quote Requested",
            "urgency_score":      urgency,
            "coverage_interests": analysis.get("coverage_interests", []),
            "current_carriers":   analysis.get("current_carriers", []),
            "created_at":         now_iso,
        },
    })

    # ── CREATE_ADVISOR_TASK ──────────────────────────────────────────────
    task_priority = "HIGH" if urgency >= 8 else "MEDIUM" if urgency >= 5 else "LOW"
    events.append({
        "eventType":    "CREATE_ADVISOR_TASK",
        "targetSystem": "InternalTaskQueue",
        "status":       "READY_TO_SEND",
        "payload": {
            "call_ref":    call_ref,
            "title":       f"Follow-up: {name} — {location}",
            "priority":    task_priority,
            "due_date":    closing if closing != "unknown" else "ASAP",
            "assigned_to": "next_available_advisor",
            "steps":       analysis.get("advisor_actions", []),
            "notes":       analysis.get("urgency", {}).get("reason", ""),
        },
    })

    # ── SEND_EMAIL ───────────────────────────────────────────────────────
    draft = analysis.get("draft_email", {})
    events.append({
        "eventType":    "SEND_EMAIL",
        "targetSystem": "EmailProvider",
        "status":       "READY_TO_SEND",
        "payload": {
            "call_ref":  call_ref,
            "to_name":   name,
            "to_email":  email,
            "from_name": "Marcus Webb — C1 Insurance Group",
            "from_email": "marcus.webb@c1insurancegroup.com",
            "subject":   draft.get("subject", f"Your Home Insurance Quote — {name}"),
            "body":      draft.get("body", ""),
            "send_after": now_iso,
        },
    })

    # ── SEND_SMS ─────────────────────────────────────────────────────────
    first_name = name.split()[0] if name else "there"
    sms_body   = (
        f"Hi {first_name}, this is Marcus at C1 Insurance Group. "
        f"I have your quotes ready — check your email or reply here "
        f"and I'll walk you through them. Closing is coming up fast!"
        if urgency >= 7 else
        f"Hi {first_name}, Marcus at C1 Insurance Group. "
        f"Your home insurance quotes are ready. Reply or call me at your convenience."
    )
    events.append({
        "eventType":    "SEND_SMS",
        "targetSystem": "SMSGateway",
        "status":       "READY_TO_SEND",
        "payload": {
            "call_ref":    call_ref,
            "to_phone":    phone,
            "from_number": "+12148880001",
            "body":        sms_body,
            "send_after":  now_iso,
        },
    })

    # ── MYUTILITIES_HANDOFF ──────────────────────────────────────────────
    # Only emit if the analysis detected a c1_to_myutils cross-sell flag
    mu_flags = [
        f for f in analysis.get("crosssell_flags", [])
        if f.get("direction") == "c1_to_myutils"
    ]
    if mu_flags:
        events.append({
            "eventType":    "MYUTILITIES_HANDOFF",
            "targetSystem": "MyUtilitiesPartnerAPI",
            "status":       "READY_TO_SEND",
            "payload": {
                "call_ref":        call_ref,
                "client_name":     name,
                "client_phone":    phone,
                "client_email":    email,
                "property_address": location,
                "utility_needs":   analysis.get("utility_needs", []),
                "referral_reason": mu_flags[0].get("reason", ""),
                "suggested_action": mu_flags[0].get("suggested_action", ""),
                "sla_minutes":     60,
                "referred_by":     "C1 Insurance Group — Marcus Webb",
                "referred_at":     now_iso,
            },
        })

    return events


# ---------------------------------------------------------------------------
# Stage 4: log_audit
# ---------------------------------------------------------------------------

def log_audit(analysis: dict, events: list[dict]) -> int:
    """
    Persist analysis + events to audit.db (SQLite). Returns the new row id.

    Schema (created on first run):
      audit_log(id, call_id, timestamp, client_name, urgency_score,
                analysis_json, events_json)
    """
    conn = sqlite3.connect(str(AUDIT_DB))
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id        TEXT NOT NULL,
            timestamp      TEXT NOT NULL,
            client_name    TEXT,
            urgency_score  INTEGER,
            analysis_json  TEXT,
            events_json    TEXT
        )
    """)

    # Derive call_id from the CRM event if present, else generate one
    crm_event = next((e for e in events if e["eventType"] == "CREATE_CRM_LEAD"), None)
    call_id   = crm_event["payload"]["call_ref"] if crm_event else str(uuid.uuid4())

    row_id = cur.execute(
        """
        INSERT INTO audit_log
            (call_id, timestamp, client_name, urgency_score, analysis_json, events_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            call_id,
            datetime.now(timezone.utc).isoformat(),
            analysis.get("client_name"),
            analysis.get("urgency", {}).get("score"),
            json.dumps(analysis),
            json.dumps(events),
        ),
    ).lastrowid

    conn.commit()
    conn.close()
    return row_id


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    width = 72
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _print_analysis(a: dict) -> None:
    _section("STAGE 1 — CALL ANALYSIS")
    print(f"  Client:       {a.get('client_name')}")
    print(f"  Property:     {a.get('property_location')}")
    print(f"  Closing:      {a.get('closing_date')}")
    print(f"  Carriers:     {', '.join(a.get('current_carriers', [])) or 'none mentioned'}")
    urg = a.get("urgency", {})
    print(f"  Urgency:      {urg.get('score')}/10 — {urg.get('reason')}")
    print(f"  Coverage:     {', '.join(a.get('coverage_interests', []))}")
    print(f"  Utility needs:{', '.join(a.get('utility_needs', [])) or 'none'}")

    flags = a.get("crosssell_flags", [])
    if flags:
        print(f"\n  Cross-sell flags ({len(flags)}):")
        for f in flags:
            arrow = "C1 → MyUtils" if f["direction"] == "c1_to_myutils" else "MyUtils → C1"
            print(f"    [{arrow}] {f['reason']}")
            print(f"             Action: {f['suggested_action']}")

    print(f"\n  Advisor actions:")
    for i, step in enumerate(a.get("advisor_actions", []), 1):
        print(textwrap.fill(f"    {i}. {step}", width=72, subsequent_indent="       "))

    draft = a.get("draft_email", {})
    print(f"\n  Draft email subject: {draft.get('subject')}")
    print(f"  Draft email body:")
    for line in draft.get("body", "").splitlines():
        print(f"    {line}")


def _print_contact(contact: dict | None) -> None:
    _section("STAGE 2 — CONTACT RESOLUTION")
    if contact:
        print(f"  Name:   {contact['name']}")
        print(f"  Phone:  {contact['phone']}")
        print(f"  Email:  {contact['email']}")
        print(f"  Source: {contact['source']}")
        print(f"  Type:   {contact['type']}")
    else:
        print("  No matching contact found in contacts.csv")


def _print_events(events: list[dict]) -> None:
    _section("STAGE 3 — OUTBOX EVENTS (mock — nothing sent)")
    for ev in events:
        print(f"\n  [{ev['status']}] {ev['eventType']} → {ev['targetSystem']}")
        payload = ev["payload"]
        for k, v in payload.items():
            if k in ("body", "steps"):
                continue  # skip long blobs in summary
            print(f"    {k}: {v}")


def _print_audit(row_id: int) -> None:
    _section("STAGE 4 — AUDIT LOG")
    print(f"  Written to:  {AUDIT_DB}")
    print(f"  Row id:      {row_id}")
    conn = sqlite3.connect(str(AUDIT_DB))
    row  = conn.execute(
        "SELECT call_id, timestamp, client_name, urgency_score FROM audit_log WHERE id=?",
        (row_id,),
    ).fetchone()
    conn.close()
    if row:
        print(f"  Call ID:     {row[0]}")
        print(f"  Timestamp:   {row[1]}")
        print(f"  Client:      {row[2]}")
        print(f"  Urgency:     {row[3]}/10")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transcript_path = BASE_DIR / "incoming_calls" / "sarah_homebuyer.txt"
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    transcript_text = transcript_path.read_text(encoding="utf-8")
    print(f"\nProcessing: {transcript_path.name}  ({len(transcript_text)} chars)")

    print("\n[1/4] Analyzing call with Gemini...")
    analysis = analyze_call(transcript_text)

    print("\n[2/4] Resolving contact...")
    contact = resolve_contact(analysis.get("client_name", ""))
    _print_contact(contact)

    analysis = scrub_invented_emails(analysis, contact)
    _print_analysis(analysis)

    print("\n[3/4] Generating outbox events...")
    events = generate_outbox_events(analysis, contact)
    _print_events(events)

    print("\n[4/4] Writing audit log...")
    row_id = log_audit(analysis, events)
    _print_audit(row_id)

    print(f"\n{'=' * 72}")
    print(f"  Pipeline complete — {len(events)} events queued, audit row {row_id}")
    print(f"{'=' * 72}\n")
