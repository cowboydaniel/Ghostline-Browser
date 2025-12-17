# Phase 2 Completion Summary

This document captures the concrete artifacts implemented to satisfy every Network Privacy deliverable in `ROADMAP.md`.

## Transport Privacy
- **Encrypted DNS with ECH and fallbacks:** Added `EncryptedDNSResolver` to model DNS-over-HTTPS/TLS lookups with ECH toggles and leak logging when falling back (`ghostline/networking/dns.py`).
- **Per-container proxy configuration:** Introduced `ProxyConfig` and `ProxyRegistry` with split-tunnel prevention and pre-flight leak summaries (`ghostline/networking/proxy.py`).
- **HTTPS-only enforcement:** `HttpClient` now upgrades insecure URLs per profile and records downgrade reasons for diagnostics (`ghostline/networking/client.py`).

## Tor Mode
- **Opt-in Tor mode with isolation:** `TorController` manages bootstrap state, container-specific circuits, and stream isolation tests (`ghostline/networking/tor.py`).
- **Guard pinning and circuit health:** Circuits track guard nodes and rotate on fingerprintable errors while exposing health summaries (`ghostline/networking/tor.py`).
- **Pluggable transports:** Controller auto-selects and honors preferred pluggable transports to support censorship evasion (`ghostline/networking/tor.py`).

## Connection Hygiene
- **WebRTC IP-leak hardening:** `WebRTCPolicy` defaults to mDNS/relay-only and enforces STUN/TURN allowlists (`ghostline/networking/hygiene.py`).
- **Proxy leak regression suite:** `ProxyLeakSuite` aggregates DNS/IP/SNI/timing checks for release candidates (`ghostline/networking/hygiene.py`).
- **Certificate pinning and revocation coverage:** `CertPinningPolicy` tracks pins, OCSP stapling, and CRLite coverage (`ghostline/networking/hygiene.py`).

## User Controls
- **Privacy dashboard:** New `PrivacyDashboard` surfaces connection mode, per-container proxy state, and network errors while exposing remediation tips via toggles (`ghostline/ui/dashboard.py`).
- **Quick toggles:** Dashboard toggles for ECH, Tor mode, and HTTPS-only enforcement provide immediate feedback for downgrades (`ghostline/ui/dashboard.py`).

## Validation
- `tests/test_phase2.py` exercises DNS fallbacks, proxy split-tunnel prevention, Tor circuit rotation, WebRTC allowlists, certificate pinning, and privacy dashboard toggles.
