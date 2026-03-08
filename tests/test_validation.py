"""Validation tests: empty/invalid input returns errors, not crashes."""


def test_empty_description_returns_error(client):
    """Submitting with a too-short description returns 422 with error message."""
    response = client.post(
        "/incidents",
        data={"title": "Test incident", "description": "short"},
        follow_redirects=True,
    )
    assert response.status_code == 422
    assert "at least 10 characters" in response.text.lower()


def test_empty_title_returns_error(client):
    """Submitting with an empty title returns 422 with error message."""
    response = client.post(
        "/incidents",
        data={"title": "", "description": "This is a valid description with enough characters."},
        follow_redirects=True,
    )
    assert response.status_code == 422
    assert "required" in response.text.lower() or "title" in response.text.lower()


def test_invalid_audience_type_returns_error(client):
    """Submitting with an invalid audience type returns 422 with error message."""
    response = client.post(
        "/incidents",
        data={
            "title": "Test incident",
            "description": "This is a valid description with enough characters.",
            "audience_type": "invalid_audience",
        },
        follow_redirects=True,
    )
    assert response.status_code == 422
    assert "audience" in response.text.lower()


def test_nonexistent_incident_returns_404(client):
    """Accessing an incident that doesn't exist returns 404."""
    response = client.get("/incidents/99999")
    assert response.status_code == 404
