# Product Requirements Document: Perkle

## Problem Statement

Premium credit card holders frequently leave money on the table by failing to use their card benefits before they expire. The challenge stems from:

- Multiple cards with different benefit schedules (monthly, quarterly, annual, semi-annual)
- Benefits that require verification via statement credits that post days after the qualifying transaction
- No unified view across cards to see what's been used vs. what's expiring
- Manual tracking in spreadsheets is tedious and error-prone

For a user with AMEX Platinum, AMEX Gold, Chase Sapphire Reserve, and Capital One Venture X, the total annual benefit value exceeds $3,500. Even missing a few monthly credits results in significant lost value.

## Product Vision

A mobile-first web application that automatically tracks credit card benefit usage by parsing transaction exports (CSV). The system intelligently matches transactions to benefits, handles the credit-attribution problem (credit posted 2/3 for transaction on 1/31 = January benefit), and alerts users before benefits expire.

## Target User

Credit card optimizer with 3-6 premium rewards cards who wants to maximize value without maintaining manual spreadsheets. Comfortable uploading CSV exports from financial aggregators.

## Core Capabilities

### 1. Authentication & User Management
- Basic auth (username/password)
- Each user has isolated data (cards, transactions, benefit history)
- JWT-based sessions

### 2. Card Portfolio

**Supported Cards (MVP)**
- AMEX Gold
- AMEX Platinum
- Chase Sapphire Reserve
- Capital One Venture X

**Config-Driven Architecture**
New cards added via YAML config files containing:
- Card metadata (name, issuer, annual fee, benefits URL)
- Account identifiers for CSV matching
- Benefit definitions with detection rules

### 3. Benefit Definitions

Each benefit specifies:
- **name**: Human-readable label
- **value**: Dollar amount
- **cadence**: monthly | quarterly | semi-annual | annual | rolling | per-booking
- **reset_type**: calendar_year | cardmember_year | rolling_years
- **tracking_mode**: auto | manual | info
- **detection_rules** (for auto):
  - credit_patterns: Regex patterns matching credit transaction names
  - lookback_days: How far back to attribute credits to original transactions

### 4. Transaction Import

**CSV Format** (Copilot Money compatible):
- date, name, amount, status, category, account, etc.

**Processing Pipeline**:
1. Parse CSV, validate required fields
2. Match transactions to user's cards via account field
3. Identify credit transactions (negative amounts)
4. Run benefit detection rules against credits
5. Attribute detected benefits to correct period (using lookback logic)
6. Deduplicate against previously imported transactions

### 5. Benefit Attribution Logic

Credits post after the qualifying transaction, but should count toward the transaction's period.

**Example**:
- 1/17: "Fish Cheeks" $146.40 on Platinum Card (Resy restaurant)
- 1/19: "Platinum Resy Credit" -$100 posts
- Result: January Resy benefit marked as USED

**Algorithm**:
1. Detect credit transaction matching benefit pattern
2. Look back N days for qualifying transaction
3. Use qualifying transaction date to determine benefit period
4. If no qualifying transaction found, use credit date

### 6. Dashboard

**Home View** (mobile-optimized)
- Aggregate "Unused Benefits" card showing all unused benefits sorted by urgency
- Summary cards for each credit card in portfolio
- Each card shows benefit status with sorting: unused → partial → used → info
- Total value captured vs. available
- Renewal warnings for cards within 30 days of anniversary

**Card Detail View**
- All benefits for selected card (sorted by status)
- Current period status with progress indicator
- Manual check-off with partial amount support
- Benefit muting toggle
- Link to official card benefits page
- Renewal date display

### 7. Manual Benefit Tracking

For benefits that can't be auto-detected:
- User taps "Mark as Used"
- Supports partial amounts (e.g., $123 of $300 travel credit)
- Input validation (can't exceed remaining credit)

Examples of manual benefits:
- AMEX Uber Cash (loaded to Uber app)
- Venture X travel credit (portal bookings)
- CSR Lyft credit (app credit, not statement)
- CSR DoorDash credits (app promos)

### 8. Info-Only Benefits

Some benefits require no user action:
- Venture X anniversary bonus miles (auto-deposited)
- CSR Apple subscriptions (auto-renews)
- Premier Collection credits (applied at checkout)

These show as "info" status and appear at bottom of benefit lists.

### 9. Benefit Muting

Users can mute benefits they don't use:
- Muted benefits hidden from dashboard
- Still visible in card detail (grayed out)
- Can be unmuted anytime

Use cases:
- User doesn't have Equinox membership
- User doesn't shop at Saks

### 10. Notifications

**Email Digest**
- Weekly summary of expiring benefits
- Upcoming card renewals (30 days before anniversary)

**Renewal Warnings**
- Dashboard banner for cards renewing within 30 days
- Card detail always shows days until renewal

## Technical Stack

- **Frontend**: React + Vite + TailwindCSS v4
- **Backend**: Python/FastAPI
- **Database**: SQLite
- **Auth**: JWT tokens
- **Deployment**: Docker + Tailscale

## Success Criteria

- User can upload CSV and see benefit status within 30 seconds
- Auto-detection accuracy >90% for supported benefits
- Mobile experience works well on phone screens
- Zero missed expiring benefits with weekly email digest
