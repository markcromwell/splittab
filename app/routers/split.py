from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import MAX_PEOPLE
from app.split_core import compute_total_charged_cents, split_evenly

router = APIRouter()


class SplitRequest(BaseModel):
    subtotal_cents: int = Field(gt=0)
    people: int = Field(gt=0, le=MAX_PEOPLE)
    tip_pct: float = Field(ge=0)
    tax_cents: int = Field(ge=0)


class SplitResponse(BaseModel):
    per_person: list[int]
    total_charged_cents: int


@router.post("/split", response_model=SplitResponse)
def split_bill(request: SplitRequest) -> SplitResponse:
    total_charged_cents = compute_total_charged_cents(
        request.subtotal_cents,
        request.tip_pct,
        request.tax_cents,
    )
    return SplitResponse(
        per_person=split_evenly(total_charged_cents, request.people),
        total_charged_cents=total_charged_cents,
    )
