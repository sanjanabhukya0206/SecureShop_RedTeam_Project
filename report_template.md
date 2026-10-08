# SecureShop Red Team / Application Security Report

## 1. Scope
Target: `http://127.0.0.1:8080`  
Scope: Own local lab application only.

## 2. Application
Technology: Python + Flask + SQLite  
Application: SecureShop

## 3. Outdated Component
| Component | Lab version | Current version identified | Security concern/CVE |
|---|---|---|---|
| Flask | 2.2.2 | Fill after checking official package/release information | Fill after verification |
| Werkzeug | 2.2.2 | Fill after checking official package/release information | Fill after verification |

Do not invent a CVE. Cite an official advisory if one applies.

## 4. ZAP Scan
- Scan date:
- ZAP version:
- Scan type:
- Target URL:
- Total alerts:
- High:
- Medium:
- Low:
- Informational:

## 5. Findings

### Finding 1 — A03 Injection / SQL Injection
**What:** Login uses unsafe SQL string construction.  
**Where:** `/login`  
**Why:** User input is concatenated into the SQL statement.  
**Impact:** Authentication logic can be manipulated.  
**Evidence:** Add ZAP request/response screenshot and local test result.  
**Fix:** Parameterized query.

### Finding 2 — A01 Broken Access Control / IDOR
**What:** Order history accepts a user-controlled `user_id`.  
**Where:** `/orders?user_id=...`  
**Why:** Server does not enforce ownership.  
**Impact:** A logged-in user may access another user's order history.  
**Evidence:** Screenshot before fix.  
**Fix:** Use the authenticated session identity and authorize every access.

### Finding 3 — A05 Security Misconfiguration
**What:** Debug mode and incomplete security headers.  
**Where:** Application configuration / HTTP responses.  
**Impact:** Excessive information exposure and weaker browser protections.  
**Fix:** Disable debug mode and add appropriate headers.

### Finding 4 — A07 Authentication/Session weakness
**What:** Weak development secret, plaintext passwords and no rate limiting.  
**Impact:** Credential/session compromise risk.  
**Fix:** Strong secret management, password hashing, rate limiting.

### Finding 5 — A06 Vulnerable/Outdated Components
**What:** Old framework/library versions are intentionally pinned.  
**Impact:** Unsupported or vulnerable dependencies can expose the application.  
**Fix:** Upgrade to supported versions and maintain dependency scanning.

## 6. Remediation
Describe each code/configuration change.

## 7. Retest
Repeat the same ZAP scan and manual checks.

| Finding | Before | After |
|---|---|---|
| SQL Injection | Vulnerable | Fixed |
| IDOR | Vulnerable | Fixed |
| Security headers/debug | Weak | Improved |
| Authentication/session | Weak | Improved |
| Outdated dependencies | Old | Upgraded |

## 8. Evidence Checklist
- [ ] Application running locally
- [ ] ZAP baseline scan
- [ ] ZAP alert screenshots
- [ ] Manual validation screenshots
- [ ] Code before/after
- [ ] Dependency version evidence
- [ ] Retest screenshots
- [ ] Final conclusion
