"""Benefit period calculation service."""
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


def get_period_boundaries(
    cadence: str,
    reference_date: date,
    card_anniversary: date | None = None,
    reset_type: str | None = None,
    reset_years: int = 4,
    last_used_date: date | None = None,
) -> tuple[date, date]:
    """Calculate the start and end dates for a benefit period.
    
    Args:
        cadence: monthly, quarterly, semi-annual, annual, one-time, per-booking, rolling
        reference_date: The date to find the period for
        card_anniversary: For cardmember_year benefits, the card anniversary date
        reset_type: calendar_year, cardmember_year, or rolling_years
        reset_years: For rolling benefits, how many years until reset
        last_used_date: For rolling benefits, when the benefit was last used
    
    Returns:
        Tuple of (period_start, period_end)
    """
    if cadence == "monthly":
        # Month containing reference_date
        start = reference_date.replace(day=1)
        end = (start + relativedelta(months=1)) - timedelta(days=1)
        
    elif cadence == "quarterly":
        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        quarter = (reference_date.month - 1) // 3
        start_month = quarter * 3 + 1
        start = date(reference_date.year, start_month, 1)
        end = (start + relativedelta(months=3)) - timedelta(days=1)
        
    elif cadence == "semi-annual":
        # H1: Jan-Jun, H2: Jul-Dec
        if reference_date.month <= 6:
            start = date(reference_date.year, 1, 1)
            end = date(reference_date.year, 6, 30)
        else:
            start = date(reference_date.year, 7, 1)
            end = date(reference_date.year, 12, 31)
            
    elif cadence == "annual":
        if reset_type == "cardmember_year" and card_anniversary:
            # Cardmember year: anniversary to anniversary
            # Find which cardmember year this date falls into
            anniv_this_year = date(reference_date.year, card_anniversary.month, card_anniversary.day)
            if reference_date >= anniv_this_year:
                start = anniv_this_year
                end = anniv_this_year + relativedelta(years=1) - timedelta(days=1)
            else:
                start = anniv_this_year - relativedelta(years=1)
                end = anniv_this_year - timedelta(days=1)
        else:
            # Calendar year (default)
            start = date(reference_date.year, 1, 1)
            end = date(reference_date.year, 12, 31)
    
    elif cadence == "rolling":
        # Rolling benefits (like Global Entry) - period based on last use
        if last_used_date:
            start = last_used_date
            end = last_used_date + relativedelta(years=reset_years) - timedelta(days=1)
        else:
            # No previous use - available now, "expires" in reset_years
            start = date(reference_date.year - reset_years, reference_date.month, reference_date.day)
            end = date(reference_date.year + reset_years, reference_date.month, reference_date.day)
            
    elif cadence == "one-time":
        # One-time benefits don't have a recurring period
        # Use a very wide range (4 years typical for Global Entry)
        start = date(reference_date.year - 4, 1, 1)
        end = date(reference_date.year + 4, 12, 31)
        
    elif cadence == "per-booking":
        # Per-booking benefits are tracked per use, not per period
        # Use the single day as the "period"
        start = reference_date
        end = reference_date
        
    else:
        raise ValueError(f"Unknown cadence: {cadence}")
    
    return start, end


def get_current_period_for_benefit(
    cadence: str,
    today: date | None = None,
    card_anniversary: date | None = None,
    reset_type: str | None = None,
    reset_years: int = 4,
    last_used_date: date | None = None,
) -> tuple[date, date]:
    """Get the current active period for a benefit."""
    if today is None:
        today = date.today()
    return get_period_boundaries(
        cadence, today, card_anniversary, reset_type, reset_years, last_used_date
    )


def days_remaining_in_period(period_end: date, today: date | None = None) -> int:
    """Calculate days remaining in a benefit period."""
    if today is None:
        today = date.today()
    delta = period_end - today
    return max(0, delta.days)


def is_period_expiring_soon(period_end: date, threshold_days: int = 7, today: date | None = None) -> bool:
    """Check if a benefit period is expiring soon."""
    return days_remaining_in_period(period_end, today) <= threshold_days
