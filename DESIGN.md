# Community Guardian — Design Documentation

## Overview

Community Guardian is a community-driven incident reporting platform for **Scenario 3: Community Safety & Digital Wellness**. It empowers users to report local security threats and receive AI-powered, audience-specific safety guidance — while maintaining transparency, user agency, and graceful degradation.

The core thesis: **turn noisy community reports into calm, actionable guidance** — tailored to who's reading it.

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (User)                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Feed UI  │  │ Report Form  │  │   Incident Detail     │  │
│  │ (filter, │  │ (title, desc │  │   (summary, checklist │  │
│  │  search) │  │  audience)   │  │    status update)     │  │
│  └────┬─────┘  └──────┬───────┘  └───────────┬───────────┘  │
└───────┼───────────────┼──────────────────────┼──────────────┘
        │               │                      │
        ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Routes (app/routes/incidents.py)        │    │
│  │  GET /           — incident feed with filters       │    │
│  │  GET /incidents/new — report form                   │    │
│  │  POST /incidents   — create (with low-signal check) │    │
│  │  GET /incidents/:id — detail view                   │    │
│  │  POST /incidents/:id/update — status/category edit  │    │
│  └──────────────┬──────────────────────────────────────┘    │
│                 │                                           │
│      ┌──────────┴──────────┐                                │
│      ▼                     ▼                                │
│  ┌────────────┐    ┌───────────────┐                        │
│  │ AI Service │    │ Fallback Rules│                        │
│  │ (OpenAI    │───▶│ (keyword      │  ← automatic fallback  │
│  │  GPT-3.5)  │    │  classifier)  │                        │
│  └────────────┘    └───────────────┘                        │
│         │                  │                                │
│         ▼                  ▼                                │
│  ┌─────────────────────────────────────┐                    │
│  │  Low-Signal Detection (heuristic)   │                    │
│  │  < 30 chars OR < 8 words → warning  │                    │
│  └─────────────────────────────────────┘                    │
│                 │                                           │
│                 ▼                                           │
│  ┌─────────────────────────────────────┐                    │
│  │    SQLite + SQLAlchemy ORM          │                    │
│  │    (community_guardian.db)           │                    │
│  └─────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | FastAPI (Python 3.11) | Modern async framework; built-in Pydantic validation, dependency injection, Form() parameter extraction |
| **Database** | SQLite + SQLAlchemy ORM | Zero-config, single-file storage; ORM prevents SQL injection; easy to swap to PostgreSQL |
| **Frontend** | Jinja2 SSR + vanilla HTML/CSS | Server-side rendering avoids SPA complexity; no build step; straightforward to follow in demo |
| **AI** | OpenAI GPT-3.5-turbo | Natural language understanding for classification + summary generation; structured JSON output |
| **Testing** | pytest + in-memory SQLite | Fast isolation; fixtures for test client and DB session; no external dependencies |

### Why Not [Alternative]?

| Decision | Alternative Considered | Why I Chose This |
|----------|----------------------|------------------|
| FastAPI over Flask | Flask is more common | FastAPI's dependency injection (`Form()`, `Depends()`) makes form handling and DB sessions cleaner |
| SQLite over PostgreSQL | PostgreSQL for production | Zero-config setup; reviewer can `pip install` and run immediately; fine for prototype scale |
| SSR over React SPA | React would look more polished | Adds build tooling (Node, Webpack/Vite), doubles complexity; SSR keeps focus on backend engineering |
| GPT-3.5 over GPT-4 | GPT-4 for better classification | 3.5 is faster, cheaper, sufficient for structured classification; 4 would be premature optimization |
| Heuristic over ML for low-signal | Train a classifier | No training data available; heuristic is transparent, explainable, zero-cost; can upgrade later |

---

## Feature Deep Dives

### 1. Dual-Path Analysis (AI + Fallback)

The system never depends solely on AI. Every incident gets analyzed, guaranteed.

**AI Path** (`app/services/ai_service.py`):
- Constructs a system prompt with audience context and category constraints
- Sends user's description to GPT-3.5-turbo requesting structured JSON
- Parses response into: `category`, `severity`, `summary`, `checklist`
- Wraps entire call in try/except — any failure triggers fallback

**Fallback Path** (`app/services/fallback_rules.py`):
- Keyword-matching classifier: scans description for category indicators
  - "phishing", "fake email", "suspicious link" → `phishing`
  - "scam", "fraud", "money" → `scam_fraud`
  - "ransomware", "malware", "hacked" → `network_security`
  - "break-in", "vandalism", "theft" → `physical_safety`
  - "identity", "SSN", "credit card" → `identity_theft`
- Default severity: `medium` (safe default for safety context)
- Pre-built checklists per category (4 steps each)
- Deterministic, instant, zero API cost

**Design Decision**: The fallback was built *first*, before the AI service. This ensures the app is always functional and the AI is a *enhancement*, not a dependency. Each incident displays a badge ("AI ANALYZED" / "RULE-BASED") so users always know the source of the analysis.

### 2. Audience-Aware AI Customization

The same phishing incident generates different guidance depending on who's reading:

**Implementation**: The AI system prompt includes an audience-specific instruction block:

```
Audience: elderly_user
→ "Use simple, clear language. Avoid technical jargon.
   Suggest asking a trusted family member or friend for help.
   Keep checklist steps short and numbered."

Audience: remote_worker
→ "Include technical security details.
   Reference MFA, VPN, network hardening.
   Assume familiarity with IT concepts."

Audience: neighborhood_group
→ "Focus on community awareness and mutual aid.
   Suggest sharing with neighbors and local authorities.
   Emphasize collective safety."
```

**Why This Matters**: A 75-year-old receiving a scam call needs "Call your grandson to help check your bank statement." A remote worker needs "Enable hardware-key MFA and rotate your API credentials." Same threat, radically different actionable guidance.

**Database Storage**: `audience_type` is stored per incident, so the feed can filter by audience and display the appropriate badge.

### 3. Noise-to-Signal Filtering

**Problem**: Community feeds get polluted with venting ("THIS SUCKS!!!"), incomplete reports ("bad email"), and panic posts that don't contain actionable information.

**Solution**: Heuristic-based pre-submission advisory.

**Detection Logic**:
```python
desc_len = len(description.strip())
word_count = len(description.split())
is_low_signal = desc_len < 30 or word_count < 8
```

**UX Flow**:
```
User submits brief report → Server detects low-signal
  → Re-render form with:
    ├── Yellow warning box: "Report is quite brief..."
    ├── Form values preserved (no data loss)
    └── Checkbox: "I understand and want to post anyway"
  → User can either:
    ├── Refine description and resubmit (no checkbox needed)
    └── Check box and submit as-is (saved with is_low_signal=true)
```

**Technical Challenge**: FastAPI's `request.form` is async, so you can't call `request.form.get()` in a synchronous handler. Solved by using FastAPI's `Form()` dependency with alias:
```python
confirm_low_signal: str = Form(default="", alias="_confirm_low_signal")
```
This extracts the form field at the parameter level, making it available synchronously.

**Why Non-Blocking**: Hard-blocking brief reports would:
- Silence legitimate urgent alerts ("Active shooter at park" = 5 words but critical)
- Frustrate users who feel censored
- Undermine trust in the platform

Instead, the advisory approach nudges toward quality while preserving agency.

### 4. Search & Filter System

**Implementation**: Server-side filtering via SQLAlchemy query building:
```python
query = db.query(Incident)
if category: query = query.filter(Incident.category == category)
if severity: query = query.filter(Incident.severity == severity)
if status:   query = query.filter(Incident.status == status)
if audience: query = query.filter(Incident.audience_type == audience)
if search:   query = query.filter(
    or_(Incident.title.ilike(f"%{search}%"),
        Incident.description.ilike(f"%{search}%"))
)
```

Filters are additive (AND logic) with text search across title + description.

---

## Data Model

### Incident Table (13 columns)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer (PK) | Auto-increment primary key |
| `title` | String(200) | Short incident headline |
| `description` | Text | Full incident description from user |
| `category` | String(50) | AI/fallback classification: phishing, scam_fraud, network_security, physical_safety, identity_theft, other |
| `severity` | String(20) | low / medium / high |
| `status` | String(20) | open / reviewed / resolved |
| `summary` | Text | AI-generated or template summary |
| `checklist` | Text (JSON) | JSON array of action items |
| `audience_type` | String(50) | neighborhood_group / remote_worker / elderly_user |
| `ai_generated` | Boolean | true = AI analyzed, false = rule-based fallback |
| `is_low_signal` | Boolean | true = user confirmed a low-signal report |
| `signal_quality_reason` | String(255) | Human-readable reason if low-signal (nullable) |
| `created_at` | DateTime | Auto-set on creation |
| `updated_at` | DateTime | Auto-set on creation and update |

### Seed Data

`data/incidents_seed.json` contains 10 synthetic incidents:
- 2 per category (phishing, scam_fraud, network_security, physical_safety, identity_theft)
- Mix of severities (low, medium, high) and statuses (open, reviewed, resolved)
- Distributed across all 3 audience types
- All have substantive descriptions (none flagged as low-signal)
- Auto-loaded on first startup; skipped if data already exists

---

## File Structure

```
panw-case-study/
├── app/
│   ├── main.py                    # FastAPI app, DB init, seed loader
│   ├── models.py                  # SQLAlchemy Incident model
│   ├── database.py                # DB engine, session, Base
│   ├── routes/
│   │   └── incidents.py           # All route handlers (GET/POST)
│   └── services/
│       ├── ai_service.py          # OpenAI integration + low-signal detection
│       └── fallback_rules.py      # Keyword classifier + low-signal detection
├── templates/
│   ├── base.html                  # Layout with nav, footer
│   ├── index.html                 # Incident feed with filters
│   ├── create.html                # Report form + warning UI
│   └── detail.html                # Incident detail + status update
├── static/
│   └── style.css                  # Minimal CSS (warning/error boxes)
├── data/
│   └── incidents_seed.json        # 10 synthetic incidents
├── tests/
│   └── test_happy_path.py         # 12 tests
├── requirements.txt
├── .env.example
├── Dockerfile
├── README.md                      # Quick reference (template format)
└── DESIGN.md                      # This file
```

---

## Testing Strategy

### Coverage: 12 Tests

| Category | Tests | What's Verified |
|----------|-------|-----------------|
| **Create & View** | 3 | Submit incident → saved → detail page renders with all fields |
| **Filter & Search** | 3 | Category filter, audience filter, keyword search all return correct subsets |
| **Audience-Specific** | 2 | Elderly user gets simpler checklist; different audiences get different guidance |
| **Low-Signal Flow** | 2 | Brief report shows warning; checkbox confirmation allows save |
| **Fallback** | 2 | AI returns None → fallback works; AI throws exception → fallback works |

### Test Infrastructure
- **In-memory SQLite**: `sqlite:///:memory:` — each test is isolated, no file I/O
- **Fixture override**: `get_db` dependency overridden with test session
- **TestClient**: Synchronous HTTP client wrapping the FastAPI app
- **No mocking of AI**: Tests use fallback path (no API key in test env) — validates real behavior

### Running
```bash
pytest tests/ -v                          # all tests
pytest tests/test_happy_path.py -v        # specific file
pytest tests/ --cov=app --cov-report=html # with coverage
```

---

## Responsible AI Considerations

### 1. Transparency
- Every incident shows "AI ANALYZED" or "RULE-BASED" badge — users always know the source
- Low-signal detection uses simple, explainable heuristics (character count, word count)
- No hidden scoring or opaque ML models

### 2. User Agency
- Low-signal warning is advisory, never blocking
- Users can override AI-assigned category and status
- Confirmation checkbox is explicit consent, not a trick

### 3. Graceful Degradation
- App works fully without OpenAI API key
- Fallback classifier was built first, AI layered on top
- Network errors, rate limits, malformed responses all handled silently

### 4. Audience-Aware Tone
- System prompts adjust language complexity per audience
- Elderly users get simpler steps; remote workers get technical details
- Respects cognitive load without being patronizing

### 5. Bias Awareness
- OpenAI may reflect societal biases in security perception
- Heuristic low-signal filter is rule-based, reducing (but not eliminating) bias risk
- Hardcoded thresholds may disadvantage terse but valid reports (acknowledged limitation)

### 6. Data Minimization
- No user tracking, analytics, or telemetry
- No authentication = no user profiles stored
- Incidents contain only what the user explicitly provides
- Synthetic seed data only — no real personal data

---

## Deployment

### Local Development
```bash
uvicorn app.main:app --reload
```

### Docker
```bash
docker build -t community-guardian .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... community-guardian
```

### Environment Variables
| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | No | None | Enables AI classification; fallback used if missing |
| `DATABASE_URL` | No | `sqlite:///community_guardian.db` | Override for PostgreSQL in production |

### Database
- Auto-created on startup via `Base.metadata.create_all()`
- Auto-seeded with 10 incidents if table is empty
- No manual migration steps required

---

## Future Enhancements

### Short-Term (Next Sprint)
1. **Feed quality scoring** — upvote/downvote; deprioritize consistently-downvoted low-signal reports
2. **Rate limiting** — per-IP throttling to prevent spam floods
3. **Pagination** — cursor-based pagination for feeds with 100+ incidents
4. **User authentication** — session-based login; track who reported what

### Medium-Term (Next Month)
5. **Semantic similarity detection** — embeddings to identify and merge duplicate reports
6. **Community validation** — "Have you experienced this?" → Verified badge at 10+ confirmations
7. **Severity auto-adjustment** — retrain weighting if low-signal reports are later confirmed critical
8. **Notification system** — email/SMS alerts for high-severity incidents; unsubscribe controls

### Long-Term (V2)
9. **Geo-tagging** — filter by neighborhood (coarse, privacy-preserving buckets)
10. **Incident timeline** — "Reported X times this week; trend is up/down"
11. **User reputation** — submission quality tracking; badges for helpful reporters
12. **Mobile app** — native iOS/Android with push notifications and offline drafts
13. **Multi-language support** — fallback keywords and AI prompts in Spanish, Mandarin, etc.
14. **Markdown editor** — rich text descriptions with better formatting

---

## Summary

Community Guardian demonstrates a responsible, user-centric approach to community safety:

- **AI-powered but human-controlled**: Suggestions, not mandates
- **Accessible**: Audience-aware guidance meets users where they are
- **Transparent**: Heuristics are simple and explainable; AI vs rule-based is always visible
- **Resilient**: Fallback classifier ensures the app works without external APIs
- **Testable**: 12 passing tests cover core flows and edge cases

The **noise-to-signal filtering** exemplifies responsible AI: it improves feed quality without silencing users, giving full agency while nudging toward better signal.
