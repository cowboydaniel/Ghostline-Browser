# Ghostline Browser Engineering Plan

For milestone details, see [ROADMAP.md](ROADMAP.md). The desktop shell is built with **PySide6** and QtWebEngine to keep the UI stack fully Python-based while aligning with the roadmap’s privacy goals.

## Vision and Goals
Build a privacy-first, security-hardened browser that matches Firefox-level usability/performance, delivers Tor Browser-level privacy protections when enabled, and applies best-practice security hardening throughout. Claims of being "untrackable" are avoided; the goal is to measurably reduce tracking and exploitation risk while maintaining practical usability.

## Threat Model
* **Network adversaries:** passive/active observers on local networks or ISPs performing traffic analysis, fingerprint correlation, or content injection. Tor mode must assume hostile networks.
* **Web trackers:** first/third-party trackers attempting cross-site correlation via fingerprinting, identifiers, or linkability through shared state.
* **Malicious websites:** attempting memory corruption, sandbox escapes, drive-by downloads, or permission abuse.
* **Malicious extensions or supply-chain compromises:** tampered builds, dependency poisoning, update-channel attacks, or unsigned code execution.
* **Device theft/local forensics:** access to local profile data; mitigated with OS/user disk encryption, not embedded encryption.
* **Non-goals:** cannot defeat targeted hardware implants or global timing correlation against Tor beyond Tor Project guarantees.

## Success Metrics
* **Fingerprinting resistance:** entropy budget aligned with Tor Browser’s RFP (~10–13 bits per surface), measurable via metrics like AmIUnique and internal fuzzing; ≥95% of users share common uniformity profiles in default hardened mode.
* **Network anonymity options:** Tor mode achieving parity with Tor Browser leak tests; DoH/DoT with ECH where available; strict proxy compliance (no direct leaks) verified in CI.
* **Exploit mitigation:** multi-process site isolation enabled by default; content processes sandboxed with seccomp-bpf, brokered filesystem/network access; minimum of quarterly red-team exercises with actionable findings closed within 60 days.
* **Supply-chain integrity:** all releases reproducible on at least two independent builders; updates signed with hardware-backed keys; SBOM published per release; 100% dependency pinning and scanning.

## Architecture Choice
* **Approach:** Build a custom browser stack from scratch rather than forking an existing engine.
  * Rendering, networking, storage, and UI layers are designed together to enforce privacy and security constraints end-to-end.
  * Local-first architecture: all features run entirely on-device with no cloud dependencies while still supporting loading any website.
  * Extensibility is achieved via well-defined internal interfaces instead of upstream patching.
* **Mitigations:** Keep the codebase modular for auditability; design APIs that allow future integration of proven components without inheriting legacy attack surface.

## Building and Running (PySide6)
1. Install Python 3.11+ and ensure Qt WebEngine dependencies are available for your platform.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the PySide6 shell:
   ```bash
   python main.py
   ```
4. Use this entry point for UI-focused smoke tests (window creation, navigation, toolbar interactions) until broader engine components land.

## Anti-Fingerprinting Strategy
* **RFP-like baseline:** enable Resist Fingerprinting defaults (user agent, screen size bucketing, font whitelist, canvas randomization, time precision reduction, WebGL limits).
* **Entropy budgeting:** treat each API surface with an entropy budget; block or standardize surfaces that exceed target budget (e.g., canvas, Web Audio, battery, gamepads, sensors) unless explicitly allowed in a high-trust profile.
* **Uniformity profiles:** predefined buckets (e.g., desktop 1080p/1440p, laptop 900p) with deterministic rounding for screen, timezone UTC, locale defaults, and standardized media codecs to maximize crowd size.
* **Per-profile toggles:** normal mode uses partitioning + tracking protection; hardened mode enforces RFP defaults; Tor mode applies maximal uniformity, circuit isolation, and disables risky APIs (WebRTC without proxy, WebGL extensions).
* **Navigator and font controls:** frozen UA, reduced platform hints, strict font whitelist with optional bundled fonts to avoid system font enumeration.
* **Timing and performance:** clamped timers, jittered events, reduced performance.now resolution, and cross-origin isolation disabled unless user-approved.

## Isolation Model
* **Site isolation:** strict site-per-process with origin keying; enable Project Fission equivalents; isolate extension processes from content.
* **Per-site containers:** first-party sets get isolated storage/identity; manual containers for advanced users; Tor mode isolates per-tab circuit and storage.
* **Process sandboxing:** hardened seccomp policies, namespace isolation, brokered file/network access; GPU and media processes sandboxed with minimal permissions.
* **Download and helper isolation:** separate utility processes for decoding/parsing untrusted formats; enforce Safe Browsing-equivalent malware checks without telemetry-driven data collection (local blocklists).

## Network Privacy Options
* **Modes:**
  * **Standard:** tracking protection + partitioned state; DoH auto-upgrade with fallback to system resolver when policy allows.
  * **Hardened:** DoH/DoT enforced, ESNI/ECH when endpoints support; WebRTC proxy-only with mDNS host candidates; optional per-container SOCKS5.
  * **Tor integration:** toggleable profile launching Tor daemon or using system Tor; enforce SOCKS-only (no DNS leaks), connection padding, first-party circuit isolation, and blocked non-proxied traffic.
* **Proxy/VPN support:** manual proxies per-container; respects PAC policies; disables prefetching, speculative connections, and DNS over insecure channels when proxy enabled.
* **Transport hygiene:** HTTPS-only mode, HSTS preload updates; OCSP stapling and CRLite/OneCRL-style revocation checks; connection coalescing limited to first-party sets to reduce cross-site linkability.

## State Partitioning and Data Handling
* **Partitioned storage:** cookies, localStorage, IndexedDB, cache, HSTS, and service workers keyed by top-level site/first-party set; disable shared cache.
* **Ephemeral modes:** optional ephemeral containers and temporary sessions; clear-on-close for Tor/hardened profiles.
* **History and download hygiene:** sanitize referrers (trim cross-site), strip link decoration parameters on navigation, and sanitize saved file metadata.
* **Storage access policy:** Storage Access API gated by user gesture and per-site container; third-party cookies blocked by default.

## Permission Hardening
* **Prompt discipline:** deny-by-default for camera/mic/USB/HID/sensors; require transient user gestures and per-site scoping.
* **Lifetime controls:** time-bounded grants; auto-revocation on inactivity; per-container scoping.
* **UI safeguards:** clear, per-tab indicators; highlight proxy/Tor mode; one-time permissions for screen sharing and clipboard.
* **Dangerous API policy:** disable or gate WebRTC local IP enumeration, Web Bluetooth, Serial, HID, and MIDI unless in explicit allowlist mode.

## Extension Model Constraints
* **Store policy:** curated, signed extensions only; optional compatibility layer for selected Firefox AMO items after review.
* **Permission review:** request shielding, warning overlays for powerful permissions (broad host access, native messaging); deny native messaging except approved enterprise builds.
* **Isolation:** extensions run in isolated processes with no file system access; restrict content-script injection to declared hosts; enforce CSP for extension pages.
* **Update control:** pinned versions for high-privilege extensions; reproducible builds for first-party add-ons.

## Update, Signing, and Supply-Chain Integrity
* **Update pipeline:** updates delivered over TLS + signed manifests; staged rollouts with canary and rollback; update keys stored in HSM.
* **Code signing:** all binaries signed; signature enforced at install and update; verify WASM signatures where applicable.
* **Dependency hygiene:** lockfiles for all tooling; vendor critical libraries; SBOM published; automated SLSA/Sigstore attestations.
* **Build isolation:** hermetic builds with pinned compilers/SDKs; minimal build images; artifact scanning (malware and policy checks).

## Reproducible Builds
* **Determinism:** SOURCE_DATE_EPOCH, normalized file ordering, and deterministic compression; documented build scripts.
* **Verification:** two independent builders produce identical hashes per release; public reproducibility dashboard.
* **Auditing:** regular diffoscope runs on release candidates; fail release if non-determinism is detected.

## Telemetry and Data Collection Policy
* **Default off:** no background telemetry, pings, or crash uploads by default; crash reports require opt-in with redaction and local preview.
* **On-device analytics:** privacy-preserving metrics (e.g., RAPPOR-like or differential privacy) only when explicitly enabled; no third-party analytics SDKs.
* **Transparency:** public data collection documentation; all probes documented with rationale and retention limits.

## Security Response Process
* **Vulnerability intake:** security.txt, encrypted reporting channel, 24-hour triage SLA.
* **Patch management:** severity-based SLAs (critical: 7 days to patch in supported branches); hotfix channel for out-of-band updates.
* **Bug bounty:** scope aligned with browser features and Tor mode; rewards scaled by exploitation potential and privacy impact.
* **Coordination:** participate in shared CVE coordination with Mozilla/Tor for overlapping code; embargoed patch handling.

## Major Risks and Mitigations
* **Performance regressions from defenses:** monitor perf budgets vs. Firefox; provide per-site overrides; invest in caching that respects partitioning.
* **Web compatibility issues from RFP/blocked APIs:** maintain allowlist mechanism with visible warnings; ship documented override UI; partner with major sites for testing.
* **Tor integration maintenance burden:** track Tor Browser patches; upstream fixes; minimize custom Tor diffs.
* **Supply-chain exposure via dependencies:** strict pinning, mirrored repositories, and continuous SBOM scanning; automated provenance attestation.
* **User misconfiguration:** ship safe defaults, clear UI indicators, and hardened presets to avoid weakening protections.

## Test Plan
* **Privacy leak tests:** automated suites covering DNS leak, WebRTC leak, proxy bypass, referrer stripping, cookie partitioning, service worker isolation, and cache partition tests.
* **Fingerprinting audits:** run AmIUnique/Panopticlick-style harnesses; entropy measurement per API; compare against Tor Browser baselines; fuzzing for subtle leaks (canvas, audio, font, timing).
* **Network anonymity validation:** Tor mode circuit isolation checks, traffic capture to verify no direct DNS/connection leaks; ECH/DoH correctness; proxy PAC adherence.
* **Exploit resilience:** sandbox escape testing, seccomp policy fuzzing, IPC fuzzing, and GPU/media parser hardening tests; ASLR/CFI/Shadow Stack verification where platform supports.
* **Supply-chain checks:** reproducible build verification, signature validation tests, SBOM diff scans, dependency vulnerability scanning in CI.
* **Red-teaming:** periodic internal and external red-team events; tabletop exercises for incident response; bug bounty intake validation.

## What this cannot guarantee and why
* Cannot guarantee anonymity against global adversaries performing large-scale timing correlation or against endpoint compromise; Tor mode inherits Tor’s limits.
* Cannot prevent user-installed extensions from exfiltrating data if granted broad permissions; curated store and warnings reduce but do not eliminate risk.
* Cannot fully stop fingerprinting by highly targeted actors; defenses aim to reduce entropy and increase crowd size, not make tracking impossible.
* Cannot protect against compromised operating systems, rootkits, or malicious hardware collecting data out-of-band.

## User education and safe defaults
* Ship with safest defaults practical: RFP-like hardening, partitioned storage, tracking protection, HTTPS-only, and DoH enabled.
* Provide clear mode indicators (Standard/Hardened/Tor) and explain trade-offs in onboarding.
* Offer guided tutorials on containers, proxy/Tor usage, and recognizing permission prompts.
* Include a privacy report card per site to show blocked trackers, partitioned data, and active protections, reinforcing informed usage.
