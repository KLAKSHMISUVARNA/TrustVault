# TrustVault - Threat Model & Security Posture (THREATS.md)

## 1. Executive Summary
TrustVault is a secure document-sharing platform featuring granular Role-Based Access Control (Viewer, Owner, Admin), cryptographic audit trails, and strict private storage boundaries. This document outlines identified attack vectors, potential business impacts, and implemented technical countermeasures.

---

## 2. Threat Matrix

| Threat ID | Threat Description | Attack Vector | Severity | Mitigation Strategy | Implemented Controls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TV-01** | Privilege Escalation via Public Registration | Tampering with POST payload to inject `role=ADMIN` or brute-forcing hardcoded setup keys | **CRITICAL** | Server-side enforcement overriding client-supplied role values | Registration forms hardcode assignment to `Role.VIEWER`. Initial Admin accounts can only be created via the CLI `seed_test_accounts` command. |
| **TV-02** | Audit Trail Forgery & Key Compromise | Compromising Django's `SECRET_KEY` allowing retroactive tampering with HMAC audit chains | **CRITICAL** | Cryptographic key separation | `AUDIT_HMAC_KEY` is completely isolated from `SECRET_KEY`. Fail-fast checks abort startup if keys are shared or missing in production. |
| **TV-03** | Insecure Direct Object References (IDOR) & Broken Object-Level Authorization (BOLA) | Direct GET/POST to `/download/<id>/` or `/manage/<id>/` bypassing frontend checks | **HIGH** | Real-time database authorization barriers | Every view calls `can_access_document()` to verify ownership, active permissions (`READ` vs `EDIT`), and active user flags. Missing ownership yields 404/403 with audit logs. |
| **TV-04** | Malicious File Upload & MIME Spoofing | Uploading executables or shell scripts disguised with benign extensions (`.pdf`, `.docx`) | **HIGH** | True binary signature (magic-byte) analysis | `validate_document_file()` inspects header bytes (`%PDF`, `\x89PNG`, `PK\x03\x04`, `\xff\xd8\xff`) and checks for non-text/PE headers before accepting uploads. |
| **TV-05** | Arbitrary File Access via Path Traversal | Specifying directory traversal sequences (`../../etc/passwd`) via filenames | **HIGH** | Boundary enforcement on storage roots | Uploads are saved into an unexposed `private_storage/` root. File downloads verify that `os.path.abspath(file_path)` starts strictly within `settings.MEDIA_ROOT`. |
| **TV-06** | Information Leakage & Cache Exposure | Browsers caching private PDFs or MIME-sniffing malicious script payloads | **MEDIUM** | Strict defensive HTTP response headers | Download responses return `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none';`, and `Cache-Control: no-store, no-cache, must-revalidate`. |

---

## 3. Cryptographic Audit Chain Architecture

To ensure immutable accountability:
1. Every event (`DOCUMENT_UPLOADED`, `DOCUMENT_DOWNLOADED`, `DOCUMENT_ACCESS_DENIED`, `PERMISSION_GRANTED`, `PERMISSION_REVOKED`) is recorded in an atomic database transaction.
2. Each event payload includes: `actor_id`, `action`, `target_type`, `target_id`, `metadata`, `timestamp`, and `previous_hash`.
3. The event hash is generated via `HMAC-SHA256(AUDIT_HMAC_KEY, canonical_json_payload)`.
4. The admin dashboard invokes `verify_audit_chain()` using constant-time `hmac.compare_digest()` to detect any record tampering, deletions, or insertions.