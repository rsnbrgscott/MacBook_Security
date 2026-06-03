import pytest
from unittest.mock import patch

_CANNED = [
    {"name": "Test PASS",    "description": "d", "status": "PASS",    "raw": "ok",   "error": None},
    {"name": "Test FAIL",    "description": "d", "status": "FAIL",    "raw": "bad",  "error": None},
    {"name": "Test WARN",    "description": "d", "status": "WARN",    "raw": "note", "error": None},
    {"name": "Test UNKNOWN", "description": "d", "status": "UNKNOWN", "raw": "",     "error": "err"},
]


@pytest.fixture
def canned_results():
    return list(_CANNED)


@pytest.fixture
def flask_client(tmp_path):
    import history
    from app import app

    db_file = tmp_path / "test.db"
    app.config.update(
        TESTING=True,
        EXTERNAL_CALLS=False,
        REFRESH_INTERVAL=0,
        ALERT_INTERVAL=0,
        PORT=8000,
    )

    saved_conn = history._conn
    with patch.object(history, "_DB_PATH", db_file):
        history._conn = None
        history.init_db()
        with patch("app.run_all_collectors", return_value=list(_CANNED)):
            with app.test_client() as client:
                yield client
    history._conn = saved_conn
