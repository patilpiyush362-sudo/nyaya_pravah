#!/usr/bin/env python
"""Test script for Nyaya Pravah scheduler"""

from app import app, db
from scheduler import generate_daily_cause_list, compute_priority_score
from models import Case

app.app_context().push()

print("=" * 70)
print("NYAYA PRAVAH - CAUSE LIST GENERATION TEST")
print("=" * 70)

# Get all courts
courts = sorted({c.court_hall for c in Case.query.filter(Case.court_hall != None).all()})

for court in courts[:2]:  # Test first 2 courts
    print(f"\n\n{'='*70}")
    print(f"COURT: {court}")
    print(f"{'='*70}")
    
    result = generate_daily_cause_list(court)
    
    print(f"\n📊 Capacity Statistics:")
    print(f"   Today's Capacity: {result['today_capacity']} cases")
    print(f"   Total Pending: {result['total_pending']} cases")
    print(f"   Rollover Protected: {result['rollover_count']} cases")
    print(f"   Scheduled Today: {len(result['scheduled_cases'])} cases")
    
    print(f"\n📋 Top 10 Scheduled Cases:")
    print(f"\n{'Rank':<6} {'Case ID':<12} {'Priority':<12} {'Rollover':<12} {'Litigant Type':<20}")
    print("-" * 70)
    
    for i, case in enumerate(result['scheduled_cases'][:10], 1):
        litigant_type = []
        if case.client_age >= 60:
            litigant_type.append("Senior")
        if not case.has_property:
            litigant_type.append("Landless")
        if case.client_working_years_left <= 3:
            litigant_type.append("Service-Limited")
        
        litigant_str = ", ".join(litigant_type) if litigant_type else "Standard"
        rollover_str = "✓ YES" if case.is_rollover_bumped else "NO"
        
        print(f"{i:<6} {case.id:<12} {case.priority_score:<12.1f} {rollover_str:<12} {litigant_str:<20}")

print("\n\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
