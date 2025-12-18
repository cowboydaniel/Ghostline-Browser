"""JavaScript injection for anti-fingerprinting enforcement.

This module generates JavaScript code that overrides browser APIs to enforce
the privacy protections calculated by the DeviceRandomizer, NoiseCalibrator,
and UniformityManager. The generated JavaScript is injected into pages at
DocumentCreation time using QtWebEngine's QWebEngineScript system.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ghostline.ui.dashboard import PrivacyDashboard


class NavigatorSpoofGenerator:
    """Generates JavaScript to spoof navigator properties."""

    @staticmethod
    def generate(device: Dict[str, str | int], user_agent: str) -> str:
        """Generate navigator spoofing JavaScript.

        Args:
            device: Dictionary with 'platform', 'memory_gb', and 'gpu' keys
            user_agent: User agent string to set

        Returns:
            JavaScript code that overrides navigator properties
        """
        platform = device.get('platform', 'Linux')
        memory_gb = device.get('memory_gb', 8)
        cores = 4 if memory_gb <= 4 else (8 if memory_gb <= 8 else 16)

        # appVersion is userAgent without the "Mozilla/" prefix
        app_version = user_agent.replace('Mozilla/', '') if user_agent.startswith('Mozilla/') else user_agent

        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // NAVIGATOR SPOOFING
  // ═══════════════════════════════════════════════════════

  Object.defineProperty(navigator, 'userAgent', {{
    get: () => '{user_agent}',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'appVersion', {{
    get: () => '{app_version}',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'appCodeName', {{
    get: () => 'Mozilla',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'appName', {{
    get: () => 'Netscape',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'product', {{
    get: () => 'Gecko',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'productSub', {{
    get: () => '20030107',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'vendor', {{
    get: () => 'Google Inc.',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'vendorSub', {{
    get: () => '',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'platform', {{
    get: () => '{platform} x86_64',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'hardwareConcurrency', {{
    get: () => {cores},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'deviceMemory', {{
    get: () => {memory_gb},
    configurable: false,
    enumerable: true
  }});
"""
        return js_code


class PluginsAndMimeTypesSpoofGenerator:
    """Generates JavaScript to spoof navigator.plugins and navigator.mimeTypes."""

    @staticmethod
    def generate() -> str:
        """Generate plugins and mimeTypes spoofing JavaScript.

        Returns:
            JavaScript code that returns empty/generic plugins list
        """
        # Return empty plugins/mimeTypes to avoid fingerprinting via installed plugins
        js_code = """
  // ═══════════════════════════════════════════════════════
  // PLUGINS AND MIME TYPES SPOOFING
  // ═══════════════════════════════════════════════════════

  // Override navigator.plugins with an empty list-like object
  const emptyPluginArray = {
    length: 0,
    item: function(index) { return null; },
    namedItem: function(name) { return null; },
    refresh: function() { },
    [Symbol.iterator]: function*() { }
  };

  Object.defineProperty(navigator, 'plugins', {
    get: () => emptyPluginArray,
    configurable: false,
    enumerable: true
  });

  // Override navigator.mimeTypes with an empty list-like object
  const emptyMimeTypes = {
    length: 0,
    item: function(index) { return null; },
    namedItem: function(name) { return null; },
    [Symbol.iterator]: function*() { }
  };

  Object.defineProperty(navigator, 'mimeTypes', {
    get: () => emptyMimeTypes,
    configurable: false,
    enumerable: true
  });
"""
        return js_code


class UserAgentDataSpoofGenerator:
    """Generates JavaScript to spoof navigator.userAgentData (Client Hints API)."""

    @staticmethod
    def generate(platform: str) -> str:
        """Generate userAgentData spoofing JavaScript.

        Args:
            platform: Platform string to report (e.g., "Windows", "macOS", "Linux")

        Returns:
            JavaScript code that overrides navigator.userAgentData
        """
        # Extract major version from platform if needed
        major_version = "134"  # Match modern Chromium version

        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // USER AGENT DATA (CLIENT HINTS API) SPOOFING
  // ═══════════════════════════════════════════════════════

  const spoofedUserAgentData = {{
    brands: [
      {{ brand: "Not:A-Brand", version: "24" }},
      {{ brand: "Chromium", version: "{major_version}" }}
    ],
    mobile: false,
    platform: "{platform}",
    platformVersion: "10.0.0",
    architecture: "x86",
    bitness: "64",
    wow64: false,
    model: "",
    uaFullVersion: "{major_version}.0.6998.208",
    fullVersionList: [
      {{ brand: "Not:A-Brand", version: "24.0.0.0" }},
      {{ brand: "Chromium", version: "{major_version}.0.6998.208" }}
    ],
    formFactors: ["Desktop"],
    getHighEntropyValues: async function(hints) {{
      return spoofedUserAgentData;
    }}
  }};

  Object.defineProperty(navigator, 'userAgentData', {{
    get: () => spoofedUserAgentData,
    configurable: false,
    enumerable: true
  }});
"""
        return js_code


class CanvasNoiseGenerator:
    """Generates JavaScript to inject noise into canvas operations.

    Uses pure randomization per call to make canvas fingerprinting impossible.
    Each getImageData() call returns random pixels for the area.
    """

    @staticmethod
    def generate(noise: Dict[str, float]) -> str:
        """Generate canvas noise injection JavaScript.

        Args:
            noise: Dictionary with 'r', 'g', 'b', 'a' noise values (range: -1 to 1)

        Returns:
            JavaScript code that wraps canvas getImageData to add noise
        """
        r_noise = noise.get('r', 0.0)
        g_noise = noise.get('g', 0.0)
        b_noise = noise.get('b', 0.0)
        a_noise = noise.get('a', 0.0)

        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // CANVAS FINGERPRINT NOISE INJECTION
  // ═══════════════════════════════════════════════════════

  const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
  CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
    const imageData = originalGetImageData.apply(this, args);

    // Apply aggressive noise: base value + full random noise
    const baseNoise = {{r: {r_noise}, g: {g_noise}, b: {b_noise}, a: {a_noise}}};

    // Add pure random noise to every pixel (full range: 0-255)
    for (let i = 0; i < imageData.data.length; i += 4) {{
      // Random noise: ±255 per channel (completely randomize)
      const rRand = Math.random() * 510 - 255;
      const gRand = Math.random() * 510 - 255;
      const bRand = Math.random() * 510 - 255;
      const aRand = Math.random() * 510 - 255;

      imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + baseNoise.r * 255 + rRand));       // R
      imageData.data[i+1] = Math.max(0, Math.min(255, imageData.data[i+1] + baseNoise.g * 255 + gRand));   // G
      imageData.data[i+2] = Math.max(0, Math.min(255, imageData.data[i+2] + baseNoise.b * 255 + bRand));   // B
      imageData.data[i+3] = Math.max(0, Math.min(255, imageData.data[i+3] + baseNoise.a * 255 + aRand));   // A
    }}

    return imageData;
  }};

  // Also wrap toDataURL and toBlob for completeness
  const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(...args) {{
    return originalToDataURL.apply(this, args);
  }};

  const originalToBlob = HTMLCanvasElement.prototype.toBlob;
  HTMLCanvasElement.prototype.toBlob = function(...args) {{
    return originalToBlob.apply(this, args);
  }};
"""
        return js_code


class WebGLSpoofGenerator:
    """Generates JavaScript to spoof WebGL parameters."""

    @staticmethod
    def generate(gpu: str) -> str:
        """Generate WebGL spoofing JavaScript.

        Args:
            gpu: GPU name to report (e.g., "Ghostline GPU Class 3")

        Returns:
            JavaScript code that overrides WebGL getParameter
        """
        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // WEBGL FINGERPRINT SPOOFING
  // ═══════════════════════════════════════════════════════

  const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(param) {{
    const UNMASKED_VENDOR_WEBGL = 0x9245;
    const UNMASKED_RENDERER_WEBGL = 0x9246;

    if (param === UNMASKED_VENDOR_WEBGL) {{
      return 'Ghostline Technologies';
    }}
    if (param === UNMASKED_RENDERER_WEBGL) {{
      return '{gpu}';
    }}

    return originalGetParameter.apply(this, arguments);
  }};

  // Also handle WebGL2
  if (typeof WebGL2RenderingContext !== 'undefined') {{
    const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function(param) {{
      const UNMASKED_VENDOR_WEBGL = 0x9245;
      const UNMASKED_RENDERER_WEBGL = 0x9246;

      if (param === UNMASKED_VENDOR_WEBGL) {{
        return 'Ghostline Technologies';
      }}
      if (param === UNMASKED_RENDERER_WEBGL) {{
        return '{gpu}';
      }}

      return originalGetParameter2.apply(this, arguments);
    }};
  }}
"""
        return js_code


class APIGateGenerator:
    """Generates JavaScript to block high-entropy APIs based on uniformity settings."""

    @staticmethod
    def generate(gating: Dict[str, bool]) -> str:
        """Generate API gating JavaScript.

        Args:
            gating: Dictionary mapping API names to allowed status
                   (True = allowed, False = blocked)

        Returns:
            JavaScript code that blocks disallowed APIs
        """
        js_parts = ["""
  // ═══════════════════════════════════════════════════════
  // HIGH-ENTROPY API GATING
  // ═══════════════════════════════════════════════════════
"""]

        # Block WebGL if not allowed
        if not gating.get('webgl', True):
            js_parts.append("""
  // Block WebGL
  const originalGetContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
    if (contextType === 'webgl' || contextType === 'webgl2' ||
        contextType === 'experimental-webgl') {
      return null;
    }
    return originalGetContext.apply(this, [contextType, ...args]);
  };
""")

        # Block WebGPU if not allowed
        if not gating.get('webgpu', True):
            js_parts.append("""
  // Block WebGPU
  // navigator.gpu is force-disabled to reduce entropy surface
  const originalWebGPU = navigator.gpu;
  Object.defineProperty(navigator, 'gpu', {
    get: () => undefined,
    configurable: false,
    enumerable: true
  });
  // Preserve property visibility while ensuring callers receive undefined
  if (originalWebGPU !== undefined) {
    navigator.gpu = undefined;
  }
""")

        # Block AudioContext if not allowed
        if not gating.get('audiocontext', True):
            js_parts.append("""
  // Block AudioContext
  window.AudioContext = undefined;
  window.webkitAudioContext = undefined;
""")

        # Block Gamepad API if not allowed
        if not gating.get('gamepad', True):
            js_parts.append("""
  // Block Gamepad API
  Object.defineProperty(navigator, 'getGamepads', {
    get: () => () => [],
    configurable: false,
    enumerable: true
  });

  window.addEventListener('gamepadconnected', (e) => e.stopImmediatePropagation(), true);
  window.addEventListener('gamepaddisconnected', (e) => e.stopImmediatePropagation(), true);
""")

        # Block Battery API if not allowed
        if not gating.get('battery', True):
            js_parts.append("""
  // Block Battery API
  if (navigator.getBattery) {
    navigator.getBattery = function() {
      return Promise.reject(new Error('Battery API is not available'));
    };
  }
""")

        return "".join(js_parts)


class TimerJitterGenerator:
    """Generates JavaScript to reduce timer granularity."""

    @staticmethod
    def generate(granularity_ms: int = 100) -> str:
        """Generate timer jitter JavaScript.

        Args:
            granularity_ms: Timer granularity in milliseconds (default: 100)

        Returns:
            JavaScript code that reduces timer precision
        """
        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // TIMER GRANULARITY REDUCTION
  // ═══════════════════════════════════════════════════════

  const GRANULARITY_MS = {granularity_ms};

  // Date.now()
  const originalDateNow = Date.now;
  Date.now = function() {{
    const now = originalDateNow();
    return Math.floor(now / GRANULARITY_MS) * GRANULARITY_MS;
  }};

  // performance.now()
  const originalPerformanceNow = performance.now;
  performance.now = function() {{
    const now = originalPerformanceNow.call(this);
    return Math.floor(now / GRANULARITY_MS) * GRANULARITY_MS;
  }};

  // Date constructor
  const OriginalDateConstructor = Date;
  Date = new Proxy(OriginalDateConstructor, {{
    construct(target, args) {{
      if (args.length === 0) {{
        const now = originalDateNow();
        const rounded = Math.floor(now / GRANULARITY_MS) * GRANULARITY_MS;
        return new target(rounded);
      }}
      return new target(...args);
    }},
    apply(target, thisArg, args) {{
      if (args.length === 0) {{
        const now = originalDateNow();
        const rounded = Math.floor(now / GRANULARITY_MS) * GRANULARITY_MS;
        return new target(rounded).toString();
      }}
      return new target(...args).toString();
    }}
  }});

  // Copy static methods
  Date.now = originalDateNow;
  Date.parse = OriginalDateConstructor.parse;
  Date.UTC = OriginalDateConstructor.UTC;
"""
        return js_code


class AudioNoiseGenerator:
    """Generates JavaScript to inject noise into AudioContext."""

    @staticmethod
    def generate(noise: float) -> str:
        """Generate audio noise injection JavaScript.

        Args:
            noise: Audio noise value (range: -1 to 1)

        Returns:
            JavaScript code that adds noise to audio analysis
        """
        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // AUDIO FINGERPRINT NOISE INJECTION
  // ═══════════════════════════════════════════════════════

  const audioNoise = {noise};

  // Wrap AnalyserNode methods if AudioContext is available
  if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {{
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;

    const originalCreateAnalyser = AudioContextClass.prototype.createAnalyser;
    AudioContextClass.prototype.createAnalyser = function() {{
      const analyser = originalCreateAnalyser.apply(this, arguments);

      const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
      analyser.getFloatFrequencyData = function(array) {{
        originalGetFloatFrequencyData.apply(this, arguments);
        for (let i = 0; i < array.length; i++) {{
          array[i] += audioNoise * 10;
        }}
      }};

      const originalGetByteFrequencyData = analyser.getByteFrequencyData;
      analyser.getByteFrequencyData = function(array) {{
        originalGetByteFrequencyData.apply(this, arguments);
        for (let i = 0; i < array.length; i++) {{
          array[i] = Math.max(0, Math.min(255, array[i] + audioNoise * 50));
        }}
      }};

      return analyser;
    }};
  }}
"""
        return js_code


class TimezoneSpoofGenerator:
    """Generates JavaScript to spoof timezone to UTC."""

    @staticmethod
    def generate(spoof_enabled: bool = True) -> str:
        """Generate timezone spoofing JavaScript.

        Args:
            spoof_enabled: Whether to spoof timezone to UTC (default: True)

        Returns:
            JavaScript code that overrides timezone-related APIs
        """
        if not spoof_enabled:
            return ""

        js_code = """
  // ═══════════════════════════════════════════════════════
  // TIMEZONE SPOOFING (UTC)
  // ═══════════════════════════════════════════════════════

  // Store original implementations
  const OriginalDate = Date;
  const OriginalIntlDateTimeFormat = Intl.DateTimeFormat;

  // Override Date.prototype.getTimezoneOffset to return 0 (UTC)
  Object.defineProperty(Date.prototype, 'getTimezoneOffset', {
    value: function() {
      return 0;  // UTC has zero offset
    },
    writable: true,
    configurable: true,
    enumerable: false
  });

  // Override Intl.DateTimeFormat to always use UTC
  const OriginalResolvedOptions = OriginalIntlDateTimeFormat.prototype.resolvedOptions;

  Intl.DateTimeFormat = new Proxy(OriginalIntlDateTimeFormat, {
    construct(target, args) {
      const locale = args[0] || 'en-US';
      const options = args[1] || {};

      // Force UTC timezone
      const modifiedOptions = Object.assign({}, options, { timeZone: 'UTC' });

      let instance;
      try {
        instance = Reflect.construct(target, [locale, modifiedOptions]);
      } catch(e) {
        instance = new target(locale, modifiedOptions);
      }

      // Wrap resolvedOptions to ensure UTC is always reported
      if (OriginalResolvedOptions) {
        const wrappedResolvedOptions = function() {
          const result = OriginalResolvedOptions.call(this);
          if (result && typeof result === 'object') {
            result.timeZone = 'UTC';
          }
          return result;
        };

        Object.defineProperty(instance, 'resolvedOptions', {
          value: wrappedResolvedOptions,
          writable: true,
          configurable: true
        });
      }

      return instance;
    }
  });

  // Preserve static methods
  if (OriginalIntlDateTimeFormat.supportedLocalesOf) {
    Intl.DateTimeFormat.supportedLocalesOf = OriginalIntlDateTimeFormat.supportedLocalesOf;
  }
"""
        return js_code


class ScreenDimensionSpoofGenerator:
    """Generates JavaScript to spoof screen dimensions with bucketing."""

    @staticmethod
    def generate(screen_config: Dict[str, int]) -> str:
        """Generate screen dimension spoofing JavaScript.

        Args:
            screen_config: Dictionary with 'width', 'height', 'availWidth', 'availHeight',
                          'colorDepth', 'pixelDepth'

        Returns:
            JavaScript code that overrides screen properties
        """
        width = screen_config.get('width', 1920)
        height = screen_config.get('height', 1080)
        avail_width = screen_config.get('availWidth', width)
        avail_height = screen_config.get('availHeight', height - 40)  # Taskbar
        color_depth = screen_config.get('colorDepth', 24)
        pixel_depth = screen_config.get('pixelDepth', 24)

        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // SCREEN DIMENSION SPOOFING (BUCKETING)
  // ═══════════════════════════════════════════════════════

  Object.defineProperty(screen, 'width', {{
    get: () => {width},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(screen, 'height', {{
    get: () => {height},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(screen, 'availWidth', {{
    get: () => {avail_width},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(screen, 'availHeight', {{
    get: () => {avail_height},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(screen, 'colorDepth', {{
    get: () => {color_depth},
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(screen, 'pixelDepth', {{
    get: () => {pixel_depth},
    configurable: false,
    enumerable: true
  }});

  // Also spoof window.devicePixelRatio
  Object.defineProperty(window, 'devicePixelRatio', {{
    get: () => 1,
    configurable: false,
    enumerable: true
  }});
"""
        return js_code


class LanguageSpoofGenerator:
    """Generates JavaScript to spoof language settings."""

    @staticmethod
    def generate(locale: str = "en-US") -> str:
        """Generate language spoofing JavaScript.

        Args:
            locale: Locale to spoof (e.g., "en-US", "fr-FR")

        Returns:
            JavaScript code that overrides navigator.language and navigator.languages
        """
        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // LANGUAGE/LOCALE SPOOFING
  // ═══════════════════════════════════════════════════════

  Object.defineProperty(navigator, 'language', {{
    get: () => '{locale}',
    configurable: false,
    enumerable: true
  }});

  Object.defineProperty(navigator, 'languages', {{
    get: () => Object.freeze(['{locale}']),
    configurable: false,
    enumerable: true
  }});
"""
        return js_code


class MediaDevicesSpoofGenerator:
    """Generates JavaScript to spoof media devices enumeration."""

    @staticmethod
    def generate(block_enumeration: bool = False) -> str:
        """Generate media devices spoofing JavaScript.

        Args:
            block_enumeration: If True, return empty device list. If False, return generic devices.

        Returns:
            JavaScript code that overrides navigator.mediaDevices.enumerateDevices
        """
        if block_enumeration:
            devices_js = "[]"
        else:
            # Return generic device list
            devices_js = """[
        { deviceId: 'default', kind: 'audioinput', label: '', groupId: 'default' },
        { deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default' },
        { deviceId: 'default', kind: 'videoinput', label: '', groupId: 'default' }
      ]"""

        js_code = f"""
  // ═══════════════════════════════════════════════════════
  // MEDIA DEVICES ENUMERATION PROTECTION
  // ═══════════════════════════════════════════════════════

  if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
    navigator.mediaDevices.enumerateDevices = function() {{
      return Promise.resolve({devices_js});
    }};
  }}
"""
        return js_code


class FingerprintInjector:
    """Main orchestrator for generating anti-fingerprinting JavaScript."""

    def __init__(self, dashboard: PrivacyDashboard, container: str) -> None:
        """Initialize the fingerprint injector.

        Args:
            dashboard: PrivacyDashboard instance with all privacy subsystems
            container: Container name to generate protections for
        """
        self.dashboard = dashboard
        self.container = container

    def generate_script(self, origin: str) -> str:
        """Generate complete anti-fingerprinting JavaScript for an origin.

        Args:
            origin: Origin URL (e.g., "https://example.com")

        Returns:
            Complete JavaScript code to inject
        """
        # Get configuration from dashboard
        config = self._get_config()

        device = config['device']
        noise = config['noise']
        gating = config['gating']
        user_agent = config['user_agent']
        platform = config.get('platform', 'Linux')
        locale = config.get('locale', 'en-US')
        screen_config = config.get('screen', {})

        # Generate header
        preset = self.dashboard.uniformity_manager.profile_for(self.container).name

        script_parts = [
            "(function() {",
            "  'use strict';",
            "",
            "  // ═══════════════════════════════════════════════════════",
            "  // GHOSTLINE BROWSER ANTI-FINGERPRINTING PROTECTION",
            f"  // Container: {self.container} | Preset: {preset} | Origin: {origin}",
            "  // ═══════════════════════════════════════════════════════",
            ""
        ]

        # Add all protection modules
        script_parts.append(NavigatorSpoofGenerator.generate(device, user_agent))
        script_parts.append(UserAgentDataSpoofGenerator.generate(platform))
        script_parts.append(PluginsAndMimeTypesSpoofGenerator.generate())
        script_parts.append(LanguageSpoofGenerator.generate(locale))
        script_parts.append(ScreenDimensionSpoofGenerator.generate(screen_config))
        script_parts.append(TimezoneSpoofGenerator.generate(spoof_enabled=True))
        script_parts.append(CanvasNoiseGenerator.generate(noise['canvas']))
        script_parts.append(WebGLSpoofGenerator.generate(str(device.get('gpu', 'Ghostline GPU'))))
        script_parts.append(APIGateGenerator.generate(gating))
        script_parts.append(TimerJitterGenerator.generate(100))
        script_parts.append(AudioNoiseGenerator.generate(noise['audio']))

        # Media devices protection (strict mode blocks enumeration, balanced returns generic)
        strict_mode = self.dashboard.uniformity_manager.profile_for(self.container).strict_mode
        script_parts.append(MediaDevicesSpoofGenerator.generate(block_enumeration=strict_mode))

        # Add footer
        script_parts.extend([
            "",
            "  console.log('[Ghostline] Anti-fingerprinting protection active');",
            "  console.log('[Ghostline] Platform:', navigator.platform);",
            f"  console.log('[Ghostline] Preset: {preset}');",
            "})();"
        ])

        return "\n".join(script_parts)

    def _get_config(self) -> Dict[str, Any]:
        """Get injection configuration from dashboard.

        Returns:
            Dictionary with device, noise, gating, user_agent, locale, and screen
        """
        from ghostline.privacy.rfp import unified_user_agent

        origin = self.dashboard._container_origins.get(self.container, "about:blank")
        device = self.dashboard._last_device_class.get(self.container, {
            'platform': 'Linux',
            'memory_gb': 8,
            'gpu': 'Ghostline GPU Class 1'
        })
        noise = self.dashboard.calibrated_noise_for(self.container)
        gating = self.dashboard.gating_snapshot(self.container)

        # Get locale from container config (default to en-US)
        locale = self.dashboard._container_locales.get(self.container, "en-US")

        # Get screen dimensions from device randomizer
        screen_config = self.dashboard.screen_dimensions_for(self.container)

        platform = str(device.get('platform', 'Linux'))
        user_agent = unified_user_agent(platform=platform + " x86_64")

        return {
            'device': device,
            'noise': noise,
            'gating': gating,
            'origin': origin,
            'user_agent': user_agent,
            'platform': platform,
            'locale': locale,
            'screen': screen_config,
        }


__all__ = [
    'FingerprintInjector',
    'NavigatorSpoofGenerator',
    'UserAgentDataSpoofGenerator',
    'PluginsAndMimeTypesSpoofGenerator',
    'CanvasNoiseGenerator',
    'WebGLSpoofGenerator',
    'APIGateGenerator',
    'TimerJitterGenerator',
    'AudioNoiseGenerator',
    'TimezoneSpoofGenerator',
    'ScreenDimensionSpoofGenerator',
    'LanguageSpoofGenerator',
    'MediaDevicesSpoofGenerator',
]
