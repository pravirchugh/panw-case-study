"""Happy-path tests: create an incident, view it, filter the feed."""


def test_create_and_view_incident(client):
    """Submit a valid incident, verify redirect and detail page content."""
    # Create
    response = client.post(
        "/incidents",
        data={
            "title": "Suspicious email from unknown sender",
            "description": "Received an email asking me to click a link and verify my bank account credentials. The sender address looks fake.",
            "audience_type": "remote_worker",
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
            "audience_type": "neighborhood_group",
        },
        follow_redirects=True,
    )

    # Physical safety incident
    client.post(
        "/incidents",
        data={
            "title": "Break-in at nearby store",
            "description": "There was a break-in and theft at the corner store last night. Windows were smashed.",
            "audience_type": "neighborhood_group",
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
            "audience_type": "remote_worker",
        },
        follow_redirects=True,
    )

    response = client.get("/?q=router")
    assert response.status_code == 200
    assert "Router compromised" in response.text

    response = client.get("/?q=nonexistent_term_xyz")
    assert response.status_code == 200
    assert "Router compromised" not in response.text


def test_audience_specific_checklist(client):
    """Elderly user audience produces simpler, tailored checklist items."""
    response = client.post(
        "/incidents",
        data={
            "title": "Suspicious phone call about gift cards",
            "description": "Someone called claiming I owe money to the IRS and must pay with gift cards immediately or face arrest.",
            "audience_type": "elderly_user",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Elderly checklists should mention asking for help from trusted people
    assert "trusted" in response.text.lower() or "family" in response.text.lower()
    # Should show the Elderly User audience badge
    assert "Elderly User" in response.text
