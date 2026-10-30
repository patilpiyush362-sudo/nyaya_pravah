# Nyaya Pravah - Quick Start Guide

## 🚀 Getting Started

### 1. Start the Application

```bash
cd c:\Users\qcc\OneDrive\Desktop\nyaya_pravah
./venv/Scripts/Activate.ps1
python app.py
```

The server will start at **http://localhost:5000**

### 2. Access the Web Interface

#### 🏠 **Home Dashboard** → http://localhost:5000/
- View metrics:
  - Total active cases: **12**
  - Vulnerable litigants: **7**
  - Rollover-protected cases: **4**
- Search cases by ID
- Register new cases

#### 📋 **Daily Cause List** → http://localhost:5000/cause-list
- Select a court from dropdown
- View prioritized hearing board
- See queue ranks with vulnerability badges
- Identify rollover-protected cases

#### 📁 **All Cases** → http://localhost:5000/cases
- Filter by stage, court, or delay status
- Full case listing with details

---

## 🔍 Key Features to Explore

### Feature 1: Vulnerability-Based Priority
Visit the **Cause List** page and select **"Bombay High Court"**. You'll see:
- Cases ranked by priority score
- Senior citizens (age ≥ 60) highlighted
- Landless/assetless litigants identified
- Service-limited individuals (≤ 3 working years) noted

**Example**: Case NP-2026-112 has the highest priority score (105.0) because:
- Age 76 (+20 points)
- Landless/assetless (+30 points)
- No working years left (+15 points)
- 4 years pending (+40 points)

### Feature 2: Rollover Protection Mechanism
On the **Cause List**, look for the **amber "Rollover Priority" badges**. These cases:
- Were listed in a previous hearing
- Were not reached before the judge's board ended
- Are automatically placed at the top of today's list
- Prevent double-skipping and ensure fairness

**Example Rollover Cases**:
- NP-2026-103: Was rank 45 but board ended at 40
- NP-2026-104: Was rank 38 but board ended at 35
- NP-2026-107: Was rank 52 but board ended at 48

### Feature 3: Dynamic Capacity
Each time you generate a cause list, the capacity randomly changes (40-60 cases) to simulate:
- Variable court workloads
- Different judge availability
- Realistic Indian judicial operations

---

## 📊 Database Overview

### Seeded Test Cases (12 total)

| ID | Title | Vulnerable? | Rollover? | Court |
|----|-------|-------------|-----------|-------|
| NP-2026-101 | Sharma Enterprises vs. Maharashtra | No | No | Bombay High Court |
| NP-2026-102 | State vs. Varma | No | No | Sessions Court, Kalyan |
| **NP-2026-103** | **Desai vs. MCGM** | **Yes** | **Yes** | **Bombay High Court** |
| **NP-2026-104** | **Kulkarni vs. Union** | **Yes** | **Yes** | **Bombay High Court** |
| NP-2026-105 | Nair vs. HDFC | Yes | No | DRT Mumbai |
| NP-2026-106 | People's Rights Forum vs. State | No | No | Bombay High Court |
| **NP-2026-107** | **Iyer vs. SBI** | **Yes** | **Yes** | **Bombay High Court** |
| NP-2026-108 | Singh vs. Housing Authority | No | No | Sessions Court, Thane |
| NP-2026-109 | Menon vs. Chandigarh Admin | Yes | No | Punjab & Haryana High Court |
| NP-2026-110 | Iqbal vs. Municipal Office | Yes | Yes | Delhi High Court |
| NP-2026-111 | Industries Ltd. vs. Income Tax | No | No | Bombay High Court |
| **NP-2026-112** | **Patel vs. Land Records Office** | **Yes** | **No** | **Bombay High Court** |

---

## 🔬 Testing the Algorithms

### Run Scheduler Test
```bash
python test_scheduler.py
```

This will:
1. Generate cause lists for each court
2. Display rankings and prioritization
3. Show rollover case placement
4. Verify priority scoring

### Expected Output:
```
COURT: Bombay High Court
─────────────────────────────────────────────────
📊 Capacity Statistics:
   Today's Capacity: 45 cases
   Total Pending: 7 cases
   Rollover Protected: 3 cases

Rank  Case ID      Priority  Rollover  Litigant Type
────────────────────────────────────────────────────
1     NP-2026-107  95.0      ✓ YES     Senior, Landless
2     NP-2026-103  75.0      ✓ YES     Senior, Landless
3     NP-2026-104  55.0      ✓ YES     Senior, Service-Limited
4     NP-2026-112  105.0     NO        Senior, Landless
...
```

### Run System Verification
```bash
python verify_system.py
```

This confirms:
- ✓ Database connectivity
- ✓ All modules loaded
- ✓ Priority scoring working
- ✓ Cause list generation working
- ✓ All routes accessible

---

## 🎯 Algorithm Walkthrough

### Priority Score Calculation

For a case to get a score, we sum:

1. **Base Duration** (+10 per year pending)
   - Case from 2024 (2 years old) = +20 points

2. **Financial Vulnerability** (+30 if landless/assetless)
   - `has_property = False` = +30 points

3. **Age Factor** (+20 if senior)
   - `client_age >= 60` = +20 points

4. **Service Limit** (+15 if few working years)
   - `client_working_years_left <= 3` = +15 points

**Example**:
```
Case NP-2026-104:
  - Age: 62 (senior) = +20
  - Working years left: 3 (limited) = +15
  - Years pending: 2 = +20
  - Property: Yes = +0
  ─────────
  Total Score = 55.0
```

### Rollover Queue Logic

```
IF case.previous_queue_number > case.previous_board_limit
THEN is_rollover_bumped = True

Example:
  Case NP-2026-103:
    - Was ranked: 45
    - Judge's board ended at: 40
    - Since 45 > 40, case was skipped
    - Solution: Place at top of next hearing
```

---

## 📈 Understanding the Dashboard

### Metrics Displayed

**Total Active Cases**: 12
- All pending judicial matters in the system

**Average Adjournments**: Varies
- How many times hearings were postponed on average

**High Delay Risk**: Count
- Cases exceeding delay thresholds

**Moderate Delay Watch**: Count
- Cases approaching delay thresholds

**Vulnerable Litigants**: 7 (NEW)
- Senior citizens, landless persons, or service-limited individuals

**Rollover Priority Cases**: 4 (NEW)
- Cases protected by rollover mechanism

---

## 🎨 UI/UX Features

### Cause List Page Styling

**Color Scheme**:
- **Amber Badges** 🟠: Rollover Priority cases (judicial fairness)
- **Blue Badges** 🔵: Vulnerable Litigants (protection)
- **Blue Rank Circles**: Queue position numbers
- **Light Blue Rows**: Rollover cases highlighted

**Information Display**:
- Case ID with hyperlinks to detail pages
- Full case title with parties
- Priority score (0-125 range)
- Litigant demographics (age, property status)
- Court name and capacity limit

**Responsive Design**:
- Works on desktop (full features)
- Adapts to tablet (condensed layout)
- Mobile-friendly (stacked layout)

---

## 🔌 API Usage

### Get Daily Cause List (JSON)

```bash
curl http://localhost:5000/api/cause-list/Bombay%20High%20Court
```

**Response**:
```json
{
  "court": "Bombay High Court",
  "today_capacity": 45,
  "total_pending": 7,
  "rollover_count": 3,
  "scheduled_count": 7,
  "cases": [
    {
      "rank": 1,
      "case_id": "NP-2026-107",
      "title": "Lakshmi Iyer vs. State Bank of India",
      "petitioner": "Lakshmi Iyer",
      "respondent": "State Bank of India",
      "priority_score": 95.0,
      "is_rollover": true,
      "client_age": 72,
      "has_property": false
    },
    ...
  ]
}
```

---

## 🛠️ Configuration

### Database
- **Type**: SQLite
- **Location**: `instance/nyaya.db`
- **Auto-created**: On first run
- **Auto-seeded**: 12 test cases on initialization

### Flask Config (in app.py)
```python
app.config["SECRET_KEY"] = "nyaya-pravah-dev"  # Change for production
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/nyaya.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
```

### Server
- **Host**: 127.0.0.1 (localhost only)
- **Port**: 5000
- **Debug Mode**: Enabled (auto-reload on file changes)

---

## 📝 Common Tasks

### Add a New Case

1. Click **"Register Case"** (navigation bar)
2. Fill in case details:
   - Title (required)
   - Case type (Civil, Criminal, Writ, etc.)
   - Filing date
   - Court hall
   - Judge name
   - Petitioner / Respondent
   - Litigant age and property status (for priority)
3. Click **"Register"**

### Generate Fresh Cause List

1. Go to **"Cause List"** (navigation bar)
2. Select a court from dropdown
3. View auto-generated prioritized list
4. Refresh to see different capacity (40-60 random)

### Search a Case

1. On **Home Dashboard**, use the search box
2. Enter case ID (e.g., `NP-2026-107`)
3. View full case details and history

### View All Cases

1. Click **"All Cases"** (navigation bar)
2. Optionally filter by:
   - Stage (Scrutiny, Notice, Framing, Evidence, etc.)
   - Court
   - Delay status
3. Click **"Adjourn"** to log an adjournment

---

## ✅ System Checklist

- [x] SQLite database with 23 fields (12 new for vulnerability/priority)
- [x] Priority scoring algorithm (Base duration + vulnerability factors)
- [x] Dynamic rollover queue (40-60 capacity, rollover-bumped cases prioritized)
- [x] Dashboard with 6 metrics including vulnerable litigants + rollover counts
- [x] Cause list route with court selector
- [x] Cause list template with badges and styling
- [x] API endpoint for JSON access
- [x] 12 seeded cases including rollover scenarios
- [x] Test scripts validating all algorithms
- [x] Database persistence confirmed
- [x] All routes functional and tested

---

## 🆘 Troubleshooting

### Issue: "No module named 'flask'"
**Solution**: Activate virtual environment
```bash
./venv/Scripts/Activate.ps1
```

### Issue: "Database locked" error
**Solution**: Delete and recreate
```bash
rm -Force instance/nyaya.db
python app.py  # Will auto-recreate and seed
```

### Issue: Port 5000 already in use
**Solution**: Change port in app.py
```python
app.run(debug=True, port=5001)  # Use 5001 instead
```

### Issue: Cases not appearing in cause list
**Solution**: Verify court name matches exactly (case-sensitive)
- Use exact name from database (e.g., "Bombay High Court")

---

## 📚 Documentation

- **IMPLEMENTATION_SUMMARY.md**: Technical overview and architecture
- **verify_system.py**: System status verification
- **test_scheduler.py**: Algorithm validation
- **scheduler.py**: Algorithm source code with comments

---

## 🎉 You're Ready!

The Nyaya Pravah judicial platform is fully operational with:
- ✅ Real SQLite database
- ✅ Advanced priority algorithms
- ✅ Rollover fairness mechanism
- ✅ Professional government UI
- ✅ Complete test coverage

**Start exploring**: http://localhost:5000

Enjoy using the platform! 🚀

