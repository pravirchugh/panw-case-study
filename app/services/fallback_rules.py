"""
Deterministic keyword-based incident classifier.

Used as the primary fallback when the AI service is unavailable, returns an
error, or produces low-confidence output.  This guarantees the app always
returns a useful category, severity, summary, and action checklist.
"""

import json
import re

# ---------------------------------------------------------------------------
# Keyword → category mapping
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "phishing": [
        "phishing",
        "click link",
        "click the link",
        "verify account",
        "verify your account",
        "credential",
        "suspicious email",
        "fake email",
        "impersonat",
        "pretending to be",
        "login page",
        "enter your password",
        "confirm your identity",
    ],
    "scam_fraud": [
        "gift card",
        "irs",
        "urgent payment",
        "lottery",
        "prize",
        "wire transfer",
        "money order",
        "nigerian prince",
        "inheritance",
        "too good to be true",
        "send money",
        "pay immediately",
        "act now",
        "limited time",
        "congratulations you won",
    ],
    "network_security": [
        "wifi",
        "wi-fi",
        "router",
        "network",
        "firewall",
        "breach",
        "data breach",
        "vpn",
        "port scan",
        "malware",
        "ransomware",
        "ddos",
        "unauthorized access",
        "hacked",
        "compromised server",
    ],
    "identity_theft": [
        "social security",
        "ssn",
        "stolen identity",
        "credit report",
        "identity theft",
        "someone opened an account",
        "fraudulent charge",
        "credit card fraud",
        "personal information stolen",
    ],
    "physical_safety": [
        "break-in",
        "break in",
        "theft",
        "vandalism",
        "suspicious person",
        "trespassing",
        "stalking",
        "harassment",
        "assault",
        "gunshot",
        "robbery",
        "burglary",
        "property damage",
    ],
}

# Keywords that automatically escalate severity to "high"
HIGH_SEVERITY_KEYWORDS = [
    "breach",
    "ransomware",
    "ssn",
    "social security",
    "stolen identity",
    "assault",
    "gunshot",
    "robbery",
    "hacked",
    "compromised",
    "identity theft",
]

# ---------------------------------------------------------------------------
# Canned checklists per category
# ---------------------------------------------------------------------------
CHECKLISTS: dict[str, list[str]] = {
    "phishing": [
        "Do not click any links or download attachments from the suspicious message.",
        "If you already clicked, change your password immediately for the affected account.",
        "Enable multi-factor authentication (MFA) on your accounts.",
        "Report the phishing attempt to the impersonated organization via their official website.",
    ],
    "scam_fraud": [
        "Stop all communication with the suspected scammer immediately.",
        "Do not send money, gift cards, or personal information.",
        "Report the scam to the FTC at reportfraud.ftc.gov.",
        "Alert your bank or financial institution if you shared payment details.",
    ],
    "network_security": [
        "Disconnect the affected device from the network if you suspect active compromise.",
        "Change your Wi-Fi password and any reused passwords immediately.",
        "Run a full antivirus/malware scan on all connected devices.",
        "Check your router firmware for updates and disable remote management.",
    ],
    "identity_theft": [
        "Place a fraud alert or credit freeze with all three credit bureaus (Equifax, Experian, TransUnion).",
        "Review your credit report for any unauthorized accounts or inquiries.",
        "File an identity theft report at identitytheft.gov.",
        "Monitor your bank and credit card statements closely for unfamiliar charges.",
    ],
    "physical_safety": [
        "If you are in immediate danger, call 911 or your local emergency number.",
        "Document the incident with photos, timestamps, and descriptions.",
        "File a report with your local police department.",
        "Alert neighbors or community members to increase awareness.",
    ],
    "other": [
        "Document the incident with as much detail as possible.",
        "Report it to the appropriate local authority or platform.",
        "Monitor the situation for any further developments.",
        "Consider reaching out to community support resources for guidance.",
    ],
}

# ---------------------------------------------------------------------------
# Summary templates per category
# ---------------------------------------------------------------------------
SUMMARY_TEMPLATES: dict[str, str] = {
    "phishing": (
        "This report describes a possible phishing attempt designed to steal "
        "credentials or personal information. Exercise caution and avoid "
        "interacting with the suspicious message."
    ),
    "scam_fraud": (
        "This report describes a potential scam or fraud attempt seeking money "
        "or sensitive information. Do not engage with the requester."
    ),
    "network_security": (
        "This report describes a potential network or cybersecurity threat. "
        "Investigate affected systems and secure network access promptly."
    ),
    "identity_theft": (
        "This report indicates possible identity theft or unauthorized use of "
        "personal information. Take immediate steps to secure your accounts "
        "and credit."
    ),
    "physical_safety": (
        "This report describes a physical safety concern in the community. "
        "Prioritize personal safety and contact local authorities if needed."
    ),
    "other": (
        "This report has been logged for review. Monitor the situation and "
        "report any new developments."
    ),
}


def classify_incident(description: str) -> dict:
    """Return {category, severity, summary, checklist} using keyword rules."""
    text = description.lower()

    # Score each category by counting keyword matches
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    # Pick the highest-scoring category, default to "other"
    if scores:
        category = max(scores, key=scores.get)  # type: ignore[arg-type]
        total_hits = scores[category]
    else:
        category = "other"
        total_hits = 0

    # Determine severity
    has_high_kw = any(kw in text for kw in HIGH_SEVERITY_KEYWORDS)
    if has_high_kw or total_hits >= 3:
        severity = "high"
    elif total_hits == 0:
        severity = "low"
    else:
        severity = "medium"

    return {
        "category": category,
        "severity": severity,
        "summary": SUMMARY_TEMPLATES[category],
        "checklist": json.dumps(CHECKLISTS[category]),
    }
