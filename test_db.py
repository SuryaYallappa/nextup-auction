from validators import check_age, check_registration_open
from datetime import date

assert check_age(20, 16, 30) is None
assert check_age(16, 16, 30) is None   # boundaries are allowed
assert check_age(30, 16, 30) is None
assert check_age(15, 16, 30) is not None
assert check_age(31, 16, 30) is not None

d = date(2026, 11, 30)
assert check_registration_open(1, "2026-11-30", d) is None                # deadline day is open
assert check_registration_open(1, "2026-12-01", d) is None
assert check_registration_open(1, "2026-11-29", d) is not None            # deadline passed
assert check_registration_open(0, "2026-12-31", d) is not None            # manually closed
assert check_registration_open(1, None, d) is None                        # no deadline set
print("Age and deadline tests passed.")