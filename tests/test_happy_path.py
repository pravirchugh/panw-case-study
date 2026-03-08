"""Happy-path tests: create an incident, view it, filter the feed."""


def test_create_and_view_incident(client):
    """Submit a valid incident, verify redirect and detail page content."""
    # Create
    response = client.post(
        "/incidents",
        data={
            "title": "Suspicious email from unknown sender",
            "description": "Received an email asking me to click a link and verify my bank account credentials. The sender address looks fake.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/incidents/")

    # View detail
    detail = client.get(location)
    assert detail.status_code == 200
    assert "Suspicious email from unknown sender" in detail.text
    assert "phishing" in detail.text.lower() or "Phishing" in detail.text

    # Verify it appears in the feed
    feed = client.get("/")
    assert feed.status_code == 200
    assert "Suspicious email from unknown sender" in feed.text


def test_filter_by_category(client):
    """Create two incidents with different categories, filter returns correct one."""
    # Phishing incident
    client.post(
        "/incidents",
        data={
            "title": "Phishing text message",
            "description": "Got a text pretending to be my bank asking me to click a link to verify my account.",
        },
        follow_redirects=True,
    )

    # Physical safety incident
    client.post(
        "/incidents",
        data={
            "title": "Break-in at nearby store",
            "description": "There was a break-in and theft at the corner store last night. Windows were smashed.",
        },
        follow_redirects=True,
    )

    # Filter by physical_safety
    response = client.get("/?category=physical_safety")
    assert response.status_code == 200
    assert "Break-in at nearby store" in response.text
    # Phishing incident should not appear when filtering for physical safety
    assert "Phishing text message" not in response.text


def test_search_incidents(client):
    """Text search matches on title and description."""
    client.post(
        "/incidents",
        data={
            "title": "Router compromised",
            "description": "Unknown devices appeared on my home wifi network. Someone may have hacked the router.",
        },
        follow_redirects=True,
    )

    response = client.get("/?q=router")
    assert response.status_code == 200
    assert "Router compromised" in response.text

    response = client.get("/?q=nonexistent_term_xyz")
    assert response.status_code == 200
    assert "Router compromised" not in response.text
