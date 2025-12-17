# Ghostline Browser Engineering Plan

A privacy-hardened browser wrapper built on **Chromium via QtWebEngine**, with a **PySide6**-based desktop shell. The project focuses on hardening, enforcement, and productization on top of the QtWebEngine/Chromium rendering and networking stack.

## Vision and Goals
Build a privacy-first, security-hardened browser that matches Firefox-level usability/performance, delivers strong privacy protections aligned with Tor transport capabilities when enabled, and applies best-practice security hardening throughout. The goal is to measurably reduce tracking and exploitation risk while maintaining practical usability. Claims are grounded in testable, enforceable properties.

## Threat Model
* **Regional nation-state adversaries (threat level 6):** passive/active observers on local networks or ISPs performing traffic analysis, fingerprint correlation, timing/volume correlation, or content injection. Tor mode must assume hostile networks with sophisticated correlation capabilities.
* **Web trackers:** first/third-party trackers attempting cross-site correlation via fingerprinting, identifiers, or linkability through shared state.
* **Malicious websites:** attempting memory corruption, sandbox escapes, drive-by downloads, or permission abuse.
* **Malicious extensions or supply-chain compromises:** tampered builds, dependency poisoning, update-channel attacks, or unsigned code execution.
* **Device theft/local forensics:** access to local profile data; mitigated with OS/user disk encryption, not embedded encryption.
* **Non-goals:** cannot defeat global passive adversaries performing worldwide timing correlation; cannot guarantee anonymity against endpoint compromise or hardware implants; Tor mode inherits Tor Project's traffic analysis limits.

## Success Metrics
* **Fingerprinting resistance:** entropy budget aligned with Tor Browser's RFP (~10–13 bits per surface), measurable via metrics like AmIUnique and internal fuzzing; ≥95% of users share common uniformity profiles in default hardened mode. Deep engine-level anti-fingerprinting is limited by QtWebEngine surfaces unless the project begins patching Chromium.
* **Network invariant enforcement:** zero direct TCP/UDP egress from renderer, GPU, utility, and extension processes in Tor mode, verified via packet capture and automated leak tests in CI; all network traffic brokered through controlled SOCKS egress path.
* **Network anonymity options:** Tor transport mode achieving zero-leak compliance in Tor Browser leak tests; DoH/DoT with ECH opportunistically where available; strict proxy compliance verified in CI.
* **Exploit mitigation:** multi-process site isolation enabled by default; content processes sandboxed with seccomp-bpf, brokered filesystem/network access; minimum of quarterly red-team exercises with actionable findings closed within 60 days.
* **Supply-chain integrity:** all releases reproducible on at least two independent builders; updates signed with hardware-backed keys; SBOM published per release; 100% dependency pinning and scanning.

## Architecture Choice
* **Approach:** Build a privacy-hardened wrapper on Chromium via QtWebEngine rather than forking an engine or building from scratch.
  * **Inherited from Chromium/QtWebEngine:** Core rendering (Blink), networking (Chromium net stack), JavaScript (V8), storage (LevelDB), GPU acceleration, codec support, and site isolation primitives.
  * **Ghostline layer focus:** Hardening enforcement, anti-fingerprinting controls, network egress enforcement, privacy-preserving state partitioning, permission hardening, extension model constraints, and productization/UI via PySide6.
  * **Local-first architecture:** All features run entirely on-device with no cloud dependencies while still supporting loading any website.
  * **Extensibility:** Well-defined internal interfaces for hardening layers; future integration of proven components possible without inheriting legacy attack surface.
* **Trade-offs:** QtWebEngine constraints limit deep engine-level customization (e.g., Tor Browser-level uniformity across all surfaces). Chromium patching required for full parity; current focus is on enforceable invariants within QtWebEngine capabilities.
* **Mitigations:** Keep the hardening layer modular for auditability; design APIs that allow future Chromium patching or integration of custom components without architectural rewrites.

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
4. Use this entry point for UI-focused smoke tests (window creation, navigation, toolbar interactions) until broader hardening components land.

## Design Pillars

### Network Egress Enforcement
**Invariant:** All network traffic in Tor mode must be brokered through a single controlled egress path with strict SOCKS-only compliance. No renderer, GPU, utility, or extension process may establish direct TCP/UDP connections.

* **Standard mode:** Direct egress allowed; tracking protection and partitioned state enforce privacy at the application layer.
* **Hardened mode:** DoH/DoT enforced; speculative connections (preconnect, prefetch, DNS prefetch, predictor caches) disabled; WebRTC proxy-only with mDNS host candidates blocked.
* **Tor mode:** Strict SOCKS-only egress; all DNS, HTTP(S), WebSocket, and application-layer connections routed through Tor SOCKS proxy; no direct network access from any subprocess. Verified via:
  * **Packet capture tests in CI:** Launch Tor mode, visit test pages, capture traffic, assert zero non-loopback packets bypass Tor.
  * **Seccomp enforcement:** Renderer/GPU/utility processes have network syscalls (connect, sendto, sendmsg) blocked via seccomp-bpf unless explicitly brokered.
  * **Automated leak test suite:** DNS leak, WebRTC leak, QUIC leak, service worker background fetch, and extension network request tests run in CI with zero-tolerance failure policy.

### Anti-Fingerprinting Strategy
* **RFP-like baseline:** enable Resist Fingerprinting defaults (user agent, screen size bucketing, font whitelist, canvas randomization, time precision reduction, WebGL limits).
* **Entropy budgeting:** treat each API surface with an entropy budget; block or standardize surfaces that exceed target budget (e.g., canvas, Web Audio, battery, gamepads, sensors) unless explicitly allowed in a high-trust profile.
* **Uniformity profiles:** predefined buckets (e.g., desktop 1080p/1440p, laptop 900p) with deterministic rounding for screen, timezone UTC, locale defaults, and standardized media codecs to maximize crowd size.
* **Per-profile toggles:** normal mode uses partitioning + tracking protection; hardened mode enforces RFP defaults; Tor mode applies maximal uniformity, circuit isolation, and disables risky APIs (WebRTC without proxy, WebGL extensions).
* **Navigator and font controls:** frozen UA, reduced platform hints, strict font whitelist with optional bundled fonts to avoid system font enumeration.
* **Timing and performance:** clamped timers, jittered events, reduced performance.now resolution, and cross-origin isolation disabled unless user-approved.
* **QtWebEngine limits:** Deep engine-level anti-fingerprinting (e.g., GPU driver string spoofing, canvas extraction path modifications) is limited without Chromium patching. Current implementation focuses on standardization and API blocking within QtWebEngine capabilities.

### Traffic Analysis Resistance
**Adversary model (threat level 6):** Regional nation-state adversary capable of correlating timing, volume, and destination sets across network observation points. Defenses aim to reduce correlation effectiveness, not guarantee anonymity against global passive adversaries.

* **Standard mode:** No specific traffic analysis defenses; focus is on application-layer privacy.
* **Hardened mode:**
  * Disable speculative connections: preconnect, DNS prefetch, prefetch, predictor caches, QUIC connection migration.
  * Disable link preloading and background resource hints.
  * Enforce connection coalescing limits to reduce cross-site linkability.
* **Tor mode:**
  * **Inherit Tor transport defenses:** Circuit isolation, connection padding (if enabled in Tor daemon), and encrypted transport.
  * **Disable speculative connections:** Same as Hardened mode; prevent timing leaks from predictive fetches.
  * **Staged plan for application-layer padding (future):**
    * **Phase 1 (research):** Evaluate cover-traffic and inter-request padding schemes; document bandwidth/latency tradeoffs.
    * **Phase 2 (optional implementation):** Implement opt-in padding regimes with clear user-facing tradeoff documentation (e.g., "+50% bandwidth overhead, +200ms median latency for reduced timing correlation").
    * **Non-goals:** No guarantees against global passive adversaries; no constant-rate cover traffic without explicit user opt-in and clear cost warnings.
  * **Test expectations:** Automated tests verify zero speculative connections in Tor mode via packet capture; timing analysis harnesses compare against Tor Browser baselines where applicable.

## Isolation Model
* **Site isolation:** strict site-per-process with origin keying; enable Project Fission equivalents; isolate extension processes from content.
* **Per-site containers:** first-party sets get isolated storage/identity; manual containers for advanced users; Tor mode isolates per-tab circuit and storage.
* **Process sandboxing:** hardened seccomp policies, namespace isolation, brokered file/network access; GPU and media processes sandboxed with minimal permissions.
* **Download and helper isolation:** separate utility processes for decoding/parsing untrusted formats; enforce Safe Browsing-equivalent malware checks without telemetry-driven data collection (local blocklists).

## Network Privacy Options
* **Modes:**
  * **Standard:** tracking protection + partitioned state; DoH auto-upgrade with fallback to system resolver when policy allows; speculative connections enabled.
  * **Hardened:** DoH/DoT enforced; ECH opportunistically where endpoints reliably support (test expectations: verify ECH handshake success for known-supporting domains, graceful fallback otherwise); WebRTC proxy-only with mDNS host candidates blocked; speculative connections disabled; optional per-container SOCKS5.
  * **Tor transport mode:** Toggleable profile launching Tor daemon or using system Tor; enforce SOCKS-only egress with zero direct network access (verified in CI); connection padding (if Tor daemon configured); first-party circuit isolation per tab; blocked non-proxied traffic via seccomp and routing enforcement. **Note:** This is Tor *transport mode* (Tor as egress), not full Tor Browser parity. QtWebEngine constraints limit engine-level fingerprint uniformity; matching Tor Browser's fingerprint homogeneity is not guaranteed without Chromium patching.
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
* **Network egress:** In Tor mode, extension network requests are routed through SOCKS proxy with same zero-direct-egress invariant as renderer processes; verified via seccomp and packet capture tests.
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
* **Tor integration maintenance burden:** track Tor Browser patches where applicable; upstream fixes; minimize custom Tor diffs. Note that full Tor Browser parity requires Chromium patching not currently planned.
* **QtWebEngine fingerprinting limits:** Deep anti-fingerprinting (canvas internals, GPU strings, etc.) is constrained by QtWebEngine; future Chromium patching required for full parity with Tor Browser.
* **Supply-chain exposure via dependencies:** strict pinning, mirrored repositories, and continuous SBOM scanning; automated provenance attestation.
* **User misconfiguration:** ship safe defaults, clear UI indicators, and hardened presets to avoid weakening protections.

## Test Plan
* **Network egress enforcement tests:** Packet capture in CI for Tor mode; verify zero non-loopback egress; test renderer, GPU, utility, extension process egress blocking via seccomp and routing verification.
* **Privacy leak tests:** automated suites covering DNS leak, WebRTC leak, QUIC leak, proxy bypass, referrer stripping, cookie partitioning, service worker isolation, cache partition, and extension network isolation tests.
* **Fingerprinting audits:** run AmIUnique/Panopticlick-style harnesses; entropy measurement per API; compare against Tor Browser baselines where applicable; fuzzing for subtle leaks (canvas, audio, font, timing).
* **Traffic analysis validation:** Verify zero speculative connections in Hardened and Tor modes via packet capture; ECH handshake correctness for supporting endpoints; proxy PAC adherence.
* **Network anonymity validation:** Tor mode circuit isolation checks, traffic capture to verify no direct DNS/connection leaks; DoH correctness.
* **Exploit resilience:** sandbox escape testing, seccomp policy fuzzing, IPC fuzzing, and GPU/media parser hardening tests; ASLR/CFI/Shadow Stack verification where platform supports.
* **Supply-chain checks:** reproducible build verification, signature validation tests, SBOM diff scans, dependency vulnerability scanning in CI.
* **Red-teaming:** periodic internal and external red-team events; tabletop exercises for incident response; bug bounty intake validation.

## What this cannot guarantee and why
* Cannot guarantee anonymity against global passive adversaries performing large-scale timing correlation or against endpoint compromise; Tor mode inherits Tor Project's traffic analysis limits and provides Tor *transport*, not full Tor Browser parity.
* Cannot prevent user-installed extensions from exfiltrating data if granted broad permissions; curated store and warnings reduce but do not eliminate risk.
* Cannot fully stop fingerprinting by highly targeted actors; defenses aim to reduce entropy and increase crowd size, not make tracking impossible. QtWebEngine constraints limit deep engine-level anti-fingerprinting without Chromium patching.
* Cannot protect against compromised operating systems, rootkits, or malicious hardware collecting data out-of-band.
* Traffic analysis defenses (padding, timing obfuscation) are best-effort and come with performance tradeoffs; no guarantees against sophisticated correlation attacks by regional or global adversaries.

## User education and safe defaults
* Ship with safest defaults practical: RFP-like hardening, partitioned storage, tracking protection, HTTPS-only, and DoH enabled.
* Provide clear mode indicators (Standard/Hardened/Tor) and explain trade-offs in onboarding; distinguish "Tor transport mode" from "Tor Browser parity".
* Offer guided tutorials on containers, proxy/Tor usage, and recognizing permission prompts.
* Include a privacy report card per site to show blocked trackers, partitioned data, active protections, and network egress mode, reinforcing informed usage.
