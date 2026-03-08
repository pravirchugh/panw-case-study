# Community Guardian — Design Documentation

## Candidate Name:
Pravir Chugh

## Scenario Chosen:
**Scenario 3: Community Safety & Digital Wellness**

A community-driven incident reporting platform that empowers users to report local security threats and receive AI-powered, audience-specific safety guidance.

## Estimated Time Spent:
~5.5 hours

---

## Quick Start

### Prerequisites:
- Python 3.11+
- pip/venvg
- OpenAI API key (for AI-powered incident analysis)
- SQLite3 (included with Python)

### Run Commands:
```bash
# Clone and enter worktree
cd panw-case-study/.claude/worktrees/vigorous-fermi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key: OPENAI_API_KEY=sk-...

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: **http://localhost:8000**

### Test Commands:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_happy_path.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## AI Disclosure

### Did you use an AI assistant (Copilot, ChatGPT, etc.)?
**Yes** — Claude (Anthropic)

### How did you verify the suggestions?
1. **Read-before-implement**: Reviewed all generated code before writing to disk
2. **Test-driven validation**: All AI suggestions validated against existing test suite
3. **Manual E2E testing**: Tested each feature (create incident, filter, search, noise-to-signal warning) in browser
4. **Error investigation**: When issues arose (e.g., AttributeError with `request.form`), investigated root cause rather than applying quick fixes
5. **Code review**: Examined generated code against project patterns (FastAPI dependency injection, SQLAlchemy ORM, Jinja2 templating)

### Give one example of a suggestion you rejected or changed:
**Rejected**: Initial suggestion was to make the low-signal warning a hard block (prevent submission entirely).
**Why**: This contradicts responsible AI principles—users should retain agency. Changed to an advisory warning with checkbox confirmation, allowing users to post low-signal reports if they explicitly choose to, while encouraging refinement.

---

## Architecture & Design

### Tech Stack
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | FastAPI | Modern async Python framework, built-in dependency injection, excellent OpenAI integration |
| **Database** | SQLite + SQLAlchemy ORM | Lightweight, zero-setup, easy to ship; ORM prevents SQL injection |
| **Frontend** | Jinja2 templates + vanilla HTML/CSS | Server-side rendering for simplicity; no build step required |
| **AI** | OpenAI GPT-3.5-turbo | Natural language understanding for incident classification; graceful fallback to rule-based engine |
| **Testing** | pytest | Industry standard; fixtures for in-memory SQLite, easy async test support |
| **Deployment** | Docker-ready | Dockerfile included for production deployment |

### Core Features

#### 1. **Incident Reporting & AI Analysis**
- Users submit reports with title, description, and audience type (Neighborhood Group, Remote Worker, Elderly User)
- FastAPI route validates input, calls AI service to classify and generate guidance
- Graceful fallback to rule-based classifier if OpenAI API unavailable
- Returns structured response: category, severity, summary, audience-tailored checklist

**Design Decision**: Two-path analysis allows demo to work without API key while showcasing AI capability.

#### 2. **Audience-Aware AI Customization**
- Same incident gets different checklists based on audience type
- System prompt includes audience context: elderly users get simpler, step-by-step guidance; remote workers get technical security details
- Stored in database for consistency across feeds

**Example**:
- **Elderly User** sees: "Ask a family member or trusted friend for help"
- **Remote Worker** sees: "Enable MFA on all work accounts; rotate credentials if compromised"

#### 3. **Noise-to-Signal Filtering**
- Heuristic detection: flags reports < 30 characters OR < 8 words as "low-signal"
- User sees advisory warning before posting: "Report is quite brief. Adding more details helps us analyze better."
- Confirmation checkbox required: "I understand and want to post this report anyway"
- Form values persist if warning appears, allowing users to refine or confirm
- Non-blocking: users retain full agency to post venting/brief reports if they choose

**Responsible AI**: Improves feed quality without silencing users. Transparent about heuristic limitations.

#### 4. **Incident Feed**
- Homepage displays all incidents with filters: category, severity, status, audience
- Search by keyword in title/description
- Sort by date, with audience badge and classification confidence ("AI ANALYZED" vs "RULE-BASED")

#### 5. **Incident Detail & Management**
- View full incident with analysis, summary, and checklist
- Edit status (Open → Reviewed → Resolved) and category
- Seed data includes 10 realistic incidents spanning all categories and audiences

---

## Implementation Details

### Key Files & Responsibilities

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app setup, database initialization, seed data loading |
| `app/models.py` | SQLAlchemy `Incident` model with 13 columns (title, description, category, severity, status, summary, checklist, audience_type, ai_generated, is_low_signal, signal_quality_reason, created_at, updated_at) |
| `app/services/ai_service.py` | OpenAI API integration; returns classification + is_low_signal + reason |
| `app/services/fallback_rules.py` | Deterministic keyword-based classifier; used if OpenAI unavailable |
| `app/routes/incidents.py` | GET/POST handlers for feed, create, detail, update |
| `templates/` | Jinja2 templates: base.html, index.html (feed), create.html, detail.html |
| `static/style.css` | Minimalist CSS with warning/error box styling |
| `tests/test_happy_path.py` | 12 tests covering create, filter, search, audience-specific guidance, low-signal warning |
| `data/incidents_seed.json` | 10 seed incidents, all with good descriptions (none flagged as low-signal) |

### Low-Signal Detection Logic
```python
description_len = len(description.strip())
word_count = len(description.split())
is_low_signal = description_len < 30 or word_count < 8

# Thresholds chosen to catch venting/incomplete reports while allowing detailed complaints
# Example flagged: "Bad stuff." (10 chars, 2 words)
# Example NOT flagged: "I am frustrated!" (16 chars, 3 words) — but if they had 30 chars+ or 8+ words, would pass
```

### Fallback Rules Engine
Used when OpenAI unavailable (e.g., rate limit, network error, or no API key):
- Keyword-based classification (e.g., "phishing", "scam", "ransomware" → categories)
- Default severity: medium (safe default for safety/security context)
- Generic checklists per category (not audience-tailored without AI)
- Deterministic, fast, no API cost

---

## Tradeoffs & Prioritization

### What did you cut to stay within the 4–6 hour limit?

1. **Semantic-based low-signal detection**: Instead of using embeddings or sentiment analysis, used simple character/word count heuristics. Still effective, zero API overhead, deployable without ML infrastructure.

2. **User authentication**: Focused on core incident reporting. Authentication would add session management, login templates, password hashing—valuable but not essential for MVP demo.

3. **Edit incident after posting**: Users can only update status/category, not description. Full edit capability would require audit trails for responsible platforms, adding complexity.

4. **Filtering UI with advanced options**: Built simple category/severity/status dropdowns. Advanced filters (date range, incident score) left for future.

5. **Real-time WebSocket updates**: Feed is server-rendered. Real-time would require WebSocket infrastructure—premature for MVP.

6. **Mobile responsiveness**: Focused on desktop UX. Would need viewport meta tags, mobile CSS breakpoints, touch-friendly buttons.

### What would you build next if you had more time?

1. **Feed Quality Scoring**: Add "helpfulness" ratings. Users upvote/downvote incidents; low-signal reports with consistent downvotes get deprioritized (transparent, user-driven curation).

2. **Semantic Similarity Detection**: Use embeddings to identify duplicate or near-identical reports; suggest merging. Improves feed signal.

3. **Severity Auto-adjustment**: Train heuristic or model on user feedback. If low-signal reports are later confirmed critical, retrain weighting.

4. **Community Validation**: "Have you experienced this?" checkbox on each incident. Incidents with 10+ confirmations get "Verified" badge.

5. **Notification System**: Email/SMS alerts for high-severity incidents in user's area; unsubscribe controls.

6. **User Accounts & Reputation**: Track user submission quality, award badges for consistent helpful reports, penalize spam (spam score).

7. **Incident Timeline**: "This was reported X times in the last week; trend is [up/down]"—shows community pattern.

8. **Markdown Editor**: Rich text for descriptions; better formatting for checklists.

9. **Geo-tagging**: Filter by neighborhood/address (requires maps integration).

10. **Mobile App**: Native iOS/Android with push notifications, offline incident drafts.

### Known Limitations

1. **No Persistent User Identity**: Anyone can report; no account system. Mitigated by low-signal filter catching spam, but bad actors could bypass with detailed fake reports.

2. **AI Bias**: OpenAI model may reflect societal biases in security/safety perception. Low-signal heuristic is simple and rule-based, reducing bias but also reducing nuance.

3. **Hardcoded Thresholds**: Low-signal detection at 30 chars / 8 words is arbitrary. No dynamic threshold tuning based on category (e.g., "Attack in progress" is valid even at 5 words).

4. **No Rate Limiting**: No per-user or per-IP request limits. Vulnerable to spam floods.

5. **SQLite Concurrency**: SQLite is single-writer; under high concurrent load, will hit "database is locked" errors. Fine for MVP, needs PostgreSQL at scale.

6. **No Audit Trail**: Updates to incidents don't log who changed what. Important for responsibility platforms.

7. **CSS Not Optimized**: Inline styles in templates; no minification or caching headers. Works fine for MVP, not production-ready.

8. **Seed Data is Static**: All seeds are "good" descriptions. No low-signal seeds to demo the warning in a fresh install (though tests cover it).

---

## Responsible AI Considerations

### Design Principles Applied

1. **Transparency**: Low-signal detection uses simple, understandable heuristics (character count, word count). Not a black box.

2. **User Agency**: Warning is advisory, not blocking. Users can post low-signal reports if they choose; system doesn't make decision for them.

3. **Graceful Degradation**: Fallback classifier ensures app works without OpenAI; safety net, not critical dependency.

4. **Audience-Aware Tone**: System prompts adjust language complexity for elderly users—respects cognitive load without being patronizing.

5. **Minimal Data Collection**: No tracking, analytics, or telemetry in MVP. Incidents are public; no personal data beyond what users provide.

6. **Clear Limitations**: README and design doc acknowledge limitations; deployment instructions include warnings about at-scale needs.

---

## Testing Strategy

### Test Coverage (12 tests)
- **Happy path**: Create, view, filter, search
- **Audience-specific**: Elderly user checklist is simpler
- **Low-signal filtering**: Brief reports trigger warning; checkbox required
- **Filter & search**: Category, audience, keyword filters work correctly
- **Detail page**: Incident displays with all fields

### In-Memory SQLite
Tests use `sqlite:///:memory:` database, so each test runs in isolation without file I/O. Fast, clean, no cleanup needed.

### Fixtures
Custom pytest fixtures for FastAPI test client and database session, following FastAPI testing best practices.

---

## Deployment Notes

### Quick Local Dev
```bash
uvicorn app.main:app --reload
```

### Production (Docker)
```bash
docker build -t community-guardian .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... community-guardian
```

### Environment Variables
- `OPENAI_API_KEY`: Required for AI classification (optional; fallback rules used if missing)
- `DATABASE_URL`: Defaults to `sqlite:///community_guardian.db`; override for PostgreSQL

### Database Setup
Automatic on startup via `Base.metadata.create_all()` and seed loading. No manual migration steps needed.

---

## Summary

**Community Guardian** demonstrates a responsible, user-centric approach to community safety:
- **AI-powered but human-controlled**: Suggestions, not mandates
- **Accessible**: Audience-aware guidance meets users where they are
- **Transparent**: Heuristics are simple and explainable
- **Resilient**: Fallback classifier ensures functionality without external APIs
- **Testable**: 12 passing tests cover core flows and edge cases

The **noise-to-signal filtering** feature exemplifies responsible AI in practice: it improves feed quality without silencing users, giving full agency while nudging toward better signal. A balance between automation and user control.

**Time spent**: ~5.5 hours (architecture planning, implementation, testing, UI refinement, error debugging).

---

## References
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [OpenAI API](https://platform.openai.com/docs/)
- [pytest Docs](https://docs.pytest.org/)
