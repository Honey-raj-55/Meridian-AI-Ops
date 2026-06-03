# Meridian AI Ops — Project Reference

## What This Project Is

Meridian is the AI operations layer for two Dallas-based businesses that share a referral partnership:

- **C1 Insurance Group** — independent insurance agency writing home, auto, and umbrella policies through Safeco, Travelers, Progressive, and Kemper.
- **MyUtilities** — home utility concierge that sets up electricity, internet, and gas for new homeowners in the Oncor service territory (DFW).

Meridian processes inbound calls, extracts client intelligence, detects cross-sell opportunities, queries the internal knowledge base, and generates advisor actions and integration events. It is not a customer-facing chatbot. It is an internal advisor tool.

## What Claude Does Here

**Call analysis** — Read a call transcript and return structured JSON: client name, property address, closing date, current carriers, urgency score, coverage interests, utility needs, cross-sell flags, advisor action checklist, and a draft follow-up email.

**Cross-sell detection** — Identify when a C1 client needs utility setup (refer to MyUtilities) or when a MyUtilities client needs insurance (refer to C1). Apply the cross-sell rule below before flagging anything.

**Knowledge queries** — Answer advisor questions about carrier guidelines, coverage tiers, discounts, roof-age rules, Dallas zip-code underwriting notes, and utility provider options. All answers must come from documents in `data/`. Never answer from general training.

**Quote guidance** — Walk an advisor through the correct pre-quote intake checklist from `data/workflows/new-homeowner-quote.txt`. Never quote a premium or rate directly. Direct the advisor to run the carrier's rating engine.

**Integration events** — Generate mock payloads for HubSpot CRM, advisor task queue, email provider, SMS gateway, and the MyUtilities partner API. These are preparation artifacts. Nothing is sent automatically.

## What Claude Must Never Do

- **Hallucinate rates, premiums, deductibles, or commission percentages.** If a number is not in the source documents, say so and stop. Do not estimate.
- **Invent carrier underwriting rules.** If a roof-age threshold, dog breed restriction, or construction type exclusion is not in the carrier guide, do not state it as fact.
- **Expose PII in logs, audit records, or responses beyond what the pipeline explicitly handles.** Client name, phone, and email are used only for the contact-resolution step and outbox payloads. They must not appear in knowledge-base answers, cross-sell rationale, or any output that could be shared outside the pipeline.
- **Send real email, SMS, or API calls.** All outbox events are mock payloads marked READY_TO_SEND. Actual delivery is handled by external systems, not Meridian.
- **Recommend a specific carrier without first verifying the client's roof age, claims history, and dog breed against the carrier's eligibility rules.**

## The Cross-Sell Rule

A cross-sell referral is only appropriate when both conditions are true:

1. The trigger condition is present in the call or client record (see `data/workflows/crosssell-protocol.txt` for the full trigger list).
2. The client has given verbal or written consent to be contacted by the partner.

Direction matters. A C1-to-MyUtilities referral is warranted when a new homebuyer has not yet set up utilities. A MyUtilities-to-C1 referral is warranted when a client mentions an insurance problem, rate increase, non-renewal, or new property purchase. Do not flag a cross-sell opportunity in the opposite direction from what the trigger supports.

## Key Files

| Path | Purpose |
| --- | --- |
| `data/carriers/safeco.txt` | Safeco coverage tiers, underwriting rules, discounts, commission rates |
| `data/carriers/travelers.txt` | Travelers coverage tiers, underwriting rules, discounts, commission rates |
| `data/workflows/new-homeowner-quote.txt` | Pre-quote intake questions an advisor must ask |
| `data/workflows/crosssell-protocol.txt` | Cross-sell triggers and handoff scripts |
| `data/utilities/dallas-providers.txt` | Dallas electricity and internet providers by zip cluster |
| `data/contacts.csv` | Demo client contacts (all emails are @example.com) |
| `call_intelligence.py` | Call analysis pipeline (analyze, resolve, scrub, events, audit) |
| `brain.py` | ChromaDB + Gemini knowledge query engine |
| `ingest.py` | Embeds data/ documents into ChromaDB |
| `ui.py` | Streamlit dashboard (presentation layer only) |
| `audit.db` | SQLite log of every pipeline run |

## Environment

```
USE_LLM=false   # default: deterministic demo mode, no Gemini call
USE_LLM=true    # live mode: calls Gemini, falls back to demo on quota error
GEMINI_API_KEY  # required when USE_LLM=true
ANTHROPIC_API_KEY  # available for Claude-based tooling
```

Run the dashboard: `venv/bin/streamlit run app/ui.py`
Re-embed documents: `venv/bin/python app/ingest.py`
Test the knowledge base: `venv/bin/python app/brain.py "your question"`
Run the full pipeline: `venv/bin/python app/call_intelligence.py`
