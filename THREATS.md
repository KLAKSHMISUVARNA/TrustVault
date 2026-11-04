# TrustVault – System Threat Model & Mitigation Analysis

This analysis maps the security vectors evaluated and mitigated during the TrustVault hardening review. It documents how our structural configurations enforce role isolation, protect file payloads, and maintain cryptographic audit trails.

---

## 1. Privilege Escalation via Client-Side Form Parameters
* **The Threat:** Public registration endpoints often allow attackers to submit raw parameters (e.g., `role=ADMIN`) using an API client or HTTP proxy to bypass client UI dropdown boxes and obtain system administration privileges.
* **How TrustVault Fixed It:** We decoupled the `role` field from the public registration form fields meta array in `accounts/forms.py`. The server explicitly overrides any client input upon form save, forcefully mapping all incoming public profile creation payloads to a standard `VIEWER` role parameter.
* **Remaining Limitations:** Administrative or Owner role mapping changes must be processed explicitly via direct server console interaction (`manage.py shell`) or back-end administrator panels.

## 2. In-Flight File Disguise & Spoofing (Extension Mismatches)
* **The Threat:** Attackers bypass simple file-extension filters by renaming dangerous binaries or malicious code targets (e.g., `payload.exe`) to look like harmless elements (e.g., `payload.pdf`).
* **How TrustVault Fixed It:** We built a custom structural file signature validator in `documents/validators.py`. When a file is uploaded, the engine intercepts the stream, reads the initial 8 structural header bytes (magic numbers), and explicitly verifies that the binary fingerprint matches the expected file format (e.g., confirming `%PDF` for documents). 
* **Remaining Limitations:** Plaintext assets (`.txt`) bypass byte signature inspection because they lack standard binary file magic headers.

## 3. Storage Invalidation & Unauthorized URL Access Leaks
* **The Threat:** Traditional applications store uploads inside a public web folder (e.g., `/media/uploads/`), creating static links that anyone can load or predict if they guess the file path or ID.
* **How TrustVault Fixed It:** We routed the `MEDIA_ROOT` configuration path in `config/settings.py` to point to a private directory (`private_storage/`) completely isolated outside the public static files path. The files are impossible to load directly via browser paths. Files are transferred exclusively via our secure view, which runs an authorization access check before streaming the binary data back to the client.
* **Remaining Limitations:** The system relies on the underlying host operating system to protect the file system folders from unauthorized local access.

## 4. Downstream Code Injection (Content Sniffing Attacks)
* **The Threat:** Browsers often attempt to identify file types automatically by reading their content streams (content sniffing). If an uploaded file contains hidden web code disguised as text, the browser may run that code automatically in the user's secure browser session.
* **How TrustVault Fixed It:** We hard-coded explicit response headers into our file download response stream in `documents/views.py`. The application transmits `X-Content-Type-Options: nosniff` to block type guessing, isolates downloaded components with a restrictive `Content-Security-Policy`, and forces immediate file down-streaming with explicit attachment dispositions.
* **Remaining Limitations:** Local client machines must use standard modern web browsers that properly respect and enforce these protection headers.

## 5. Audit Log Alteration & State Tampering Tracking
* **The Threat:** Administrators or attackers with database access can quietly rewrite audit trails to delete records of unauthorized downloads or modify timestamps to hide their tracking logs.
* **How TrustVault Fixed It:** We implemented a tamper-evident audit log ledger using an HMAC-SHA256 signature chain. Every system transaction event calculates its own signature using the record details combined with the previous record's hash signature and a secure, environment-isolated secret key. If a record is quietly altered, the signature verification chain fails immediately.
* **Remaining Limitations:** While this allows the system to instantly detect if data has been modified or tampered with, it does not prevent a root-level database user from deleting the entire log table history at once.

---
*Verified Operational Baseline: All 24 security and validation test routines are passing successfully.*
