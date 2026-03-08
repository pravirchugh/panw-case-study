# Community Guardian

An AI-powered community safety and digital wellness platform that helps users report, triage, and act on local safety incidents and digital threats.

**Candidate Name:** Pravir Chugh

**Scenario Chosen:** 3 - Community Safety & Digital Wellness

**Estimated Time Spent:** ~5 hours

---

## Quick Start

### Prerequisites

- Python 3.11+
- (Optional) OpenAI API key for AI-powered analysis

### Run Commands

```bash
# 1. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional - app works without it)

# 4. Start the server
uvicorn app.main:app --reload

# 5. Open http://127.0.0.1:8000 in your browser
```

### Test Commands

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## Design Overview

### Problem & Approach

As digital and physical security threats grow more complex, community members need a way to share safety information without the noise and anxiety of social media. Community Guardian provides a calm, structured incident reporting system with AI-powered triage.

I chose Scenario 3 because it aligns closely with Palo Alto Networks' focus on security and AI-powered platforms. I intentionally scoped the prototype around **incident intake, triage, and actionability** -- one complete end-to-end flow rather than many half-built features.

### Architecture

```
FastAPI (Python 3.11)
├── SQLite database (zero-config, file-based)
├── Jinja2 server-side templates
├── OpenAI GPT-3.5-turbo (summarize + categorize)
└── Deterministic fallback rules engine
```

**Why this stack:**
- **FastAPI** -- Pydantic validation built-in, clear route structure, easy to test
- **SQLite** -- Zero configuration, single file, ideal for prototype scope
- **Jinja2 SSR** -- Avoids SPA complexity; the demo is straightforward to follow
- **Server-rendered HTML** -- No frontend build step, works immediately

### Core Flow

1. User submits an incident report (title + description)
2. Input is validated (title required, description min 10 chars)
3. AI service attempts to classify and summarize the report
4. If AI fails or is unavailable, deterministic keyword rules take over
5. Incident is saved with category, severity, summary, and action checklist
6. User can view the feed, search/filter, and update incident status

### AI Integration + Fallback

**AI Service:** Calls OpenAI GPT-3.5-turbo to produce a JSON response with category, severity, summary, and checklist.

**Fallback Rules Engine:** A keyword-matching classifier that maps incident text to categories (phishing, scam/fraud, network security, physical safety, identity theft) with canned checklists. This runs automatically when:
- No API key is configured
- The API returns an error or times out
- The response cannot be parsed

The fallback is **first-class** -- it was built before the AI service, and the app works fully without any API key. Each incident displays a badge indicating whether analysis was "AI Analyzed" or "Rule-Based," so users always know the source.

### Search & Filter

The incident feed supports:
- **Text search** across title and description
- **Category filter** (phishing, scam/fraud, network security, etc.)
- **Severity filter** (low, medium, high)
- **Status filter** (open, reviewed, resolved)
- **Audience filter** (Remote Worker, Elderly User, Neighborhood Group)

### AI Analyzed vs Rule-Based: What Changes

| | **Rule-Based (Fallback)** | **AI Analyzed (OpenAI)** |
|---|---|---|
| **Badge** | Yellow "RULE-BASED" | Purple "AI ANALYZED" |
| **Summary** | Generic template per category | Context-specific to the actual report |
| **Checklist** | Canned 4 steps per category | Tailored to the specific incident details |
| **Speed** | Instant | ~1-2 seconds (API call) |
| **Reliability** | Always works, no external dependency | Falls back to rules on any failure |

**Example:** A tech support scam report about a fake virus pop-up demanding $299:
- **Rule-based summary:** "This report describes a potential scam or fraud attempt seeking money or sensitive information."
- **AI summary:** "Encountered a scam pop-up claiming computer infection and demanding payment for fake tech support."
- **AI checklist:** "Do not call the provided number or download any software" / "Force close the browser tab or restart the browser" -- specific to the pop-up scenario vs generic "report to FTC" advice.

---

## Testing

8 tests covering three categories:

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_happy_path.py` | 4 | Create incident, view detail, filter by category, audience, text search |
| `test_ai_fallback.py` | 2 | AI returns None -> fallback works; AI throws exception -> fallback works |
| `test_validation.py` | 3 | Empty description -> 422 error; empty title -> 422 error; nonexistent incident -> 404 |

Tests use an in-memory SQLite database and TestClient, so they run in ~0.05s with no external dependencies.

---

## Synthetic Data

`data/incidents_seed.json` contains 10 synthetic incidents covering all categories, severities, and statuses. The database is automatically seeded on first startup. No real personal data is included.

---

## AI Disclosure

- **Did you use an AI assistant?** Yes -- Claude (Anthropic) for code generation and architecture decisions.
- **How did you verify the suggestions?** Manually reviewed all generated code, ran the test suite, and tested the full flow in the browser. Verified AI classification output against expected categories for each seed incident.
- **Example of a suggestion rejected or changed:** The AI assistant initially suggested using the AI model for real-time threat classification only (categorize + assign severity), without generating a human-readable summary or tailored checklist. I pushed for the AI to also produce a contextual summary and incident-specific action steps on each submission, since the core value proposition of the app is turning noisy reports into calm, actionable guidance. This made the AI output significantly more useful compared to just labeling a category, and the contrast with the generic fallback templates is what demonstrates the AI's real value.

---

## Tradeoffs & Prioritization

### What I cut to stay within the timebox
- **Authentication/authorization** -- Not needed to demonstrate the core triage flow
- **Map visualization** -- Would add complexity without demonstrating engineering rigor
- **Real-time notifications** -- Background job infrastructure is out of scope
- **Safe Circles messaging** -- Encryption and group features are a separate product slice
- **Polished UI** -- Clean but minimal; focused on functionality over aesthetics

### What I would build next
- **Confidence scoring** -- AI returns a confidence level; below threshold, automatically use fallback and flag for human review
- **User feedback loop** -- Let users correct AI misclassifications to improve the rules engine
- **Incident deduplication** -- Detect and merge similar reports
- **Privacy-preserving location** -- Coarse neighborhood-level buckets (not GPS coordinates)
- **Rate limiting and abuse prevention** -- Protect against spam submissions
- **Export and reporting** -- CSV export for community group meetings

### Known limitations
- AI classification depends on prompt engineering; adversarial or ambiguous inputs may be miscategorized
- Keyword fallback is English-only and may not catch novel threat patterns
- SQLite is single-writer; would need PostgreSQL for concurrent production use
- No authentication means any user can update any incident's status
- No pagination on the incident feed (fine for prototype scale, not production)

---

## Responsible AI Considerations

- **Fallback by design:** The app never relies solely on AI. Every incident gets classified even if the model is down.
- **Transparency:** Each incident clearly shows whether analysis was AI-generated or rule-based.
- **User correction:** Users can manually override the AI-assigned category and status.
- **Synthetic data only:** No real personal data is collected, stored, or processed.
- **No precise location:** The system does not store GPS coordinates or precise addresses.
- **Calm framing:** Summaries and checklists are written to empower, not alarm.

---

## Video Demo

[Link to video will be added here]
