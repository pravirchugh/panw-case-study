"""
OpenAI-powered incident analyzer.

Calls GPT-3.5-turbo to summarize and categorize an incident report.
Tailors tone and advice based on the reporter's audience type.
Returns None on ANY failure so the caller can fall back to rule-based
classification.
"""

import json
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "phishing",
    "scam_fraud",
    "network_security",
    "physical_safety",
    "identity_theft",
    "other",
}
VALID_SEVERITIES = {"low", "medium", "high"}

AUDIENCE_TONE_INSTRUCTIONS = {
    "neighborhood_group": (
        "The reporter is part of a neighborhood community group. "
        "Use a calm, informative tone. Focus checklist steps on community-level "
        "actions: alerting neighbors, filing local reports, and collective awareness."
    ),
    "remote_worker": (
        "The reporter is a remote worker concerned about network security and home safety. "
        "Use a technically precise but accessible tone. Focus checklist steps on "
        "securing devices, networks, and digital accounts. Include specific technical "
        "actions like checking router settings, running scans, or enabling MFA."
    ),
    "elderly_user": (
        "The reporter is an elderly user who may be less familiar with technology. "
        "Use simple, reassuring language. Avoid jargon. Keep checklist steps short and "
        "very clear. Include a step about asking a trusted family member, friend, or "
        "official source for help. Emphasize that it is okay to ask for assistance."
    ),
}

BASE_SYSTEM_PROMPT = """You are a community safety analyst. Given an incident report, analyze it and return a JSON object with exactly these fields:

- "category": one of "phishing", "scam_fraud", "network_security", "physical_safety", "identity_theft", "other"
- "severity": one of "low", "medium", "high"
- "summary": 1-2 calm, factual sentences summarizing the incident
- "checklist": a JSON array of 3-4 short, actionable steps the reporter should take

{audience_instructions}

Return ONLY valid JSON, no markdown fences or extra text."""


def analyze_incident(description: str, audience_type: str = "neighborhood_group") -> dict | None:
    """
    Call OpenAI to classify and summarize an incident.

    Returns a dict with {category, severity, summary, checklist} on success,
    or None on any failure (missing key, API error, bad response, etc.).
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your-openai-api-key-here":
        logger.info("No valid OPENAI_API_KEY set; skipping AI analysis.")
        return None

    audience_instructions = AUDIENCE_TONE_INSTRUCTIONS.get(
        audience_type, AUDIENCE_TONE_INSTRUCTIONS["neighborhood_group"]
    )
    system_prompt = BASE_SYSTEM_PROMPT.format(audience_instructions=audience_instructions)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": description},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        raw = response.choices[0].message.content
        if not raw:
            logger.warning("Empty response from OpenAI.")
            return None

        # Strip markdown fences if the model wraps them anyway
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        data = json.loads(raw)

        # Validate required fields
        category = data.get("category", "other")
        severity = data.get("severity", "medium")
        summary = data.get("summary", "")
        checklist = data.get("checklist", [])

        if category not in VALID_CATEGORIES:
            category = "other"
        if severity not in VALID_SEVERITIES:
            severity = "medium"
        if not isinstance(checklist, list):
            checklist = [str(checklist)]

        # Detect low-signal reports (venting, too brief, etc.)
        desc_len = len(description.strip())
        word_count = len(description.split())
        is_low_signal = desc_len < 30 or word_count < 8

        signal_quality_reason = None
        if is_low_signal:
            if desc_len < 30:
                signal_quality_reason = "Report is quite brief. Adding more details helps us analyze better."
            else:
                signal_quality_reason = "Report lacks detail. Please describe the incident more thoroughly."

        return {
            "category": category,
            "severity": severity,
            "summary": summary,
            "checklist": json.dumps(checklist),
            "is_low_signal": is_low_signal,
            "signal_quality_reason": signal_quality_reason,
        }

    except Exception:
        logger.exception("AI analysis failed; will use fallback.")
        return None
