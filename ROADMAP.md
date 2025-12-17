# Ghostline Browser Roadmap

The roadmap is organized as a series of overlapping tracks. Each track includes granular deliverables, success criteria, and checkpoints to ensure privacy and performance regressions are caught early.

## Phase 1: Foundation (Months 0–3)
- **Rendering and Networking Core**
  - Build a minimal but spec-aligned HTML/CSS parser with deterministic layout tests.
  - Implement HTTP/2 + HTTP/3 client with ALPN, connection coalescing guards, and per-profile connection pools.
  - Add content process sandboxing with strict seccomp profiles and allowlist-based filesystem access.
  - Establish deterministic startup sequence with structured logging for cold/warm start benchmarking.
- **PySide6 UI and Shell**
  - Standardize on a PySide6 + QtWebEngine application shell with typed signals/slots for navigation, chrome controls, and status surfaces.
  - Define a UI component library (toolbars, permission prompts, container switcher) with shared styles, dark/light themes, and accessibility baselines.
  - Create PySide6 end-to-end smoke tests that open windows, navigate, and assert load events to keep the UI stack regression-tested alongside engine changes.
  - Package PySide6 build tooling into the containerized dev environment, including Qt WebEngine dependencies and platform-specific bundling scripts.
- **Privacy Baseline**
  - Integrate the Resisting Fingerprinting (RFP) baseline: rounded timers, reduced precision in canvas/audio APIs, and user-agent unification.
  - Enforce partitioned cookies, storage, and cache keyed by top-level site and container identity.
  - Ship HTTPS-only mode as default with downgrade interstitials and HSTS preload list updates.
  - Build site-isolation plumbing with per-site process allocation and strict origin checks for cross-process messaging.
- **Security and Supply Chain**
  - Implement executable signing and reproducible build pipeline with pinned toolchains.
  - Create build reproducibility CI job comparing local and CI artifacts via hash diffing.
  - Stand up fuzzing harnesses for parsers, URL handling, and sandbox escape surfaces.
  - Document security response process, severity rubric, and SLAs for patch turnaround.
- **Developer Experience and Telemetry Guardrails**
  - Provide hermetic dev environment (containerized) with caching for toolchains and dependencies.
  - Add privacy-preserving telemetry toggles with metrics budgets and zero PII policy.
  - Publish coding standards for privacy-sensitive code paths and API review checklist.

## Phase 2: Network Privacy (Months 3–6)
- **Transport Privacy**
  - Integrate DNS-over-HTTPS and DNS-over-TLS with Encrypted Client Hello (ECH) and fallbacks with leak detection.
  - Add per-container proxy configuration with strict split-tunnel prevention and pre-flight leak tests.
  - Implement HTTPS-only enforcement at the connection manager level with downgrade reason logging.
- **Tor Mode**
  - Build opt-in Tor mode with bootstrap status UI, circuit isolation per container, and stream isolation tests.
  - Provide guard node pinning, circuit health monitoring, and automatic circuit rotation on fingerprintable errors.
  - Integrate pluggable transports for censorship evasion with auto-probing and user override controls.
- **Connection Hygiene**
  - Harden WebRTC against IP leaks: default mDNS, ICE policy enforcement, and STUN/TURN allowlists.
  - Create automatic proxy leak regression suite (DNS, IP, SNI, timing) executed per release candidate.
  - Add certificate pinning policy for first-party services and verify OCSP stapling/CRLite coverage.
- **User Controls**
  - Build privacy dashboard exposing connection mode, proxy state, and network errors with remediation tips.
  - Provide quick toggles for ECH, Tor mode, and HTTPS-only enforcement with clear warnings on downgrades.

## Phase 3: Advanced Fingerprinting Defenses (Months 6–9)
- **Uniformity Profiles**
  - Offer per-container uniformity presets (e.g., “strict”, “balanced”, “compat”) with deterministic capability masks.
  - Normalize fonts via bundled font packs with locale-aware defaults and explicit per-site overrides.
  - Gate high-entropy APIs (WebGL, WebGPU, AudioContext, Gamepads) with promptless denial in strict mode.
- **Entropy Budgeting**
  - Implement runtime entropy budgets with cross-API accounting; surface violations in devtools and telemetry.
  - Add device class randomization (GPU, memory, platform) with stability windows to avoid churn fingerprints.
  - Introduce canvas/audio noise injection with calibrated amplitude and per-origin seeds.
- **Measurement and Audits**
  - Build automated fingerprinting audit suite comparing uniformity across clean profiles and containers.
  - Integrate external fingerprinting testbeds (e.g., FPInspector-like) into CI with snapshot diffs.
  - Publish privacy scorecards per release showing deltas in entropy, pass/fail counts, and mitigations shipped.
- **Container UX**
  - Expand multi-container UX: color-coding, isolation badges, and default policy bundles.
  - Provide container templates for specific threat models (research, shopping, banking) with pre-tuned settings.

## Phase 4: Extension and Permission Hardening (Months 9–12)
- **Extension Platform**
  - Curate signed extension store with mandatory static analysis, permission review, and reproducible build requirements.
  - Enforce manifest-level capability gating, blocking sensitive APIs (native messaging, clipboard, file system) by default.
  - Add per-container extension allowlists/denylists with UI to clone configurations across containers.
  - Build extension sandbox monitoring with resource budgets (CPU, memory, network) and anomaly alerts.
- **Permission UX**
  - Redesign permission prompts with clear scope, duration (session/once/persistent), and expected data access.
  - Implement auto-revocation for unused permissions and exposure logging per origin.
  - Provide one-time permissions for camera/mic/geolocation, with automatic reset on tab close.
- **Policy and Governance**
  - Establish permission policy engine to enforce enterprise rules, compliance modes, and audit exports.
  - Add native messaging restrictions with allowlist-only connectors and signed host validation.

## Phase 5: Reliability, Response, and Performance (Months 12+)
- **Testing and Release Engineering**
  - Stand up full privacy CI: proxy leak suite, fingerprinting uniformity tests, Tor mode integration, and regression diffs.
  - Ship reproducibility dashboard comparing nightly, beta, and stable artifacts with variance alerts.
  - Build staged rollout tooling with kill switches, feature flags, and canary cohorts.
- **Incident Response and Monitoring**
  - Launch red-team program with quarterly exercises focused on fingerprinting bypass, sandbox escape, and network leaks.
  - Add crash/telemetry pipeline with client-side redaction, sampled uploads, and privacy budget enforcement.
  - Define on-call rotations, runbooks, and playbooks for privacy regressions and security incidents.
- **Performance and UX Polish**
  - Optimize cold start, page load, and input latency with automated profiling in CI for top sites.
  - Add power/CPU/bandwidth usage overlays and recommendations in the privacy dashboard.
  - Conduct usability studies for permission flows, Tor mode discoverability, and container management.
- **Community and Ecosystem**
  - Publish threat models, architecture docs, and changelogs for each release train.
  - Open-source privacy test harnesses and invite external contributions with clear governance.
  - Maintain compatibility matrix for extensions, Tor transports, and OS platforms with deprecation timelines.
