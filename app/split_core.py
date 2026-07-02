from decimal import Decimal, ROUND_HALF_UP
from typing import SupportsFloat

from app.config import MAX_PEOPLE


def compute_total_charged_cents(
    subtotal_cents: int,
    tip_pct: SupportsFloat,
    tax_cents: int,
) -> int:
    """Return subtotal + tax + tip cents, with tip rounded HALF-UP.

    HALF-UP means a fractional cent of .5 rounds away from zero. For example,
    a 12.5% tip on 10 cents is 1.25 cents, rounded to 1 cent, while 15% on
    10 cents is 1.5 cents, rounded to 2 cents.
    """
    tip_cents = (
        Decimal(subtotal_cents) * Decimal(str(tip_pct)) / Decimal("100")
    ).to_integral_value(rounding=ROUND_HALF_UP)
    return subtotal_cents + int(tip_cents) + tax_cents


def split_evenly(total: int, people: int) -> list[int]:
    if people <= 0 or people > MAX_PEOPLE:
        raise ValueError(f"people must be between 1 and {MAX_PEOPLE}")

    base = total // people
    remainder = total % people
    return [base + 1] * remainder + [base] * (people - remainder)
