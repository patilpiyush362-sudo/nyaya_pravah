from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func

from extensions import db
from models import Case, CaseEvent
from news_feed import get_latest_updates
from scheduler import generate_daily_cause_list
from seed import seed_if_empty
from transparency import STAGE_STEPS, explain_stage, stage_step_from_name

ROOT = Path(__file__).resolve().parent
INSTANCE = ROOT / "instance"
INSTANCE.mkdir(exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
    instance_path=str(INSTANCE),
)
app.config["SECRET_KEY"] = "nyaya-pravah-dev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(INSTANCE / "nyaya.db").replace("\\", "/")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def dashboard_metrics() -> dict:
    total = Case.query.count()
    avg_adj = db.session.query(func.avg(Case.adjournments_count)).scalar() or 0
    flagged = Case.query.filter(Case.delay_status.ilike("%High Delay Risk%")).count()  # type: ignore
    moderate = Case.query.filter(Case.delay_status.ilike("%Moderate%")).count()  # type: ignore
    
    # Count vulnerable citizens (senior age >= 60 OR no property OR limited working years)
    vulnerable_cases = Case.query.filter(
        (Case.client_age >= 60) | (Case.has_property == False) | (Case.client_working_years_left <= 3)
    ).count()
    
    # Count rollover-protected cases
    rollover_cases = Case.query.filter(Case.is_rollover_bumped == True).count()
    
    return {
        "total_cases": total,
        "avg_adjournments": round(float(avg_adj), 1),
        "high_delay": flagged,
        "watch_delay": moderate,
        "vulnerable_litigants": vulnerable_cases,
        "rollover_protected": rollover_cases,
    }


def next_case_id() -> str:
    year = datetime.now().year
    prefix = f"NP-{year}-"
    last = (
        Case.query.filter(Case.id.like(f"{prefix}%"))
        .order_by(Case.id.desc())
        .first()
    )
    if last:
        try:
            n = int(last.id.split("-")[-1]) + 1
        except ValueError:
            n = 101
    else:
        n = 101
    return f"{prefix}{n}"


def wants_json() -> bool:
    if request.is_json:
        return True
    accept = request.accept_mimetypes
    return accept.best == "application/json" and accept[accept.best] > accept["text/html"]


def payload_from_request() -> dict:
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return {k: (v if v is not None else "") for k, v in data.items()}
    return {key: request.form.get(key, "").strip() for key in request.form}


def build_case_from_payload(data: dict) -> Case:
    case_id = (data.get("id") or "").strip().upper() or next_case_id()
    stage = data.get("current_stage") or "Scrutiny"
    adj = int(data.get("adjournments_count") or 0)
    step = data.get("stage_step")
    try:
        step_n = int(step) if step not in (None, "") else stage_step_from_name(stage)
    except (TypeError, ValueError):
        step_n = stage_step_from_name(stage)

    case = Case(  # type: ignore
        id=case_id,  # type: ignore
        title=data.get("title") or "Untitled matter",  # type: ignore
        case_type=data.get("case_type") or "Civil",  # type: ignore
        filing_date=data.get("filing_date") or datetime.now().strftime("%d %b %Y"),  # type: ignore
        current_stage=stage,  # type: ignore
        stage_step=max(1, min(step_n, 4)),  # type: ignore
        adjournments_count=adj,  # type: ignore
        next_hearing_date=data.get("next_hearing_date") or "",  # type: ignore
        court_hall=data.get("court_hall") or "",  # type: ignore
        judge_name=data.get("judge_name") or "",  # type: ignore
        petitioner=data.get("petitioner") or "",  # type: ignore
        respondent=data.get("respondent") or "",  # type: ignore
    )
    case.apply_transparency()
    return case


def lookup_case(case_id: str | None) -> Case | None:
    if not case_id:
        return None
    return db.session.get(Case, case_id.strip().upper())


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        return track()
    return render_template(
        "dashboard.html",
        metrics=dashboard_metrics(),
        latest_news=get_latest_updates(limit=5),
        active="home",
    )


@app.route("/track", methods=["GET", "POST"])
@app.route("/track/<case_id>", methods=["GET"])
def track(case_id=None):
    searched = False
    case = None
    insight = None
    if request.method == "POST":
        searched = True
        cid = request.form.get("case_id", "").strip().upper()
        case = lookup_case(cid)
        if not case:
            flash(
                "No judicial record found matching the specified Case Tracking ID. "
                "Please verify the registration number.",
                "error",
            )
    else:
        cid = case_id or request.args.get("case_id", "")
        if cid:
            searched = True
            case = lookup_case(cid)
            if not case:
                flash("No judicial record found matching the specified Case Tracking ID.", "error")

    if case:
        insight = explain_stage(
            case.current_stage,
            adjournments_count=case.adjournments_count,
            filing_date=case.filing_date,
        )

    return render_template(
        "case_detail.html" if case else "dashboard.html",
        case=case,
        searched=searched,
        insight=insight,
        steps=STAGE_STEPS,
        metrics=dashboard_metrics(),
        active="home" if not case else "search",
        events=case.events if case else [],
    )


@app.route("/cases")
def list_cases():
    stage = request.args.get("stage", "").strip()
    court = request.args.get("court", "").strip()
    delay = request.args.get("delay", "").strip()

    query = Case.query
    if stage:
        step = _stage_to_step(stage)
        if step:
            query = query.filter(Case.stage_step == step)  # type: ignore
        else:
            query = query.filter(Case.current_stage.ilike(f"%{stage}%"))  # type: ignore
    if court:
        query = query.filter(Case.court_hall.ilike(f"%{court}%"))  # type: ignore
    if delay:
        query = query.filter(Case.delay_status.ilike(f"%{delay}%"))  # type: ignore

    cases = query.order_by(Case.id.asc()).all()
    courts = sorted(
        {c.court_hall for c in Case.query.all() if c.court_hall},
        key=str.lower,
    )
    return render_template(
        "cases.html",
        cases=cases,
        courts=courts,
        steps=STAGE_STEPS,
        filters={"stage": stage, "court": court, "delay": delay},
        active="cases",
    )


def _stage_to_step(stage: str):
    mapping = {name: i + 1 for i, name in enumerate(STAGE_STEPS)}
    return mapping.get(stage)


@app.route("/cases/new", methods=["GET", "POST"])
def new_case():
    if request.method == "POST":
        return create_case()
    return render_template(
        "new_case.html",
        steps=STAGE_STEPS,
        suggested_id=next_case_id(),
        active="new",
    )


@app.route("/api/cases", methods=["POST"])
def create_case():
    data = payload_from_request()
    title = (data.get("title") or "").strip()
    if not title:
        if wants_json() or request.is_json:
            return jsonify({"error": "title is required"}), 400
        flash("Case title is required.", "error")
        return redirect(url_for("new_case"))

    case = build_case_from_payload(data)
    if db.session.get(Case, case.id):
        if wants_json() or request.is_json:
            return jsonify({"error": f"Case {case.id} already exists"}), 409
        flash(f"Case {case.id} already exists. Choose another tracking ID.", "error")
        return redirect(url_for("new_case"))

    db.session.add(case)
    db.session.add(
        CaseEvent(  # type: ignore
            case_id=case.id,  # type: ignore
            event_type="Filed",  # type: ignore
            note=f"New matter submitted: {case.title}. Stage: {case.current_stage}.",  # type: ignore
        )
    )
    db.session.commit()

    if wants_json() or request.is_json:
        return jsonify(case.to_dict()), 201

    flash(f"Case {case.id} registered successfully.", "success")
    return redirect(url_for("track", case_id=case.id))


@app.route("/cases/<case_id>/adjourn", methods=["POST"])
def adjourn_case(case_id):
    case = lookup_case(case_id)
    if not case:
        flash("Cannot adjourn: case not found.", "error")
        return redirect(url_for("home"))

    case.adjournments_count = (case.adjournments_count or 0) + 1
    next_date = request.form.get("next_hearing_date", "").strip()
    if next_date:
        case.next_hearing_date = next_date
    case.recalc_delay_status()
    db.session.add(
        CaseEvent(  # type: ignore
            case_id=case.id,  # type: ignore
            event_type="Adjournment",  # type: ignore
            note=(  # type: ignore
                f"Hearing adjourned. Adjournments on record: {case.adjournments_count}. "
                f"Delay status: {case.delay_status}."
                + (f" Next date: {case.next_hearing_date}." if case.next_hearing_date else "")
            ),
        )
    )
    db.session.commit()
    flash(f"Adjournment logged for {case.id}. Delay status is now {case.delay_status}.", "success")
    return redirect(url_for("track", case_id=case.id))


@app.route("/cause-list")
def cause_list():
    """
    Display the daily cause list (hearing board) with prioritized cases.
    Supports filtering by court.
    """
    court_filter = request.args.get("court", "").strip()
    
    # Get all unique courts from database
    all_courts = sorted(
        {c.court_hall for c in Case.query.filter(Case.court_hall != None).all()},
        key=str.lower,
    )
    
    cause_data = None
    if court_filter:
        # Generate the prioritized cause list for the selected court
        cause_data = generate_daily_cause_list(court_filter)
        scheduled_cases = cause_data["scheduled_cases"]
    else:
        scheduled_cases = []
    
    return render_template(
        "cause_list.html",
        all_courts=all_courts,
        selected_court=court_filter,
        scheduled_cases=scheduled_cases,
        cause_data=cause_data,
        metrics=dashboard_metrics(),
        active="cause-list",
    )


@app.route("/api/cause-list/<court_name>")
def api_cause_list(court_name):
    """
    API endpoint to generate and return daily cause list as JSON.
    """
    cause_data = generate_daily_cause_list(court_name)
    
    return jsonify({
        "court": court_name,
        "today_capacity": cause_data["today_capacity"],
        "total_pending": cause_data["total_pending"],
        "rollover_count": cause_data["rollover_count"],
        "scheduled_count": len(cause_data["scheduled_cases"]),
        "cases": [
            {
                "rank": case.scheduled_queue_number,
                "case_id": case.id,
                "title": case.title,
                "petitioner": case.petitioner,
                "respondent": case.respondent,
                "priority_score": case.priority_score,
                "is_rollover": case.is_rollover_bumped,
                "client_age": case.client_age,
                "has_property": case.has_property,
            }
            for case in cause_data["scheduled_cases"]
        ]
    }), 200


with app.app_context():
    db.create_all()
    seed_if_empty()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
