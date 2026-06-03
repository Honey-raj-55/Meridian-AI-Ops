<div align="center">

# 🧠 Meridian AI Ops

### AI Operations Layer for Insurance & Home Advisory Platforms

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange?style=flat)](https://trychroma.com)
[![Gemini](https://img.shields.io/badge/Gemini_1.5_Flash-LLM-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![Claude](https://img.shields.io/badge/Claude_API-Anthropic-D4A843?style=flat)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

**A call comes in. Meridian transcribes it, understands it, finds the customer,
generates the follow-up, flags cross-sell opportunities, and logs the entire workflow —
in seconds, not minutes.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Demo](#-demo-walkthrough) · [Roadmap](#-roadmap)

---

![Meridian AI Ops Demo](https://raw.githubusercontent.com/Honey-raj-55/Meridian-AI-Ops/main/app/assets/demo-preview.png)

</div>

---

## The Problem

Independent insurance agencies and home advisory businesses run on phone calls.
Every call ends the same way: an advisor spends 15–20 minutes doing manual work —
writing notes, drafting follow-up emails, entering data into the CRM, flagging
cross-sell opportunities to a different team, looking up carrier guidelines.

That manual work **scales linearly with headcount**. It kills throughput.
It causes missed cross-sells. It buries institutional knowledge in individual heads.

**Meridian eliminates that friction.**

---

## ✨ Features

### Module 1 — Call Intelligence

| Capability | What It Does |
|---|---|
| **Call Analysis** | Extracts client name, property, urgency, coverage interests, utility needs from any call transcript |
| **Cross-sell Detection** | Automatically detects both directions: insurance client → utility setup, utility client → insurance quote |
| **Advisor Action Plan** | Generates prioritized next-step checklist for the advisor |
| **Follow-up Draft** | Produces a ready-to-send email in a warm, professional advisor voice |
| **Integration Outbox** | Emits structured events for CRM, advisor task, SMS, email, and partner handoff — adapter-swappable for any production system |
| **Audit Log** | Every AI decision persisted to SQLite with timestamp, confidence, and source |

### Module 2 — Meridian Brain

| Capability | What It Does |
|---|---|
| **Knowledge Base** | Carrier guides, quoting workflows, cross-sell protocols, utility provider data — all indexed |
| **Semantic Search** | Vector similarity search over proprietary documents, not the public internet |
| **Source Citations** | Every answer traces back to the source document |
| **Advisor Queries** | Natural language questions get precise, grounded answers — no hallucinated rates |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MERIDIAN AI OPS                            │
├──────────────────────┬──────────────────────────────────────────┤
│   MODULE 1           │   MODULE 2                              │
│   Call Intelligence  │   Meridian Brain                        │
│                      │                                          │
│  Transcript          │  Knowledge Documents                    │
│      ↓               │      ↓                                  │
│  Client Extraction   │  Chunking + Embedding                   │
│      ↓               │      ↓                                  │
│  Intent Analysis     │  ChromaDB Vector Store                  │
│      ↓               │      ↓                                  │
│  Cross-sell Detect   │  Semantic Search                        │
│      ↓               │      ↓                                  │
│  Advisor Summary     │  Grounded LLM Answer                    │
│      ↓               │      ↓                                  │
│  Follow-up Draft     │  Source Citations                       │
│      ↓               │                                          │
│  Integration Outbox  │                                          │
│      ↓               │                                          │
│  SQLite Audit Log    │                                          │
└──────────────────────┴──────────────────────────────────────────┘

Integration Outbox — Adapter Pattern
┌──────────────────────────────────────────┐
│  IAdapter (interface)                    │
├──────────────────────────────────────────┤
│  MockCrmAdapter        → demo/dev        │
│  MockEmailAdapter      → demo/dev        │
│  MockSmsAdapter        → demo/dev        │
│  MockMyUtilitiesAdapter → demo/dev       │
├──────────────────────────────────────────┤
│  HubSpotAdapter        → production swap │
│  TwilioAdapter         → production swap │
│  AgencyZoomAdapter     → production swap │
│  N8NWebhookAdapter     → production swap │
└──────────────────────────────────────────┘
```

**The AI workflow never changes. Only the adapter changes when you go to production.**

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Vector Database | [ChromaDB](https://trychroma.com) | Local, zero-config, production-grade |
| Embeddings | [sentence-transformers](https://sbert.net) `all-MiniLM-L6-v2` | Free, runs locally, fast |
| Primary LLM | Gemini 1.5 Flash | Free tier — 1M tokens/day |
| Premium LLM | Claude API (Anthropic) | Reserved for high-precision tasks |
| Backend | FastAPI | Lightweight, async, production-ready |
| UI | Streamlit | Fast to build, clean for demos |
| Database | SQLite | Zero-config audit persistence |
| Language | Python 3.9+ | — |

**Total infrastructure cost: $0** — no paid services, no trials, no subscriptions.

---

## 📁 Project Structure

```
meridian-ai-ops/
│
├── app/
│   ├── data/
│   │   ├── carriers/
│   │   │   ├── safeco.txt
│   │   │   ├── travelers.txt
│   │   │   ├── progressive.txt
│   │   │   └── kemper.txt
│   │   ├── workflows/
│   │   │   ├── new-homeowner-quote.txt
│   │   │   ├── crosssell-protocol.txt
│   │   │   └── renewal-workflow.txt
│   │   └── utilities/
│   │       └── dallas-providers.txt
│   │
│   ├── ingest.py              # Load docs → chunk → embed → ChromaDB
│   ├── brain.py               # Semantic search + grounded LLM answers
│   ├── call_intelligence.py   # Full call analysis pipeline
│   └── ui.py                  # Streamlit interface
│
├── .claude/
│   └── agents/
│       ├── carrier-specialist.md
│       └── crosssell-agent.md
│
├── rules/
│   ├── never-hallucinate-rates.md
│   └── data-privacy.md
│
├── skills/
│   └── answer-carrier-query.md
│
├── incoming_calls/            # Drop audio or transcript files here
├── outbox/                    # Integration events written here
├── chroma_db/                 # Auto-created vector store
├── audit.db                   # Auto-created SQLite audit log
├── CLAUDE.md                  # Claude Code workspace configuration
├── .env.example               # Environment variable template
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- A free [Gemini API key](https://aistudio.google.com/apikey) (no credit card)
- Optional: Anthropic API key for Claude

### 1. Clone the repo

```bash
git clone https://github.com/Honey-raj-55/Meridian-AI-Ops.git
cd Meridian-AI-Ops
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ First install downloads the sentence-transformers model (~90 MB). Allow 2–5 minutes on first run.

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_claude_key_here   # optional
```

### 5. Ingest the knowledge base

```bash
python app/ingest.py
```

Expected output:
```
✅ Ingested 247 chunks from 6 documents
   Carriers: 4 files
   Workflows: 3 files
   Utilities: 1 file
```

### 6. Launch the app

```bash
streamlit run app/ui.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## 🎬 Demo Walkthrough

### Module 1 — Call Intelligence

1. Go to the **Call Intelligence** tab
2. Click **Load Incoming Call** — loads a sample homebuyer transcript
3. Click **Analyze Call**

You'll see:

```
CLIENT SUMMARY
──────────────────────────────────────────
Name:             Sarah Mitchell
Property:         Plano, TX — closing next Friday
Urgency:          9/10 — active closing timeline
Coverage Need:    Home insurance + Auto bundle
Utility Needs:    Electricity, Internet

CROSS-SELL DETECTED
──────────────────────────────────────────
⚡ MyUtilities → C1  Utility setup for new home → insurance quote
🏠 C1 → MyUtilities  New homeowner → utility connection referral

ADVISOR ACTION PLAN
──────────────────────────────────────────
□ Call back today — closing is next Friday
□ Request lender's minimum coverage requirements
□ Ask for current auto declarations page
□ Offer MyUtilities setup during the same call

FOLLOW-UP EMAIL
──────────────────────────────────────────
Subject: Your home insurance & move-in setup for Plano
[Ready-to-send email — advisor reviews and clicks send]

INTEGRATION OUTBOX
──────────────────────────────────────────
✅ CREATE_CRM_LEAD         → CRM        READY_TO_SEND
✅ CREATE_ADVISOR_TASK     → Internal   READY_TO_SEND
✅ SEND_EMAIL              → Email      READY_TO_SEND
✅ MYUTILITIES_HANDOFF     → MyUtils    READY_TO_SEND
✅ AUDIT_LOG_SAVED         → SQLite     COMPLETE
```

### Module 2 — Meridian Brain

Example queries:

```
"What should an advisor ask a new homeowner before quoting?"
"What's Safeco's sweet spot for Dallas homes?"
"Which internet providers serve zip code 75230?"
"Walk me through the renewal workflow for Travelers policies."
"What cross-sell triggers should I look for on a MyUtilities call?"
```

Each answer cites its source document — no hallucinations, no invented rates.

---

## 🔌 Integration Outbox — Adapter Pattern

The integration layer is built for production extensibility. Today it runs with mock adapters. When you have production credentials, only the adapter changes — the entire AI workflow stays the same.

```python
# Today (demo)
crm_adapter = MockCrmAdapter()

# Tomorrow (production) — one line change
crm_adapter = HubSpotAdapter(api_key=os.getenv("HUBSPOT_KEY"))
crm_adapter = AgencyZoomAdapter(api_key=os.getenv("AGENCYZOOM_KEY"))
```

Designed to connect to:

| System | Purpose |
|---|---|
| **HubSpot / AgencyZoom** | CRM lead creation, contact update |
| **Twilio / Bland.ai / VAPI** | SMS delivery, voice workflow triggers |
| **Retell AI** | Call transcription + live agent assist |
| **n8n / Make / Zapier** | Workflow automation webhooks |
| **MyUtilities internal API** | Cross-company handoff |

---

## 📊 Knowledge Base

The Brain is pre-loaded with insurance agency knowledge across six document categories:

| Document | Contents |
|---|---|
| `safeco.txt` | Coverage tiers, Dallas hail risk guidelines, commission rates, bundle discounts, target client profiles |
| `travelers.txt` | Carrier-specific rules, commercial lines, specialty coverage |
| `progressive.txt` | Auto-forward pricing, Platinum agency benefits |
| `kemper.txt` | Inner Circle agency status, specialty markets |
| `new-homeowner-quote.txt` | Every question an advisor must ask before quoting |
| `crosssell-protocol.txt` | Triggers, scripts, and handoff language for both C1↔MyUtilities directions |
| `dallas-providers.txt` | Electricity and internet providers by Dallas zip code |

---

## 🗺 Roadmap

```
✅  PHASE 1 (Complete)
    Call Intelligence + Internal Brain + Integration Outbox

🔜  PHASE 2 — Automation Layer
    Real CRM adapter (HubSpot / AgencyZoom)
    Live email sending via Gmail API
    SMS delivery via Twilio
    n8n workflow triggers for renewal sequences

🔜  PHASE 3 — Voice Layer
    Live call transcription via Retell AI / VAPI
    Real-time advisor assist during calls
    Post-call auto-processing without manual upload

🔜  PHASE 4 — Operations Dashboard
    Advisor pipeline visibility
    Cross-sell conversion tracking
    Revenue opportunity heatmap
    Team performance metrics
```

---

## 🤝 Built For

This project was designed as the AI operations layer for independent insurance agencies and home advisory platforms — specifically businesses operating the combined **insurance + utility concierge** model where the same homebuyer touchpoint serves two revenue streams simultaneously.

The architecture is intentionally **business-agnostic at the adapter layer** and **business-specific at the intelligence layer** — meaning the AI models and prompts are tuned to insurance/home advisory use cases, while every integration point is swappable for any CRM, communication, or automation system.

---

<div align="center">

Built with Python · ChromaDB · Gemini · Claude · Streamlit

**[View Demo](https://github.com/Honey-raj-55/Meridian-AI-Ops) · [Report Issue](https://github.com/Honey-raj-55/Meridian-AI-Ops/issues) · [LinkedIn](https://linkedin.com/in/honey-raj)**

</div>
