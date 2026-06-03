# Rule: Data Privacy and PII Handling

## What Counts as PII in This Project

| Field | Examples |
| --- | --- |
| Client name | Sarah Mitchell |
| Phone number | (214) 883-7042 |
| Email address | sarah.mitchell.demo@example.com |
| Property address | 4817 Thornbury Drive, Plano, TX 75093 |
| Lender and loan number | Rocket Mortgage, loan # |
| Claims history details | Date, type, and amount of prior losses |
| Current carrier and policy number | State Farm policy # |
| Dog breed (when noted for underwriting) | Combined with name becomes identifiable |

## Where PII Is Allowed

PII is permitted only in these locations and for these purposes:

1. **Incoming call transcripts** — stored in `incoming_calls/` as the raw source record. Access is internal only.
2. **Contact resolution** — `data/contacts.csv` is used exclusively to look up a matching email and phone for outbox event payloads. Demo emails use the `@example.com` domain.
3. **Outbox event payloads** — PII fields (name, phone, email, address) appear in structured integration events destined for HubSpot, the task queue, email provider, SMS gateway, and the MyUtilities API. These are mock payloads in demo mode and are never transmitted.
4. **Audit log** — `audit.db` stores the full pipeline output including PII as a structured JSON blob. This database is local only and must not be shared, exported, or included in version control.

## Where PII Must Not Appear

- **Knowledge base answers** (`brain.py` responses) — Do not include client name, phone, email, or address in answers returned by `query_brain()`. Answers are pulled from carrier and workflow documents, not from call records.
- **Cross-sell rationale** — The reason and suggested action fields in cross-sell flags describe the trigger condition generically. They must not repeat the client's name, phone, or email.
- **Logs or console output** — Standard Python logging and print statements must not output raw PII. The `__main__` blocks in `call_intelligence.py` and `brain.py` may print client name and urgency score for demo readability but must not print phone numbers or email addresses.
- **Error messages** — Exception messages surfaced to the UI must not include PII. If an exception contains a client record, catch it, log it sanitized, and show a generic message.

## Email Address Handling

Meridian includes an active scrubbing step (`scrub_invented_emails`) that replaces any LLM-generated email address in advisor actions and draft email fields with the resolved contact email from `data/contacts.csv`, or the literal string `[client email needed]` if no contact is found. This runs on every pipeline execution before events are generated.

All demo email addresses must use the `@example.com` domain with `.demo` in the local part (e.g., `sarah.mitchell.demo@example.com`). Real client email addresses must never appear in the demo data files.

## Version Control

The following files must not be committed to any shared repository:

- `audit.db` — contains full pipeline output with PII
- `.env` — contains API keys
- `incoming_calls/*.txt` — contains call transcripts with client PII (demo transcripts with fictional data are acceptable)
- `data/contacts.csv` — contains client contact records (demo file with `@example.com` addresses is acceptable)

Add these to `.gitignore` if the project is ever committed to a remote repository.
