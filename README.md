# Community Guardian

An AI-powered community safety and digital wellness platform that helps users report, triage, and act on local safety incidents and digital threats.

**Candidate Name:** Pravir Chugh

**Scenario Chosen:** 3 - Community Safety & Digital Wellness

**Estimated Time Spent:** ~5.5 hours

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

## AI Disclosure

- **Did you use an AI assistant?** Yes -- Claude (Anthropic) for code generation and architecture decisions.
- **How did you verify the suggestions?** Manually reviewed all generated code, ran the full test suite (12 tests), and tested every flow in the browser. Verified AI classification output against expected categories. Investigated root causes for errors rather than applying quick fixes.
- **Example of a suggestion rejected or changed:** The AI assistant initially suggested making the low-signal warning a hard block (prevent submission entirely for brief reports). I rejected this because it contradicts responsible AI principles -- users should retain agency. Changed to an advisory warning with checkbox confirmation, allowing users to post low-signal reports if they explicitly choose to.

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
├── Audience-aware AI prompting (3 audience types)
├── Noise-to-signal filtering (heuristic-based)
└── Deterministic fallback rules engine
```

**Why this stack:**
- **FastAPI** -- Pydantic validation built-in, clear route structure, easy to test
- **SQLite** -- Zero configuration, single file, ideal for prototype scope
- **Jinja2 SSR** -- Avoids SPA complexity; the demo is straightforward to follow
- **Server-rendered HTML** -- No frontend build step, works immediately

### Core Flow

1. User submits an incident report (title + description + audience type)
2. Input is validated (title required, description min 10 chars)
3. **Low-signal check**: If description is too brief (< 30 chars or < 8 words), show advisory warning with confirmation checkbox
4. AI service classifies and summarizes the report with **audience-tailored** guidance
5. If AI fails or is unavailable, deterministic keyword rules take over
6. Incident is saved with category, severity, summary, and action checklist
7. User can view the feed, search/filter, and update incident status

---

## Key Features

### 1. AI Integration + Fallback

**AI Service:** Calls OpenAI GPT-3.5-turbo to produce a JSON response with category, severity, summary, and checklist -- tailored to the user's audience type.

**Fallback Rules Engine:** A keyword-matching classifier that maps incident text to categories (phishing, scam/fraud, network security, physical safety, identity theft) with canned checklists. This runs automatically when:
- No API key is configured
- The API returns an error or times out
- The response cannot be parsed

The fallback is **first-class** -- it was built before the AI service, and the app works fully without any API key. Each incident displays a badge indicating whether analysis was "AI Analyzed" or "Rule-Based," so users always know the source.

### 2. Audience-Aware AI Customization

Users select their audience type when reporting: **Neighborhood Group**, **Remote Worker**, or **Elderly User**. The AI tailors its response accordingly:

| Audience | Guidance Style | Example |
|----------|---------------|---------|
| **Elderly User** | Simple, step-by-step, mentions trusted family/friends | "Ask a family member or trusted friend to help check the computer" |
| **Remote Worker** | Technical security details, MFA, network hardening | "Enable hardware-key or app-based MFA on all work accounts" |
| **Neighborhood Group** | Community-focused, share awareness, report to authorities | "Alert your neighbors and local community group" |

### 3. Noise-to-Signal Filtering

Reports that are too brief trigger an advisory warning before saving:
- **Detection**: Description < 30 characters OR < 8 words
- **Warning**: "Report is quite brief. Adding more details helps us analyze better."
- **Confirmation**: Checkbox required -- "I understand and want to post this report anyway"
- **Non-blocking**: Users retain full agency to post if they choose

This improves feed quality without silencing users -- a responsible AI approach.

### 4. Search & Filter

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
| **Checklist** | Canned 4 steps per category | Tailored to incident details + audience |
| **Speed** | Instant | ~1-2 seconds (API call) |
| **Reliability** | Always works, no external dependency | Falls back to rules on any failure |

---

## Testing

12 tests covering four categories:

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_happy_path.py` | 6 | Create incident, view detail, filter by category, filter by audience, text search, audience-specific checklist, low-signal warning flow |
| `test_ai_fallback.py` | 2 | AI returns None -> fallback works; AI throws exception -> fallback works |
| `test_validation.py` | 4 | Empty description -> 422; empty title -> 422; nonexistent incident -> 404; status update works |

Tests use an in-memory SQLite database and TestClient, so they run in ~0.05s with no external dependencies.

---

## Synthetic Data

`data/incidents_seed.json` contains 10 synthetic incidents covering all categories, severities, statuses, and audience types. The database is automatically seeded on first startup. No real personal data is included.

---

## Tradeoffs & Prioritization

### What I cut to stay within the timebox
- **Authentication/authorization** -- Not needed to demonstrate the core triage flow
- **Semantic low-signal detection** -- Used simple character/word count heuristics instead of embeddings or sentiment analysis. Still effective, zero API overhead.
- **Map visualization** -- Would add complexity without demonstrating engineering rigor
- **Real-time notifications** -- Background job infrastructure is out of scope
- **Safe Circles messaging** -- Encryption and group features are a separate product slice
- **Mobile responsiveness** -- Clean but desktop-focused; mobile would need viewport meta tags and touch-friendly buttons

### What I would build next
- **Feed quality scoring** -- User upvote/downvote; low-signal reports with consistent downvotes get deprioritized
- **Semantic similarity detection** -- Use embeddings to identify and merge duplicate reports
- **Community validation** -- "Have you experienced this?" checkbox; 10+ confirmations get "Verified" badge
- **User feedback loop** -- Let users correct AI misclassifications to improve the rules engine
- **Notification system** -- Email/SMS alerts for high-severity incidents in user's area
- **Rate limiting and abuse prevention** -- Protect against spam submissions
- **User accounts & reputation** -- Track submission quality, award badges for helpful reports

### Known limitations
- AI classification depends on prompt engineering; adversarial or ambiguous inputs may be miscategorized
- Low-signal thresholds (30 chars / 8 words) are hardcoded; no dynamic tuning per category
- Keyword fallback is English-only and may not catch novel threat patterns
- SQLite is single-writer; would need PostgreSQL for concurrent production use
- No authentication means any user can update any incident's status
- No pagination on the incident feed (fine for prototype scale, not production)
- No audit trail for incident updates

---

## Responsible AI Considerations

- **Fallback by design:** The app never relies solely on AI. Every incident gets classified even if the model is down.
- **Transparency:** Each incident clearly shows whether analysis was AI-generated or rule-based.
- **User agency:** Low-signal warnings are advisory, not blocking. Users can always post if they confirm.
- **Audience awareness:** Guidance is tailored to user context -- simpler for elderly users, technical for remote workers.
- **User correction:** Users can manually override the AI-assigned category and status.
- **Synthetic data only:** No real personal data is collected, stored, or processed.
- **No precise location:** The system does not store GPS coordinates or precise addresses.
- **Calm framing:** Summaries and checklists are written to empower, not alarm.

---

## Design Documentation

See [DESIGN.md](DESIGN.md) for detailed architecture, implementation decisions, and future enhancement plans.

## Video Demo

[Link to video will be added here]
