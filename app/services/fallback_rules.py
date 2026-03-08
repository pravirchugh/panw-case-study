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
# Audience-specific checklist overrides
# ---------------------------------------------------------------------------
ELDERLY_CHECKLISTS: dict[str, list[str]] = {
    "phishing": [
        "Do not click any links in the message. Just close it.",
        "If you clicked a link or gave out information, ask a trusted family member or friend to help you change your password.",
        "Call your bank using the number on the back of your card to let them know.",
        "It is okay to ask for help. You can also call 211 for local support.",
    ],
    "scam_fraud": [
        "Hang up the phone or stop replying to the message right away.",
        "Do not send any money, gift cards, or personal details.",
        "Tell a family member or trusted friend what happened so they can help.",
        "You can report scams by calling 1-877-382-4357 (FTC helpline).",
    ],
    "network_security": [
        "Turn off your computer or disconnect from the internet for now.",
        "Ask a trusted family member or a local tech helper to check your device.",
        "Do not enter any passwords until someone you trust has looked at it.",
        "Write down what happened so you can share it with whoever helps you.",
    ],
    "identity_theft": [
        "Call your bank right away using the number on your card or statement.",
        "Ask a trusted family member to help you place a fraud alert on your credit.",
        "Do not share your Social Security number with anyone who contacts you.",
        "You can get free help at identitytheft.gov or by calling 1-877-438-4338.",
    ],
    "physical_safety": [
        "If you feel unsafe right now, call 911.",
        "Lock your doors and stay inside until help arrives.",
        "Ask a neighbor or family member to come stay with you if possible.",
        "When you feel safe, write down what you saw so you can tell the police.",
    ],
    "other": [
        "Write down what happened, including the date and time.",
        "Tell a trusted family member or friend about the situation.",
        "If you are unsure what to do, call 211 for free local help.",
        "It is okay to ask for help -- you do not need to handle this alone.",
    ],
}

REMOTE_WORKER_CHECKLISTS: dict[str, list[str]] = {
    "phishing": [
        "Do not click any links or download attachments. Forward the message to your IT/security team if applicable.",
        "If you entered credentials, change your password immediately and revoke any active sessions.",
        "Enable MFA on all work and personal accounts (use an authenticator app, not SMS).",
        "Check your email account's recent login activity for unauthorized access.",
    ],
    "scam_fraud": [
        "Stop all communication with the suspected scammer immediately.",
        "If you shared financial details, contact your bank and freeze the affected card.",
        "Report the scam to the FTC at reportfraud.ftc.gov and to your local authorities.",
        "Review recent transactions on all accounts for unauthorized charges.",
    ],
    "network_security": [
        "Disconnect the compromised device from your network immediately.",
        "Log into your router admin panel (typically 192.168.1.1) and change the Wi-Fi password and admin password.",
        "Run a full malware scan, update your router firmware, and disable WPS and remote management.",
        "Audit all devices on your network and change any passwords that were reused across services.",
    ],
    "identity_theft": [
        "Place a fraud alert or credit freeze with Equifax, Experian, and TransUnion immediately.",
        "Review your credit report at annualcreditreport.com for unauthorized accounts.",
        "File an identity theft report at identitytheft.gov and save the recovery plan.",
        "Set up transaction alerts on all bank accounts and credit cards.",
    ],
    "physical_safety": [
        "If you are in immediate danger, call 911.",
        "Review and update your home security setup (locks, cameras, motion lights).",
        "File a police report and save the case number for insurance or follow-up.",
        "Share the alert with neighbors via your community group or neighborhood app.",
    ],
    "other": [
        "Document the incident with timestamps, screenshots, and relevant details.",
        "Report it to the appropriate platform, authority, or your company's security team.",
        "Check whether any of your accounts or devices were affected.",
        "Monitor the situation and set up alerts for any related activity.",
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


AUDIENCE_CHECKLISTS: dict[str, dict[str, list[str]]] = {
    "neighborhood_group": CHECKLISTS,
    "remote_worker": REMOTE_WORKER_CHECKLISTS,
    "elderly_user": ELDERLY_CHECKLISTS,
}


def classify_incident(description: str, audience_type: str = "neighborhood_group") -> dict:
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

    # Select audience-appropriate checklist
    checklist_set = AUDIENCE_CHECKLISTS.get(audience_type, CHECKLISTS)

    return {
        "category": category,
        "severity": severity,
        "summary": SUMMARY_TEMPLATES[category],
        "checklist": json.dumps(checklist_set[category]),
    }
