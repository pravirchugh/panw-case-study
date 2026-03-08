from pydantic import BaseModel, field_validator

VALID_CATEGORIES = [
    "phishing",
    "scam_fraud",
    "network_security",
    "physical_safety",
    "identity_theft",
    "other",
]
VALID_SEVERITIES = ["low", "medium", "high"]
VALID_STATUSES = ["open", "reviewed", "resolved"]
VALID_AUDIENCES = ["neighborhood_group", "remote_worker", "elderly_user"]
AUDIENCE_LABELS = {
    "neighborhood_group": "Neighborhood Group",
    "remote_worker": "Remote Worker",
    "elderly_user": "Elderly User",
}


class IncidentCreate(BaseModel):
    title: str
    description: str
    audience_type: str = "neighborhood_group"

    @field_validator("audience_type")
    @classmethod
    def valid_audience(cls, v: str) -> str:
        if v not in VALID_AUDIENCES:
            raise ValueError(f"Audience must be one of: {', '.join(VALID_AUDIENCES)}")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required.")
        if len(v) > 200:
            raise ValueError("Title must be 200 characters or fewer.")
        return v

    @field_validator("description")
    @classmethod
    def description_min_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters.")
        return v


class IncidentUpdate(BaseModel):
    status: str | None = None
    category: str | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return v
