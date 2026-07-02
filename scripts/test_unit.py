from fastapi.testclient import TestClient

from app import create_app
from app.split_core import compute_total_charged_cents, split_evenly

client = TestClient(create_app())


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_compute_total_charged_cents_uses_half_up_rounding():
    cases = [
        (10, 15, 0, 12),
        (10, 12.5, 0, 11),
        (1000, 12.5, 37, 1162),
    ]

    for subtotal_cents, tip_pct, tax_cents, expected_total in cases:
        assert compute_total_charged_cents(subtotal_cents, tip_pct, tax_cents) == expected_total


def test_split_evenly_exact_sum_invariant_table():
    cases = [
        ("one person", 1234, 1),
        ("people greater than subtotal cents", 2, 3),
        ("fractional percent tip", compute_total_charged_cents(1000, 12.5, 0), 4),
        ("large group", 12345, 1000),
    ]

    for label, total, people in cases:
        per_person = split_evenly(total, people)
        assert len(per_person) == people, label
        assert sum(per_person) == total, label


def test_split_evenly_remainder_goes_to_first_people():
    total = 14
    people = 5
    base = total // people
    remainder = total % people

    per_person = split_evenly(total, people)

    assert per_person == [base + 1] * remainder + [base] * (people - remainder)
    assert per_person[:remainder] == [base + 1] * remainder
    assert per_person[remainder:] == [base] * (people - remainder)
    assert sum(per_person) == total


def test_split_api_happy_path_exact_sum():
    resp = client.post(
        "/split",
        json={
            "subtotal_cents": 1000,
            "people": 3,
            "tip_pct": 12.5,
            "tax_cents": 101,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_charged_cents"] == 1226
    assert len(body["per_person"]) == 3
    assert body["per_person"] == [409, 409, 408]
    assert sum(body["per_person"]) == body["total_charged_cents"]


def test_split_api_validation_errors_return_422():
    valid_payload = {
        "subtotal_cents": 1000,
        "people": 2,
        "tip_pct": 20,
        "tax_cents": 80,
    }
    invalid_cases = [
        {"people": 0},
        {"subtotal_cents": 0},
        {"tip_pct": -1},
        {"tax_cents": -1},
        {"subtotal_cents": None},
        {"people": "many"},
    ]

    for override in invalid_cases:
        payload = valid_payload | override
        resp = client.post("/split", json=payload)
        assert resp.status_code == 422


def test_split_api_missing_field_returns_422():
    payload = {
        "subtotal_cents": 1000,
        "people": 2,
        "tip_pct": 20,
    }

    resp = client.post("/split", json=payload)

    assert resp.status_code == 422
