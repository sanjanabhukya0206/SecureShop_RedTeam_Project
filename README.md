# SecureShop — Red Team / Application Security Lab

SecureShop is a **local-only Flask e-commerce training application** designed for an application-security lab. It intentionally contains controlled weaknesses so students can follow:

**BUILD → EXPOSE → SCAN → INVESTIGATE → VALIDATE SAFELY → FIX → RETEST → REPORT**

> Use only on `127.0.0.1` or another system you own/are explicitly authorized to test. Do not expose the vulnerable version to the Internet.

## Included functionality

- Home page and product catalogue
- Product search/details
- Registration and login
- Profile and order history
- Cart/order creation
- Admin area and user management
- Health endpoint
- Deliberately vulnerable red-team version
- Hardened reference implementation in `fixed/`
- Windows launcher and report template
- Basic project smoke tests

## Intentional weaknesses in the lab version

1. **A03 Injection — SQL Injection:** `/login` builds a SQL query by concatenating form input.
2. **A01 Broken Access Control — IDOR:** `/orders?user_id=<id>` trusts a request parameter for ownership.
3. **A05 Security Misconfiguration:** debug mode is enabled and security headers are intentionally incomplete.
4. **Authentication/session weaknesses:** weak development secret, plaintext passwords and no rate limiting.
5. **A06 Vulnerable/Outdated Components:** `requirements.txt` pins old Flask/Werkzeug versions for controlled lab comparison.

The `fixed/` version removes these core weaknesses by using parameterized SQL, password hashing, authenticated ownership checks, safer configuration and security headers.

## Run the vulnerable lab version — Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:8080`

Demo accounts:
- `admin / admin123`
- `student / student123`

## Run the fixed version

From the project root:

```powershell
py -m venv .venv-fixed
.\.venv-fixed\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-fixed.txt
$env:SECRET_KEY = "replace-with-a-long-random-value"
python fixed\app.py
```

The fixed version uses a separate SQLite database, `secureshop_fixed.db`.

## ZAP workflow

Use OWASP ZAP only against:

`http://127.0.0.1:8080`

Record the ZAP version, scan type, alert count, severity, affected URL and evidence. Run the same checks against the fixed version and compare the results.

## Safe manual validation

- Verify normal login works.
- Inspect `/login` for unsafe SQL construction in the source and document the behavior locally.
- Log in as `student` and compare `/orders` with and without a `user_id` parameter to demonstrate the authorization flaw.
- Inspect response headers and debug behavior.
- Compare dependency versions against supported releases using authoritative package/advisory information.
- Repeat the checks against `fixed/app.py` and record the remediation.

## Project structure

```text
SecureShop_RedTeam_Project/
├── app.py                    # intentionally vulnerable lab app
├── requirements.txt          # intentionally old lab dependencies
├── run_windows.bat
├── README.md
├── PROJECT_CHECKLIST.md
├── report_template.md
├── templates/
├── static/
├── tests/
└── fixed/
    ├── app.py                # hardened reference implementation
    ├── requirements-fixed.txt
    ├── templates/
    └── static/
```

## Important

This is an educational security lab, not a production store. The vulnerable version deliberately contains insecure code and should remain local and isolated.
