from datetime import datetime, timezone

from extensions import db
from transparency import compute_delay_status, explain_stage


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    case_type = db.Column(db.String(120), nullable=False)
    filing_date = db.Column(db.String(40), nullable=False)
    current_stage = db.Column(db.String(120), nullable=False)
    stage_step = db.Column(db.Integer, nullable=False, default=1)
    plain_explanation = db.Column(db.Text, nullable=False, default="")
    adjournments_count = db.Column(db.Integer, nullable=False, default=0)
    delay_status = db.Column(db.String(64), nullable=False, default="On Track")
    next_hearing_date = db.Column(db.String(40), nullable=True)
    court_hall = db.Column(db.String(160), nullable=True)
    judge_name = db.Column(db.String(160), nullable=True)
    petitioner = db.Column(db.String(160), nullable=True)
    respondent = db.Column(db.String(160), nullable=True)

    # Litigant Vulnerability & Priority Metrics
    client_age = db.Column(db.Integer, default=45)
    client_working_years_left = db.Column(db.Integer, default=10)
    has_property = db.Column(db.Boolean, default=True)
    case_start_year = db.Column(db.Integer, nullable=False, default=2026)
    previous_queue_number = db.Column(db.Integer, default=0)
    previous_board_limit = db.Column(db.Integer, default=0)
    is_rollover_bumped = db.Column(db.Boolean, default=False)
    priority_score = db.Column(db.Float, default=0.0)
    scheduled_queue_number = db.Column(db.Integer, default=0)

    events = db.relationship(
        "CaseEvent",
        backref="case",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="CaseEvent.created_at.desc()",
    )

    def apply_transparency(self) -> None:
        insight = explain_stage(
            self.current_stage,
            adjournments_count=self.adjournments_count or 0,
            filing_date=self.filing_date,
        )
        self.plain_explanation = insight["explanation"]
        self.delay_status = insight["delay_status"]
        if not self.stage_step:
            self.stage_step = insight["stage_step"]
        else:
            self.stage_step = max(1, min(int(self.stage_step), 4))

    def recalc_delay_status(self) -> None:
        status, _reason = compute_delay_status(
            adjournments_count=self.adjournments_count or 0,
            stage_name=self.current_stage,
            filing_date=self.filing_date,
        )
        self.delay_status = status
        insight = explain_stage(
            self.current_stage,
            adjournments_count=self.adjournments_count or 0,
            filing_date=self.filing_date,
        )
        self.plain_explanation = insight["explanation"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "case_type": self.case_type,
            "filing_date": self.filing_date,
            "current_stage": self.current_stage,
            "stage_step": self.stage_step,
            "plain_explanation": self.plain_explanation,
            "adjournments_count": self.adjournments_count,
            "delay_status": self.delay_status,
            "next_hearing_date": self.next_hearing_date,
            "court_hall": self.court_hall,
            "judge_name": self.judge_name,
            "petitioner": self.petitioner,
            "respondent": self.respondent,
            "client_age": self.client_age,
            "client_working_years_left": self.client_working_years_left,
            "has_property": self.has_property,
            "case_start_year": self.case_start_year,
            "priority_score": self.priority_score,
            "scheduled_queue_number": self.scheduled_queue_number,
            "is_rollover_bumped": self.is_rollover_bumped,
        }


class CaseEvent(db.Model):
    __tablename__ = "case_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    case_id = db.Column(db.String(32), db.ForeignKey("cases.id"), nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
