from models import Case, CaseEvent
from extensions import db
from transparency import explain_stage, stage_step_from_name


def _case(**kwargs) -> Case:
    stage = kwargs["current_stage"]
    adj = kwargs.get("adjournments_count", 0)
    insight = explain_stage(stage, adjournments_count=adj, filing_date=kwargs.get("filing_date"))
    kwargs.setdefault("stage_step", kwargs.get("stage_step") or stage_step_from_name(stage))
    kwargs.setdefault("plain_explanation", insight["explanation"])
    kwargs.setdefault("delay_status", insight["delay_status"])
    return Case(**kwargs)


def seed_if_empty() -> None:
    if Case.query.count() > 0:
        return

    samples = [
        # Regular case: established business owner, healthy timeline
        _case(
            id="NP-2026-101",
            title="M/s Sharma Enterprises vs. State of Maharashtra",
            case_type="Civil Writ Petition (CWP)",
            filing_date="14 Jan 2026",
            current_stage="Evidence & Arguments",
            stage_step=3,
            adjournments_count=1,
            next_hearing_date="12 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice S. K. Deshmukh",
            petitioner="Rajesh Sharma",
            respondent="State Revenue Department",
            client_age=48,
            client_working_years_left=15,
            has_property=True,
            case_start_year=2026,
        ),
        # Criminal case: young, recent filing
        _case(
            id="NP-2026-102",
            title="State of Maharashtra vs. Sandeep Varma & Ors.",
            case_type="Criminal Regular (CR)",
            filing_date="03 Feb 2026",
            current_stage="Police Report & Verification",
            stage_step=1,
            adjournments_count=0,
            next_hearing_date="18 Sep 2026",
            court_hall="Sessions Court, Kalyan Division",
            judge_name="District Judge K. R. Joshi",
            petitioner="State of Maharashtra",
            respondent="Sandeep Varma",
            client_age=35,
            client_working_years_left=27,
            has_property=True,
            case_start_year=2026,
        ),
        # Vulnerable case: senior citizen, landless, pending long
        _case(
            id="NP-2026-103",
            title="Anita Desai vs. Municipal Corporation of Greater Mumbai",
            case_type="Civil",
            filing_date="20 Nov 2025",
            current_stage="Notice under Order V CPC",
            stage_step=2,
            adjournments_count=2,
            next_hearing_date="05 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Judge P. N. Kulkarni",
            petitioner="Anita Desai",
            respondent="MCGM",
            client_age=68,  # Senior citizen: +20 points
            client_working_years_left=2,  # Service limit: +15 points
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2025,  # 1 year old: +10 points
            previous_queue_number=45,  # Was listed but not reached
            previous_board_limit=40,  # Board capacity was 40, so 45 > 40 = ROLLOVER
            is_rollover_bumped=True,
        ),
        # Long-pending case with early stage
        _case(
            id="NP-2026-104",
            title="Ramesh Kulkarni vs. Union of India",
            case_type="Writ",
            filing_date="08 Mar 2024",
            current_stage="Framing of Issues",
            stage_step=2,
            adjournments_count=5,
            next_hearing_date="22 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice A. M. Patil",
            petitioner="Ramesh Kulkarni",
            respondent="Union of India",
            client_age=62,  # Senior: +20 points
            client_working_years_left=3,  # Service limit: +15 points
            has_property=True,
            case_start_year=2024,  # 2 years old: +20 points
            previous_queue_number=38,  # Was listed but not reached
            previous_board_limit=35,  # Board capacity was 35, so 38 > 35 = ROLLOVER
            is_rollover_bumped=True,
        ),
        # Final hearing stage, moderate priority
        _case(
            id="NP-2026-105",
            title="Priya Nair vs. HDFC Bank Ltd.",
            case_type="Civil",
            filing_date="11 Jun 2025",
            current_stage="Final Hearing",
            stage_step=4,
            adjournments_count=3,
            next_hearing_date="02 Sep 2026",
            court_hall="DRT Mumbai",
            judge_name="Presiding Officer L. S. Mehta",
            petitioner="Priya Nair",
            respondent="HDFC Bank Ltd.",
            client_age=52,
            client_working_years_left=13,
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2025,  # 1 year: +10 points
        ),
        # Recent filing, early stage
        _case(
            id="NP-2026-106",
            title="People's Rights Forum vs. State of Maharashtra",
            case_type="Writ",
            filing_date="30 Jan 2026",
            current_stage="Scrutiny",
            stage_step=1,
            adjournments_count=0,
            next_hearing_date="09 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice R. V. Sawant",
            petitioner="People's Rights Forum",
            respondent="State of Maharashtra",
            client_age=45,
            client_working_years_left=20,
            has_property=True,
            case_start_year=2026,
        ),
        # Very vulnerable: senior, landless, long-pending, rollover from previous board
        _case(
            id="NP-2026-107",
            title="Lakshmi Iyer vs. State Bank of India",
            case_type="Civil Petition",
            filing_date="12 Feb 2023",
            current_stage="Evidence & Arguments",
            stage_step=3,
            adjournments_count=4,
            next_hearing_date="11 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice S. K. Deshmukh",
            petitioner="Lakshmi Iyer",
            respondent="State Bank of India",
            client_age=72,  # Senior: +20 points
            client_working_years_left=0,  # Service limit: +15 points
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2023,  # 3 years: +30 points
            previous_queue_number=52,  # Was listed but not reached
            previous_board_limit=48,  # Board capacity: 52 > 48 = ROLLOVER
            is_rollover_bumped=True,
        ),
        # Moderate age, moderate years left, has property
        _case(
            id="NP-2026-108",
            title="Deepak Singh vs. Housing Development Authority",
            case_type="Administrative Writ",
            filing_date="15 Jul 2025",
            current_stage="Notice under Order V CPC",
            stage_step=2,
            adjournments_count=1,
            next_hearing_date="08 Sep 2026",
            court_hall="Sessions Court, Thane Division",
            judge_name="Additional District Judge R. N. Yadav",
            petitioner="Deepak Singh",
            respondent="Housing Development Authority",
            client_age=55,
            client_working_years_left=10,
            has_property=True,
            case_start_year=2025,
        ),
        # Older petitioner, limited working years, no property
        _case(
            id="NP-2026-109",
            title="Geetha Menon vs. Chandigarh Administration",
            case_type="Civil Writ",
            filing_date="05 Sep 2024",
            current_stage="Framing of Issues",
            stage_step=2,
            adjournments_count=2,
            next_hearing_date="15 Sep 2026",
            court_hall="Punjab & Haryana High Court",
            judge_name="Hon'ble Justice T. P. Singh",
            petitioner="Geetha Menon",
            respondent="Chandigarh Administration",
            client_age=64,  # Senior: +20 points
            client_working_years_left=2,  # Service limit: +15 points
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2024,  # 2 years: +20 points
        ),
        # Recent rollover from previous hearing session
        _case(
            id="NP-2026-110",
            title="Mohammad Iqbal vs. Municipal Revenue Office",
            case_type="Writ Petition",
            filing_date="20 Apr 2025",
            current_stage="Evidence & Arguments",
            stage_step=3,
            adjournments_count=1,
            next_hearing_date="13 Sep 2026",
            court_hall="Delhi High Court",
            judge_name="Hon'ble Justice A. K. Sharma",
            petitioner="Mohammad Iqbal",
            respondent="Municipal Revenue Office",
            client_age=58,
            client_working_years_left=7,
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2025,
            previous_queue_number=41,  # Was listed but not reached
            previous_board_limit=39,  # Board capacity: 41 > 39 = ROLLOVER
            is_rollover_bumped=True,
        ),
        # Long-pending standard case
        _case(
            id="NP-2026-111",
            title="Industries Ltd. vs. Income Tax Department",
            case_type="Writ",
            filing_date="22 Aug 2023",
            current_stage="Final Hearing",
            stage_step=4,
            adjournments_count=6,
            next_hearing_date="20 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice M. S. Karnik",
            petitioner="Industries Ltd.",
            respondent="Income Tax Department",
            client_age=50,
            client_working_years_left=15,
            has_property=True,
            case_start_year=2023,  # 3 years: +30 points
        ),
        # Very senior, landless, very long pending
        _case(
            id="NP-2026-112",
            title="Subhadra Patel vs. State Land Records Office",
            case_type="Civil",
            filing_date="11 Jun 2022",
            current_stage="Notice under Order V CPC",
            stage_step=2,
            adjournments_count=7,
            next_hearing_date="19 Sep 2026",
            court_hall="Bombay High Court",
            judge_name="Hon'ble Justice S. K. Deshmukh",
            petitioner="Subhadra Patel",
            respondent="State Land Records Office",
            client_age=76,  # Senior: +20 points
            client_working_years_left=0,  # Service limit: +15 points
            has_property=False,  # Vulnerable: +30 points
            case_start_year=2022,  # 4 years: +40 points
        ),
    ]

    for case in samples:
        db.session.add(case)
        db.session.add(
            CaseEvent(
                case_id=case.id,
                event_type="Filed",
                note=f"Matter registered as {case.id} ({case.case_type}).",
            )
        )
        if case.adjournments_count:
            db.session.add(
                CaseEvent(
                    case_id=case.id,
                    event_type="Adjournment",
                    note=(
                        f"{case.adjournments_count} prior adjournment(s) on record. "
                        f"Current listing: {case.next_hearing_date}."
                    ),
                )
            )
        if case.is_rollover_bumped:
            db.session.add(
                CaseEvent(
                    case_id=case.id,
                    event_type="Rollover",
                    note=(
                        f"Case was listed at queue position {case.previous_queue_number} but board ended at {case.previous_board_limit}. "
                        f"Eligible for rollover priority in next hearing."
                    ),
                )
            )
        db.session.add(
            CaseEvent(
                case_id=case.id,
                event_type="Stage update",
                note=f"Current stage recorded as {case.current_stage}.",
            )
        )

    db.session.commit()

