from datetime import date, datetime
from zoneinfo import ZoneInfo


def clean_phone(raw):
    """Return a 10-digit phone number as text, or None if it isn't valid."""
    raw = raw or ""  # protects against None
    digits = "".join(ch for ch in raw if ch in "0123456789")  # ASCII digits only
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return None


def today_in_india():
    """Today's date in Indian time, even if the server runs in another timezone."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def check_age(age, min_age, max_age):
    """Return an error message, or None if the age is allowed."""
    if age < min_age or age > max_age:
        return f"This tournament is for ages {min_age} to {max_age}."
    return None


def check_registration_open(registration_open, deadline, today):
    """Return an error message, or None if players can still register.

    registration_open: 1 or 0 (the organizer's manual toggle)
    deadline: text like "2026-11-30", or None if there is no deadline
    today: a date object
    """
    if not registration_open:
        return "Registration for this tournament is closed."
    if deadline and today > date.fromisoformat(deadline):
        return f"Registration closed on {deadline}."
    return None