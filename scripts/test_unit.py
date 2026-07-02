from fastapi.testclient import TestClient

from app import create_app
from app.config import MAX_PEOPLE, settings
from app.split_core import compute_total_charged_cents, split_evenly

client = TestClient(create_app())


def test_root_landing_payload():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"app_name": "SplitTab", "docs": None}


def test_root_landing_payload_advertises_docs_when_openapi_exposed(monkeypatch):
    monkeypatch.setattr(settings, "expose_openapi", True)
    exposed_client = TestClient(create_app())

    resp = exposed_client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"app_name": "SplitTab", "docs": "/docs"}


def test_openapi_and_docs_are_disabled_by_default():
    for path in ("/openapi.json", "/docs", "/redoc"):
        resp = client.get(path)
        assert resp.status_code == 404


def test_openapi_is_served_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "expose_openapi", True)
    exposed_client = TestClient(create_app())

    resp = exposed_client.get("/openapi.json")

    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "SplitTab"


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
        ("max group", 12345, MAX_PEOPLE),
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


def test_split_evenly_rejects_people_outside_bounds():
    invalid_people_counts = [0, -1, MAX_PEOPLE + 1]

    for people in invalid_people_counts:
        try:
            split_evenly(100, people)
        except ValueError as exc:
            assert f"1 and {MAX_PEOPLE}" in str(exc)
        else:
            raise AssertionError(f"expected ValueError for people={people}")


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
        {"people": MAX_PEOPLE + 1},
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


def test_split_api_accepts_max_people():
    resp = client.post(
        "/split",
        json={
            "subtotal_cents": 1000,
            "people": MAX_PEOPLE,
            "tip_pct": 0,
            "tax_cents": 0,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_charged_cents"] == 1000
    assert len(body["per_person"]) == MAX_PEOPLE
    assert sum(body["per_person"]) == body["total_charged_cents"]


def test_wait_healthy_scheme_guard():
    from unittest.mock import patch, MagicMock
    from scripts.setup import wait_healthy

    # 1) Assert that file://, ftp://, and custom:// URLs are rejected and return False
    # and urllib.request.urlopen is never called
    with patch("urllib.request.urlopen") as mock_urlopen:
        assert wait_healthy("file:///etc/passwd") is False
        assert wait_healthy("ftp://example.com/file") is False
        assert wait_healthy("custom://example.com/api") is False
        mock_urlopen.assert_not_called()

    # 2) Assert that http:// and https:// URLs pass the scheme guard (i.e. urlopen is called)
    # and if urlopen succeeds, wait_healthy returns True.
    # Also assert that the response is read with a bounded limit.
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test http://
        assert wait_healthy("http://localhost:8000/health", timeout=1) is True
        mock_urlopen.assert_called_with("http://localhost:8000/health", timeout=5)
        mock_response.read.assert_called_with(4096)

        # Reset and test https://
        mock_urlopen.reset_mock()
        mock_response.read.reset_mock()
        assert wait_healthy("https://localhost:8000/health", timeout=1) is True
        mock_urlopen.assert_called_with("https://localhost:8000/health", timeout=5)
        mock_response.read.assert_called_with(4096)

    # 3) Assert that if urlopen raises an exception, wait_healthy continues trying and
    # returns False when it times out (or after the timeout has passed).
    # We mock time.time to simulate time passing and mock time.sleep to avoid delay.
    time_values = [100, 100, 102, 104]
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")) as mock_urlopen, \
         patch("time.sleep") as mock_sleep, \
         patch("time.time", side_effect=time_values):
        assert wait_healthy("http://localhost:8000/health", timeout=2) is False
        assert mock_urlopen.call_count > 0
        assert mock_sleep.call_count > 0


def test_setup_run_install_subprocess_success():
    from unittest.mock import patch, MagicMock
    from scripts.setup import run_install

    mock_args = MagicMock()
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.returncode = 0

    with patch("scripts.setup.check_prerequisites", return_value=True), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("scripts.setup.wait_healthy", return_value=True), \
         patch("subprocess.run", return_value=mock_subprocess_result) as mock_run:
        
        run_install(mock_args)

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        
        argv = args[0]
        assert isinstance(argv, list)
        assert len(argv) > 0
        assert argv[0] == "docker"
        assert argv == ["docker", "compose", "up", "-d", "--build"]
        assert kwargs.get("shell") is not True


def test_setup_run_install_subprocess_failure():
    from unittest.mock import patch, MagicMock
    from scripts.setup import run_install

    mock_args = MagicMock()
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.returncode = 1

    with patch("scripts.setup.check_prerequisites", return_value=True), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("scripts.setup.wait_healthy", return_value=True), \
         patch("subprocess.run", return_value=mock_subprocess_result) as mock_run, \
         patch("sys.exit") as mock_exit:
        
        run_install(mock_args)

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        
        argv = args[0]
        assert isinstance(argv, list)
        assert len(argv) > 0
        assert argv[0] == "docker"
        assert kwargs.get("shell") is not True
        
        mock_exit.assert_called_once_with(1)

