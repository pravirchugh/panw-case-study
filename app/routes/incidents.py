import json

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident
from app.schemas import VALID_CATEGORIES, VALID_SEVERITIES, VALID_STATUSES, IncidentCreate
from app.services.ai_service import analyze_incident
from app.services.fallback_rules import classify_incident

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def list_incidents(
    request: Request,
    q: str = Query("", description="Search text"),
    category: str = Query("", description="Filter by category"),
    severity: str = Query("", description="Filter by severity"),
    status: str = Query("", description="Filter by status"),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)

    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(Incident.title.ilike(term), Incident.description.ilike(term))
        )
    if category and category in VALID_CATEGORIES:
        query = query.filter(Incident.category == category)
    if severity and severity in VALID_SEVERITIES:
        query = query.filter(Incident.severity == severity)
    if status and status in VALID_STATUSES:
        query = query.filter(Incident.status == status)

    incidents = query.order_by(Incident.created_at.desc()).all()

    # Parse checklist JSON for display
    for inc in incidents:
        inc._checklist_items = json.loads(inc.checklist) if inc.checklist else []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "incidents": incidents,
            "q": q,
            "category": category,
            "severity": severity,
            "status": status,
            "categories": VALID_CATEGORIES,
            "severities": VALID_SEVERITIES,
            "statuses": VALID_STATUSES,
        },
    )


@router.get("/incidents/new", response_class=HTMLResponse)
def new_incident_form(request: Request):
    return templates.TemplateResponse(
        "create.html", {"request": request, "errors": [], "title": "", "description": ""}
    )


@router.post("/incidents", response_class=HTMLResponse)
def create_incident(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    # Validate input
    try:
        data = IncidentCreate(title=title, description=description)
    except ValidationError as e:
        errors = [err["msg"] for err in e.errors()]
        return templates.TemplateResponse(
            "create.html",
            {"request": request, "errors": errors, "title": title, "description": description},
            status_code=422,
        )

    # Try AI analysis first, fall back to rules
    try:
        ai_result = analyze_incident(data.description)
    except Exception:
        ai_result = None

    if ai_result is not None:
        analysis = ai_result
        ai_generated = True
    else:
        analysis = classify_incident(data.description)
        ai_generated = False

    incident = Incident(
        title=data.title,
        description=data.description,
        category=analysis["category"],
        severity=analysis["severity"],
        summary=analysis["summary"],
        checklist=analysis["checklist"],
        ai_generated=ai_generated,
        status="open",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return RedirectResponse(url=f"/incidents/{incident.id}", status_code=303)


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
def get_incident(request: Request, incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    checklist_items = json.loads(incident.checklist) if incident.checklist else []

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "incident": incident,
            "checklist_items": checklist_items,
            "statuses": VALID_STATUSES,
            "categories": VALID_CATEGORIES,
        },
    )


@router.post("/incidents/{incident_id}/update", response_class=HTMLResponse)
def update_incident(
    request: Request,
    incident_id: int,
    status: str = Form(None),
    category: str = Form(None),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if status and status in VALID_STATUSES:
        incident.status = status
    if category and category in VALID_CATEGORIES:
        incident.category = category

    db.commit()
    return RedirectResponse(url=f"/incidents/{incident_id}", status_code=303)
