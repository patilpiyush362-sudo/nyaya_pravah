"""
Nyaya Pravah Scheduler Module

Implements:
- Priority score computation based on litigant vulnerability
- Dynamic cause list generation with rollover protection
"""

import random
from typing import List

from extensions import db
from models import Case


def compute_priority_score(case: Case, current_year: int = 2026) -> float:
    """
    Compute priority score for a case based on vulnerability factors.
    
    Scoring breakdown:
    - Base duration: +10 points for every active year
    - Financial vulnerability: +30 points if has_property is False (landless/assetless)
    - Age factor: +20 points if client_age >= 60
    - Service limit: +15 points if client_working_years_left <= 3
    
    Args:
        case: Case object to score
        current_year: Current calendar year (default: 2026)
    
    Returns:
        float: Priority score
    """
    score = 0.0
    
    # Base duration: +10 for every active year
    years_active = current_year - case.case_start_year
    score += 10 * max(0, years_active)
    
    # Financial vulnerability: +30 if landless/assetless (has_property = False)
    if not case.has_property:
        score += 30
    
    # Age factor: +20 if senior citizen (age >= 60)
    if case.client_age >= 60:
        score += 20
    
    # Service limit: +15 if working years left <= 3
    if case.client_working_years_left <= 3:
        score += 15
    
    return score


def generate_daily_cause_list(court_name: str, current_year: int = 2026) -> dict:
    """
    Generate prioritized daily cause list (hearing board) for a given court.
    
    Algorithm:
    1. Determine today's capacity (40-60 realistic court board size)
    2. Query all pending cases for the court
    3. Update priority scores for all cases
    4. Apply Dynamic Rollover Rule:
       - Identify cases where previous_queue_number > previous_board_limit
       - Mark them as is_rollover_bumped = True
       - Place at absolute top of new list (ranks 1 onwards)
    5. Sort remaining standard cases by priority_score descending
    6. Assign sequential queue numbers 1 to today_capacity
    7. Update previous_board_limit = today_capacity for scheduled cases
    8. Commit to SQLite
    
    Args:
        court_name: Name of the court (e.g., "Bombay High Court")
        current_year: Current calendar year (default: 2026)
    
    Returns:
        dict: {
            "today_capacity": int,
            "scheduled_cases": List[Case],
            "total_pending": int,
            "rollover_count": int
        }
    """
    # Determine dynamic capacity for today (realistic court board: 40-60 cases)
    today_capacity = random.randint(40, 60)
    
    # Query all pending cases for this court
    pending_cases = Case.query.filter_by(court_hall=court_name).all()
    
    if not pending_cases:
        return {
            "today_capacity": today_capacity,
            "scheduled_cases": [],
            "total_pending": 0,
            "rollover_count": 0,
        }
    
    # Update priority scores for all cases
    for case in pending_cases:
        case.priority_score = compute_priority_score(case, current_year)
    
    # Identify rollover cases (listed before but judge's board ended before their turn)
    rollover_cases = []
    standard_cases = []
    
    for case in pending_cases:
        if case.previous_queue_number > 0 and case.previous_queue_number > case.previous_board_limit:
            case.is_rollover_bumped = True
            rollover_cases.append(case)
        else:
            case.is_rollover_bumped = False
            standard_cases.append(case)
    
    # Sort rollover cases by priority (highest first) - these go to top
    rollover_cases.sort(key=lambda c: c.priority_score, reverse=True)
    
    # Sort standard cases by priority (highest first)
    standard_cases.sort(key=lambda c: c.priority_score, reverse=True)
    
    # Combine: rollover cases first, then standard cases
    ordered_cases = rollover_cases + standard_cases
    
    # Take only up to today's capacity and assign queue numbers
    scheduled_cases = ordered_cases[:today_capacity]
    
    for rank, case in enumerate(scheduled_cases, start=1):
        case.scheduled_queue_number = rank
        case.previous_board_limit = today_capacity
    
    # Commit all changes to SQLite
    db.session.commit()
    
    return {
        "today_capacity": today_capacity,
        "scheduled_cases": scheduled_cases,
        "total_pending": len(pending_cases),
        "rollover_count": len(rollover_cases),
    }


def simulate_board_hearing(court_name: str, cases_heard: int):
    """
    Simulate a hearing session to update case queue tracking for next generation.
    
    Args:
        court_name: Name of the court
        cases_heard: Number of cases actually heard before adjournment
    """
    cases = Case.query.filter_by(court_hall=court_name).all()
    for case in cases:
        if case.scheduled_queue_number > 0 and case.scheduled_queue_number <= cases_heard:
            # Case was heard, reset for next cycle
            case.previous_queue_number = 0
            case.is_rollover_bumped = False
        elif case.scheduled_queue_number > 0 and case.scheduled_queue_number > cases_heard:
            # Case was listed but not reached - becomes rollover candidate
            case.previous_queue_number = case.scheduled_queue_number
        case.scheduled_queue_number = 0
    
    db.session.commit()
