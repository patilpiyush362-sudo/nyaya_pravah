# Nyaya Pravah - Judicial Platform Implementation

## Overview

**Nyaya Pravah** is a comprehensive judicial case tracking and management platform with advanced features for priority-based case scheduling and vulnerable litigant protection. The system implements a **Vulnerability-Based Priority Ranking Algorithm** and a **Dynamic Rollover Queue mechanism** to ensure fair and equitable access to justice.

## ✅ Implementation Complete

The full system has been successfully implemented with the following components:

### 1. **Database & Persistence Layer** (`models.py`)

#### Core Case Model with Enhanced Fields

```python
class Case(db.Model):
    # Original fields
    id: String(32) - Primary key (e.g., 'NP-2026-101')
    title: String(255)
    case_type: String(120)
    filing_date: String(40)
    current_stage: String(120)
    stage_step: Integer (1-4)
    plain_explanation: Text
    adjournments_count: Integer
    delay_status: String(50)
    next_hearing_date: String(40)
    court_hall: String(160)
    judge_name: String(160)
    petitioner: String(160)
    respondent: String(160)
    
    # NEW: Litigant Vulnerability & Priority Metrics
    client_age: Integer (default=45)
    client_working_years_left: Integer (default=10)
    has_property: Boolean (default=True, False=vulnerable landless/assetless)
    case_start_year: Integer (default=2026)
    previous_queue_number: Integer (default=0)
    previous_board_limit: Integer (default=0)
    is_rollover_bumped: Boolean (default=False)
    priority_score: Float (default=0.0)
    scheduled_queue_number: Integer (default=0)
```

**Database**: SQLite (`instance/nyaya.db`)

---

### 2. **Priority Ranking & Rollover Scheduler** (`scheduler.py`)

#### Algorithm A: Priority Score Calculation

```python
def compute_priority_score(case, current_year=2026) -> float:
    """
    Vulnerability-Based Priority Score Formula:
    
    Base Score Components:
    • Base Duration: +10 points per active year (current_year - case_start_year)
    • Financial Vulnerability: +30 points if has_property = False (landless/assetless)
    • Age Factor: +20 points if client_age >= 60 (senior citizen)
    • Service Limit: +15 points if client_working_years_left <= 3
    
    Example Scores:
    • Standard business owner (young, has property): 0-10 points
    • Vulnerable senior (landless, 3+ years pending, near retirement): 75-105 points
    • High-priority case (very old, no assets, many years pending): 95-125 points
    """
```

**Score Breakdown Example**:
- Case NP-2026-112: Age 76 + Landless + No working years + 4 years pending = **105.0 points** ⭐ Highest
- Case NP-2026-107: Age 72 + Landless + No working years + 3 years pending = **95.0 points**
- Case NP-2026-104: Age 62 + 3 years working left + 2 years pending = **55.0 points**

#### Algorithm B: Daily Cause List Generation

```python
def generate_daily_cause_list(court_name: str) -> dict:
    """
    Dynamic Judicial Scheduling Algorithm:
    
    Step 1: Determine Capacity
      → today_capacity = random.randint(40, 60)
      → Realistic simulation of Indian court daily board sizes
    
    Step 2: Identify Rollover Cases
      → Find cases where: previous_queue_number > previous_board_limit
      → Meaning: Case was listed but judge's board ended before their turn
      → Mark: is_rollover_bumped = True
    
    Step 3: Apply Judicial Fairness (Rollover Priority)
      → Rollover cases placed at RANKS 1 onwards (top of list)
      → Sorted by priority_score (highest first within rollover group)
      → Guarantees no case is skipped twice
    
    Step 4: Schedule Remaining Cases
      → Standard cases sorted by priority_score (descending)
      → Assigned queue numbers 1 to today_capacity
    
    Step 5: Persist Changes
      → Update: previous_board_limit = today_capacity
      → Update: scheduled_queue_number for all scheduled cases
      → Commit to SQLite
    
    Returns:
    {
        "today_capacity": 45,           # Dynamic capacity for this day
        "scheduled_cases": [...],       # Prioritized case list
        "total_pending": 7,             # All cases for this court
        "rollover_count": 3             # Cases eligible for rollover
    }
    """
```

**Real-World Example Output**:
```
Court: Bombay High Court
Today's Capacity: 45 cases
Total Pending: 7 cases
Rollover Protected: 3 cases

Rank  Case ID        Priority  Status        Litigant Type
───────────────────────────────────────────────────────────
1     NP-2026-107    95.0      🔄 ROLLOVER   Senior, Landless, Service-Limited
2     NP-2026-103    75.0      🔄 ROLLOVER   Senior, Landless, Service-Limited
3     NP-2026-104    55.0      🔄 ROLLOVER   Senior, Service-Limited
4     NP-2026-112    105.0     Standard      Senior, Landless, Service-Limited
5     NP-2026-111    30.0      Standard      Standard
6     NP-2026-101    0.0       Standard      Standard
7     NP-2026-106    0.0       Standard      Standard
```

Notice how **rollover cases are protected** by placement at the top, despite lower priority scores!

---

### 3. **Application Routes & Dashboard** (`app.py`)

#### Route 1: Dashboard (`GET /`)
```python
@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main dashboard with official e-Courts styling
    
    Displays:
    • Total active cases
    • Average adjournments per case
    • High delay risk count
    • Moderate delay watch count
    • Total vulnerable litigants (NEW)
    • Rollover-protected cases (NEW)
    
    Features:
    • Case search by ID
    • Live metrics
    """
```

#### Route 2: Daily Cause List (`GET /cause-list`)
```python
@app.route("/cause-list")
def cause_list():
    """
    Interactive hearing board display with:
    
    • Court selector dropdown
    • Dynamic capacity display ("Today's Capacity: 45 cases")
    • Prioritized case table with:
      - Queue rank (1, 2, 3, ...)
      - Case ID and title
      - Priority score
      - Amber "Rollover Priority" badge
      - Blue "Vulnerable Litigant" badge
      - Litigant demographics (age, property, working years)
    
    Features:
    • Real-time priority calculation
    • Visual distinction for rollover cases
    • Vulnerable litigant identification
    • Responsive grid layout
    """
```

#### Route 3: API Endpoint (`GET /api/cause-list/<court_name>`)
```python
@app.route("/api/cause-list/<court_name>")
def api_cause_list(court_name):
    """JSON API for programmatic access to cause lists"""
    # Returns JSON with full scheduling data
```

---

### 4. **Database Seeding** (`seed.py`)

**12 Realistic Test Cases** pre-populated on startup:

| Case ID | Type | Litigant Profile | Rollover | Priority |
|---------|------|-------------------|----------|----------|
| NP-2026-101 | Business dispute | Young, established | No | Low |
| NP-2026-102 | Criminal | Young respondent | No | Low |
| **NP-2026-103** | **Civil** | **68yo, Landless, 1yr pending** | **YES** | **High** |
| **NP-2026-104** | **Writ** | **62yo, Service-limited, 2yr pending** | **YES** | **High** |
| NP-2026-105 | Bank case | Middle-age, landless | No | Medium |
| NP-2026-106 | Writ | Standard litigant | No | Low |
| **NP-2026-107** | **Civil** | **72yo, Landless, 3yr pending** | **YES** | **Very High** |
| NP-2026-108 | Administrative | Mid-career | No | Low |
| NP-2026-109 | Writ | 64yo, landless, 2yr pending | No | High |
| NP-2026-110 | Writ | 58yo, landless, recent | Yes | Medium |
| NP-2026-111 | Tax case | Business, long-pending | No | Medium |
| **NP-2026-112** | **Land dispute** | **76yo, Landless, 4yr pending** | **No** | **Highest (105)** |

Cases marked with ** demonstrate the rollover and vulnerability systems.

---

### 5. **Frontend Templates**

#### `templates/cause_list.html` (NEW)
- Interactive court selector
- Capacity display with statistics
- Priority-ordered case table
- Color-coded badges:
  - **Amber** 🟠: "Rollover Priority (Board Exhausted Previous Hearing)"
  - **Blue** 🔵: "Vulnerable Litigant"
- Litigant vulnerability indicators (age, property status, working years)
- Responsive design with embedded CSS

#### Enhanced `templates/dashboard.html`
- Added 2 new metric cards:
  - **Vulnerable Litigants**: Count of cases involving seniors, landless, or service-limited individuals
  - **Rollover Priority Cases**: Count of cases with rollover protection

#### Updated `templates/base.html`
- Added navigation link to "Cause List" route

---

## 🔬 Testing & Validation

### Test Results

```
======================================================================
NYAYA PRAVAH - CAUSE LIST GENERATION TEST
======================================================================

Court: Bombay High Court
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Capacity Statistics:
   Today's Capacity: 45 cases
   Total Pending: 7 cases
   Rollover Protected: 3 cases
   Scheduled Today: 7 cases

📋 Top 10 Scheduled Cases:

Rank   Case ID      Priority     Rollover     Litigant Type
──────────────────────────────────────────────────────────
1      NP-2026-107  95.0         ✓ YES        Senior, Landless, Service-Limited
2      NP-2026-103  75.0         ✓ YES        Senior, Landless, Service-Limited
3      NP-2026-104  55.0         ✓ YES        Senior, Service-Limited
4      NP-2026-112  105.0        NO           Senior, Landless, Service-Limited
5      NP-2026-111  30.0         NO           Standard
6      NP-2026-101  0.0          NO           Standard
7      NP-2026-106  0.0          NO           Standard

✅ VALIDATION SUCCESSFUL
```

**Key Observations**:
1. ✅ Rollover cases correctly prioritized at ranks 1-3
2. ✅ Priority scores accurately calculated
3. ✅ Vulnerable litigants properly identified
4. ✅ Dynamic capacity working (45 cases)
5. ✅ Database persistence confirmed

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nyaya Pravah                         │
│            Judicial Case Management Platform            │
└─────────────────────────────────────────────────────────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
         ┌──────────┐ ┌────────┐ ┌─────────┐
         │ Flask    │ │SQLite  │ │Templates│
         │ Routes   │ │Database│ │ (HTML)  │
         └──────────┘ └────────┘ └─────────┘
              │            │           │
         ┌────┴────────────┴────────────┴────┐
         │                                   │
         ▼                                   ▼
    ┌─────────────┐              ┌──────────────────┐
    │  app.py     │              │  scheduler.py    │
    │  Routes     │◄─────────────│  Algorithms      │
    │  Dashboard  │              │  Priority Score  │
    │  API        │              │  Cause List Gen  │
    └─────────────┘              └──────────────────┘
         │
    ┌────┴─────────────────┐
    ▼                      ▼
┌─────────────┐      ┌──────────────┐
│ models.py   │      │ seed.py      │
│ Case Schema │      │ Test Data    │
└─────────────┘      └──────────────┘
```

---

## 🚀 Running the System

### Start the Application
```bash
cd nyaya_pravah
./venv/Scripts/Activate.ps1
python app.py
```

### Access the Platform
- **Main Dashboard**: http://localhost:5000/
- **Daily Cause List**: http://localhost:5000/cause-list
- **API Endpoint**: http://localhost:5000/api/cause-list/<court_name>

### Test the Scheduler
```bash
python test_scheduler.py
```

---

## 📈 Features & Benefits

### 1. **Vulnerability-Based Priority Ranking**
- Automatically prioritizes elderly, landless, and service-limited litigants
- Ensures equitable access to justice
- Transparent scoring mechanism

### 2. **Dynamic Rollover Queue Protection**
- Prevents double-skipping of listed cases
- Guarantees fairness in judicial proceedings
- Automatic re-prioritization for each hearing

### 3. **Real-Time Metrics Dashboard**
- Live statistics on vulnerable litigants
- Rollover protection counts
- Delay risk assessment

### 4. **Persistent SQLite Database**
- Production-ready SQLite implementation
- Scalable schema design
- Automatic schema creation on first run

### 5. **Official e-Courts Styling**
- Government of India branding
- Constitutional seal and insignia
- Professional, accessible UI

---

## 📝 Key Algorithms Explained

### Priority Score Formula
```
Priority Score = (Base Duration × 10) + (Property Vulnerability × 30) 
               + (Age Factor × 20) + (Service Limit × 15)

Where:
• Base Duration = years pending
• Property Vulnerability = 1 if landless, else 0
• Age Factor = 1 if age ≥ 60, else 0
• Service Limit = 1 if working_years_left ≤ 3, else 0
```

### Rollover Logic
```
If case.previous_queue_number > case.previous_board_limit:
    → Case was listed but judge's board ended before their turn
    → Mark: is_rollover_bumped = True
    → Place at top of next hearing's queue (Rank 1 onwards)
    → Sort rollover group by priority_score (highest first)
```

---

## 📂 File Structure

```
nyaya_pravah/
├── app.py                    # Flask application & routes
├── models.py                 # SQLAlchemy Case & CaseEvent models
├── scheduler.py              # Priority algorithms (NEW)
├── extensions.py             # Flask-SQLAlchemy initialization
├── seed.py                   # Database seeding (UPDATED)
├── transparency.py           # Stage explanations
├── requirements.txt          # Dependencies
├── test_scheduler.py         # Verification script
└── templates/
    ├── base.html             # Base layout
    ├── dashboard.html        # Main dashboard (UPDATED)
    ├── cause_list.html       # Daily cause list (NEW)
    ├── cases.html            # Case listing
    ├── case_detail.html      # Case details
    └── new_case.html         # Case registration
└── static/
    └── css/
        └── style.css         # Styling
└── instance/
    └── nyaya.db              # SQLite database (auto-created)
```

---

## ✨ Implementation Highlights

1. **Full SQLite Integration**: Real persistent database with all new fields
2. **Mathematical Algorithms**: Vulnerability-based scoring and rollover logic
3. **Dynamic Scheduling**: Random capacity (40-60) simulating real court operations
4. **Litigant Protection**: Clear badges and UI indicators for vulnerable cases
5. **Rollover Fairness**: Automatic re-prioritization ensuring no double-skipping
6. **Comprehensive Seeding**: 12 realistic test cases including rollover scenarios
7. **Professional UI**: Government-official styling with judicial symbolism
8. **API-Ready**: JSON endpoints for programmatic access

---

## 🎯 Next Steps (Optional Enhancements)

1. Authentication & role-based access control (judges, clerks, public)
2. Email notifications for upcoming hearings
3. Historical analytics and trend reporting
4. Integration with actual e-Courts portal
5. Mobile-responsive improvements
6. PDF generation for formal cause lists

---

## ✅ Verification Checklist

- [x] SQLite database with all specified fields
- [x] Priority score algorithm implemented
- [x] Dynamic rollover queue mechanism working
- [x] Routes created: `/`, `/cause-list`, `/api/cause-list/<court>`
- [x] Dashboard metrics updated
- [x] Cause list template with badges and styling
- [x] 12 test cases seeded including rollover scenarios
- [x] Test script validates algorithms
- [x] System runs without errors
- [x] Database persists correctly

**Status**: 🟢 **COMPLETE AND OPERATIONAL**

---

Generated: August 30, 2026
Platform: Nyaya Pravah v1.0
