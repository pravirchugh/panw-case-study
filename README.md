# Community Guardian

An AI-powered community safety and digital wellness platform that helps users report, triage, and act on local safety incidents.

---

**Candidate Name:** Pravir Chugh

**Scenario Chosen:** 3 — Community Safety & Digital Wellness

**Estimated Time Spent:** ~5.5 hours

**Video Link:** https://youtu.be/ca0tN935l9I

---

## Quick Start

**Prerequisites:**
- Python 3.11+
- (Optional) OpenAI API key for AI-powered analysis

**Run Commands:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY (optional — app works without it)
uvicorn app.main:app --reload  # visit http://127.0.0.1:8000
```

**Test Commands:**
```bash
source .venv/bin/activate
python -m pytest tests/ -v    # 12 tests, ~0.05s, no external dependencies
```

---

## AI Disclosure

- **Did you use an AI assistant?** Yes — Claude (Anthropic) for code generation and architecture decisions.
- **How did you verify the suggestions?** Manually reviewed all generated code, ran the full test suite (12 tests), and tested every feature end-to-end in the browser. Investigated root causes for errors rather than applying quick fixes.
- **Example of a suggestion rejected or changed:** The AI suggested making noise-to-signal filtering a hard block (prevent submission entirely for brief reports). I rejected this because it contradicts responsible AI principles — users should retain agency. Changed to a non-blocking advisory warning with a confirmation checkbox.

---

## Tradeoffs & Prioritization

**What did you cut to stay within the 4–6 hour limit?**
- User authentication — not needed to demonstrate the core triage flow
- Semantic low-signal detection (embeddings/sentiment) — used simple char/word count heuristics instead; still effective, zero API overhead
- Map visualization and geo-tagging — adds complexity without demonstrating engineering depth
- Real-time WebSocket notifications — background job infrastructure is out of scope
- Mobile responsiveness — clean but desktop-focused

**What would you build next if you had more time?**
- Feed quality scoring with user upvote/downvote
- Semantic similarity detection to merge duplicate reports
- Community validation ("Have you experienced this?" → Verified badge)
- User accounts, reputation tracking, and rate limiting
- Email/SMS alerts for high-severity incidents
- Incident trend timelines and geo-tagging

**Known limitations:**
- AI classification depends on prompt engineering; adversarial inputs may be miscategorized
- Low-signal thresholds (30 chars / 8 words) are hardcoded with no per-category tuning
- Keyword fallback is English-only
- SQLite is single-writer; needs PostgreSQL for concurrent production use
- No authentication — any user can update any incident's status
- No pagination on the incident feed

---

See **[DESIGN.md](DESIGN.md)** for full architecture, implementation details, and responsible AI considerations.
