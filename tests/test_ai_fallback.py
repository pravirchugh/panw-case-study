"""Edge-case test: AI service unavailable, fallback rules produce a valid result."""

from unittest.mock import patch


def test_fallback_when_ai_unavailable(client):
    """When AI service returns None, the app still classifies via rules."""
    with patch("app.routes.incidents.analyze_incident", return_value=None):
        response = client.post(
            "/incidents",
            data={
                "title": "Gift card scam phone call",
                "description": "Someone called claiming I owe money to the IRS and must pay immediately with gift cards or face arrest. This is clearly a scam.",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    # Should have been classified by fallback rules
    assert "Rule-Based" in response.text or "rule-based" in response.text.lower()
    # Should be categorized as scam/fraud based on keywords
    assert "scam" in response.text.lower() or "fraud" in response.text.lower()
    # Should have a checklist
    assert "Recommended Actions" in response.text


def test_fallback_when_ai_raises_exception(client):
    """When AI service throws an exception, fallback still works."""
    with patch(
        "app.routes.incidents.analyze_incident",
        side_effect=Exception("API connection timeout"),
    ):
        response = client.post(
            "/incidents",
            data={
                "title": "Ransomware attack on local business",
                "description": "A local business was hit by ransomware. Their systems are locked and attackers demand cryptocurrency payment. The business has been hacked.",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Rule-Based" in response.text or "rule-based" in response.text.lower()
    # Network security keywords should be detected
    assert "network" in response.text.lower() or "security" in response.text.lower()
