"""Static smoke checks that do not require Flask to be installed."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_files_exist():
    for rel in ["app.py", "requirements.txt", "README.md", "templates/base.html", "fixed/app.py", "requirements-fixed.txt"]:
        assert (ROOT / rel).exists(), rel


def test_fixed_app_contains_core_controls():
    source = (ROOT / "fixed/app.py").read_text(encoding="utf-8")
    assert 'WHERE username=?' in source
    assert 'check_password_hash' in source
    assert 'session["user_id"]' in source
    assert 'debug=False' in source
    assert 'X-Content-Type-Options' in source
