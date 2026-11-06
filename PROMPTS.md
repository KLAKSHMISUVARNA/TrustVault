# TrustVault – AI Development Prompt Logs & Verification History

This log documents the interactive prompt history, code generation cycles, and manual security reviews conducted during the architectural hardening of TrustVault.

---

## Entry 1: Core System Security Review (Phase 4)
- **Date:** November 4, 2026
- **Objective:** Perform a deep architectural review of the file transport endpoints and settings keys.
- **Prompt Used:** "I am running a code review for config/settings.py, documents/forms.py, documents/permissions.py, and documents/views.py. Inspect my code changes for structural vulnerabilities, privilege escalation, or exposed secrets before I commit."
- **AI Output:** Provided baseline structural views and recommended isolating secrets using environment variables.
- **Flaws Identified:** The initial suggestion relied on a standard file extension validation layer without auditing the file content byte markers, leaving the system open to file-spoofing attacks.
- **Manual Correction:** Implemented explicit validation checks to reject empty data structures (0 bytes) and enforce environment variable injection constraints before staging the commit.

## Entry 2: Public Account Privilege Escalation (Phase 9)
- **Date:** November 4, 2026
- **Objective:** Secure the user account creation endpoint to block unauthorized role assignments.
- **Prompt Used:** "Review my accounts/forms.py and accounts/views.py implementation. Ensure users cannot intercept or manipulate registration requests to escalate privileges."
- **AI Output:** Generated a form layout that included choice selection drop-down parameters for roles directly in the public registration metadata array.
- **Flaws Identified:** Including the `role` field in the public `Meta.fields` array allowed attackers to bypass the drop-down menu using standard HTTP proxies or API tools and inject arbitrary payloads like `role=ADMIN` directly into the database.
- **Manual Correction:** Stripped the `role` choice out of the public registration fields completely. Configured the model's `save()` routine on the server side to forcefully default all public registrations to a `VIEWER` attribute layout.

## Entry 3: Hardening Download Binary Streams (Phase 10)
- **Date:** November 4, 2026
- **Objective:** Prevent malicious cross-site code execution through file transfers.
- **Prompt Used:** "Secure my document download view inside documents/views.py. Make sure files cannot be executed or sniffed maliciously by web browsers."
- **AI Output:** Provided a standard Django `FileResponse` object configuration mapping that lacked specific security headers.
- **Flaws Identified:** The output omitted modern browser-hardening headers, leaving clients open to content-sniffing exploits where a browser attempts to run web code hidden inside non-executable extensions.
- **Manual Correction:** Hard-coded explicit response headers (`X-Content-Type-Options: nosniff`, restrictive `Content-Security-Policy`, and immediate attachment dispositions) directly into the view logic.

## Entry 4: Secure Private Storage Implementation (Phase 6 Hardening)
- **Date:** November 4, 2026
- **Objective:** Completely isolate uploaded documents out of public web path accessibility.
- **Prompt Used:** "Configure my config/settings.py to use an isolated folder directory structure so uploaded documents cannot be accessed via direct web path links."
- **AI Output:** Suggested mapping `MEDIA_URL` and `MEDIA_ROOT` paths directly to the public application asset roots.
- **Flaws Identified:** Storing documents inside public folders exposes them to direct URL scraping if an attacker guesses or brute-forces the file path or numeric ID.
- **Manual Correction:** Routed `MEDIA_ROOT` to a private directory (`private_storage/`) outside the public web server scope and forced all access traffic through our authorization permissions view layer.

## Entry 5: Designing the Dark Security Dashboard UI (Phase 13 & 14)
- **Date:** November 4, 2026
- **Objective:** Style all authentication, management, and log interfaces using a dark navy theme.
- **Prompt Used:** "Build a professional CSS template file and apply it across all my accounts, login, registration, and management HTML files using dark navy security colors."
- **AI Output:** Provided separate styles inside the individual HTML pages rather than linking them to a centralized stylesheet.
- **Flaws Identified:** Inlining styles breaks maintainability rules and increases code duplication across different roles and templates.
- **Manual Correction:** Created a unified, reusable CSS file inside `static/css/styles.css` and mapped it globally across all templates via `STATICFILES_DIRS`.

## Entry 6: Binary File Signature Validation & Polyglot Prevention (Phase 15)
- **Date:** November 6, 2026
- **Objective:** Enforce zero-trust validation on uploaded file contents to prevent malicious executable execution.
- **Prompt Used:** "Implement file-signature validation for uploaded files in documents/validators.py to prevent file-extension spoofing without introducing external native C-library dependencies."
- **AI Output:** Proposed integrating third-party wrapper libraries like `python-magic`, which would introduce compilation and external DLL dependencies on host environments.
- **Flaws Identified:** Adding external non-pure-Python packages creates platform instability across deployment environments. Furthermore, simple magic-number matching failed to catch polyglot executables hidden inside valid file wrappers.
- **Manual Correction:** Re-engineered `documents/validators.py` using pure Python standard libraries (`zipfile` and header slicing). Added explicit header magic byte validation for PDF (`%PDF`), PNG (`\x89PNG\r\n\x1a\n`), JPEG (`\xff\xd8\xff`), and OpenXML DOCX archive structures (`PK\x03\x04` containing `[Content_Types].xml`), while rejecting PE/ELF headers masquerading as `.txt`.

## Entry 7: Cryptographic Audit Hash Separation & Schema Remediation (Phase 16)
- **Date:** November 6, 2026
- **Objective:** Isolate HMAC audit trail signing from core web application sessions and fix model attribute mismatches.
- **Prompt Used:** "Audit config/settings.py and audit/views.py for HMAC key isolation and schema inconsistencies."
- **AI Output:** Reassigned `AUDIT_HMAC_KEY = SECRET_KEY` in settings and attempted to log audit entries using raw unverified keyword arguments in views.
- **Flaws Identified:** Conflating `SECRET_KEY` and `AUDIT_HMAC_KEY` exposes the immutable audit log chain if the session secret is rotated or breached. Furthermore, views queried `created_at` and `current_hash`, triggering field exceptions against `AuditEvent`'s actual schema (`timestamp` and `event_hash`).
- **Manual Correction:** Enforced distinct environment keys for `SECRET_KEY` and `AUDIT_HMAC_KEY` with strict production validation checks. Built an adapter in `audit/services.py` (`record_audit_event`) to translate view-level parameters (`document`, `ip_address`, `details`) into canonical schema payloads (`target_type`, `target_id`, `metadata`).

## Entry 8: Real-Time BOLA / IDOR Defense & URL Route Alignment (Phase 17)
- **Date:** November 6, 2026
- **Objective:** Synchronize URL routing endpoints with granular permission checks to satisfy the test suite.
- **Prompt Used:** "Resolve naming mismatches between documents/urls.py and documents/views.py, and enforce real-time database permission checks."
- **AI Output:** Suggested generic function names (`document_upload_view`, `document_detail_view`) and raised HTTP 403 `PermissionDenied` indiscriminately across all endpoints.
- **Flaws Identified:** `documents/urls.py` strictly expected exact names (`upload_document`, `manage_permissions`, `download_document`). Additionally, returning HTTP 403 when non-owners queried permission endpoints leaked information about document existence.
- **Manual Correction:** Aligned `documents/views.py` 1:1 with `urls.py`. Configured non-owner access on management endpoints to return HTTP 404 (`Http404`) to prevent object enumeration, while logging `DOCUMENT_ACCESS_DENIED` security audit events into the database chain.

## Entry 9: Database Schema Integrity & Windows Resource Teardown (Phase 18)
- **Date:** November 6, 2026
- **Objective:** Fix SQLite `NOT NULL` constraint violations and Windows OS file-lock race conditions during test suite runs.
- **Prompt Used:** "Debug the test failure: IntegrityError: NOT NULL constraint failed: documents_document.file_size and WinError 32 during test cleanup."
- **AI Output:** Suggested relaxing database constraints by making `file_size` nullable (`null=True, blank=True`).
- **Flaws Identified:** Making security-critical metadata nullable weakens data integrity and breaks existing model contracts. Leaving file streams unmanaged also triggered Windows OS file-locking collisions during test cleanup.
- **Manual Correction:** Populated `document.file_size` directly from `form.cleaned_data['file'].size` within an atomic database transaction in `upload_document`, supplemented with a defensive fallback in `Document.save()`. Resolved Windows temp file locks by passing native file descriptors cleanly to `FileResponse`. Successfully brought the test suite to **26/26 passing tests**.