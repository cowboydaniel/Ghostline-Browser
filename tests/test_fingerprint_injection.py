"""Tests for anti-fingerprinting JavaScript injection."""
import pytest

from ghostline.privacy.injector import (
    APIGateGenerator,
    AudioNoiseGenerator,
    CanvasNoiseGenerator,
    FingerprintInjector,
    LanguageSpoofGenerator,
    MediaDevicesSpoofGenerator,
    NavigatorSpoofGenerator,
    ScreenDimensionSpoofGenerator,
    TimerJitterGenerator,
    TimezoneSpoofGenerator,
    WebGLSpoofGenerator,
)
from ghostline.ui.dashboard import PrivacyDashboard


def test_navigator_spoof_generator_produces_valid_javascript():
    """Test that NavigatorSpoofGenerator creates valid JS with correct values."""
    device = {
        'platform': 'Windows',
        'memory_gb': 16,
        'gpu': 'Ghostline GPU Class 4'
    }
    user_agent = 'Mozilla/5.0 (Windows x86_64) Ghostline/1.0'

    js_code = NavigatorSpoofGenerator.generate(device, user_agent)

    assert 'navigator' in js_code
    assert 'platform' in js_code
    assert 'Windows x86_64' in js_code
    assert 'hardwareConcurrency' in js_code
    assert '16' in js_code  # cores for 16GB memory
    assert 'deviceMemory' in js_code
    assert 'Object.defineProperty' in js_code
    assert 'configurable: false' in js_code
    assert user_agent in js_code


def test_navigator_spoof_cores_scale_with_memory():
    """Test that hardware concurrency scales with memory."""
    low_mem_device = {'platform': 'Linux', 'memory_gb': 4, 'gpu': 'GPU'}
    mid_mem_device = {'platform': 'Linux', 'memory_gb': 8, 'gpu': 'GPU'}
    high_mem_device = {'platform': 'Linux', 'memory_gb': 16, 'gpu': 'GPU'}

    low_js = NavigatorSpoofGenerator.generate(low_mem_device, 'UA')
    mid_js = NavigatorSpoofGenerator.generate(mid_mem_device, 'UA')
    high_js = NavigatorSpoofGenerator.generate(high_mem_device, 'UA')

    # Low memory should get 4 cores
    assert 'hardwareConcurrency' in low_js
    assert '4' in low_js

    # Mid memory should get 8 cores
    assert 'hardwareConcurrency' in mid_js
    assert '8' in mid_js

    # High memory should get 16 cores
    assert 'hardwareConcurrency' in high_js
    assert '16' in high_js


def test_canvas_noise_generator_produces_valid_javascript():
    """Test that CanvasNoiseGenerator creates valid JS with noise values."""
    noise = {'r': 0.15, 'g': -0.08, 'b': 0.12, 'a': 0.03}

    js_code = CanvasNoiseGenerator.generate(noise)

    assert 'CanvasRenderingContext2D' in js_code
    assert 'getImageData' in js_code
    assert 'originalGetImageData' in js_code
    assert 'imageData.data' in js_code
    assert '0.15' in js_code
    assert '-0.08' in js_code
    assert '0.12' in js_code
    assert '0.03' in js_code
    assert 'Math.max' in js_code  # Clamping
    assert 'Math.min' in js_code


def test_webgl_spoof_generator_produces_valid_javascript():
    """Test that WebGLSpoofGenerator creates valid JS with GPU name."""
    gpu = 'Ghostline GPU Class 3'

    js_code = WebGLSpoofGenerator.generate(gpu)

    assert 'WebGLRenderingContext' in js_code
    assert 'getParameter' in js_code
    assert 'UNMASKED_VENDOR_WEBGL' in js_code
    assert 'UNMASKED_RENDERER_WEBGL' in js_code
    assert '0x9245' in js_code
    assert '0x9246' in js_code
    assert 'Ghostline Technologies' in js_code
    assert gpu in js_code
    assert 'WebGL2RenderingContext' in js_code  # Also handles WebGL2


def test_api_gate_generator_blocks_webgpu_when_disabled():
    """Test that APIGateGenerator blocks WebGPU when gating is False."""
    gating = {
        'webgl': True,
        'webgpu': False,  # Blocked
        'audiocontext': True,
        'gamepad': True
    }

    js_code = APIGateGenerator.generate(gating)

    assert 'navigator.gpu' in js_code
    assert 'undefined' in js_code
    # Should not block WebGL since it's allowed
    assert 'webgl' not in js_code.lower() or 'WebGL' not in js_code


def test_api_gate_generator_blocks_webgl_when_disabled():
    """Test that APIGateGenerator blocks WebGL when gating is False."""
    gating = {
        'webgl': False,  # Blocked
        'webgpu': True,
        'audiocontext': True,
        'gamepad': True
    }

    js_code = APIGateGenerator.generate(gating)

    assert 'getContext' in js_code
    assert 'webgl' in js_code
    assert 'return null' in js_code


def test_api_gate_generator_blocks_audiocontext_when_disabled():
    """Test that APIGateGenerator blocks AudioContext when gating is False."""
    gating = {
        'webgl': True,
        'webgpu': True,
        'audiocontext': False,  # Blocked
        'gamepad': True
    }

    js_code = APIGateGenerator.generate(gating)

    assert 'AudioContext' in js_code
    assert 'undefined' in js_code
    assert 'webkitAudioContext' in js_code


def test_api_gate_generator_blocks_gamepad_when_disabled():
    """Test that APIGateGenerator blocks Gamepad API when gating is False."""
    gating = {
        'webgl': True,
        'webgpu': True,
        'audiocontext': True,
        'gamepad': False  # Blocked
    }

    js_code = APIGateGenerator.generate(gating)

    assert 'getGamepads' in js_code
    assert '[]' in js_code  # Returns empty array
    assert 'gamepadconnected' in js_code


def test_api_gate_generator_allows_all_when_all_enabled():
    """Test that APIGateGenerator doesn't add blocking code when all APIs are allowed."""
    gating = {
        'webgl': True,
        'webgpu': True,
        'audiocontext': True,
        'gamepad': True
    }

    js_code = APIGateGenerator.generate(gating)

    # Should only have the header comment, no actual blocking code
    assert 'HIGH-ENTROPY API GATING' in js_code
    # Should be very short (just header)
    assert len(js_code) < 200


def test_timer_jitter_generator_produces_valid_javascript():
    """Test that TimerJitterGenerator creates valid JS with granularity."""
    js_code = TimerJitterGenerator.generate(100)

    assert 'Date.now' in js_code
    assert 'performance.now' in js_code
    assert 'GRANULARITY_MS' in js_code
    assert '100' in js_code
    assert 'Math.floor' in js_code
    assert 'originalDateNow' in js_code
    assert 'originalPerformanceNow' in js_code
    assert 'Proxy' in js_code  # Uses Proxy for Date constructor


def test_audio_noise_generator_produces_valid_javascript():
    """Test that AudioNoiseGenerator creates valid JS with noise value."""
    noise = 0.05

    js_code = AudioNoiseGenerator.generate(noise)

    assert 'AudioContext' in js_code
    assert 'createAnalyser' in js_code
    assert 'getFloatFrequencyData' in js_code
    assert 'getByteFrequencyData' in js_code
    assert '0.05' in js_code
    assert 'audioNoise' in js_code


def test_fingerprint_injector_integration():
    """Test that FingerprintInjector integrates all generators correctly."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")
    dashboard.record_navigation("test", "https://example.com")

    injector = FingerprintInjector(dashboard, "test")
    script = injector.generate_script("https://example.com")

    # Verify all components are present
    assert 'GHOSTLINE BROWSER ANTI-FINGERPRINTING PROTECTION' in script
    assert 'Container: test' in script
    assert 'https://example.com' in script

    # Navigator spoofing
    assert 'navigator.platform' in script

    # Canvas noise
    assert 'CanvasRenderingContext2D' in script
    assert 'getImageData' in script

    # WebGL spoofing
    assert 'WebGLRenderingContext' in script
    assert 'UNMASKED_RENDERER_WEBGL' in script

    # API gating (research template uses strict mode)
    assert 'navigator.gpu' in script or 'HIGH-ENTROPY API GATING' in script

    # Timer jitter
    assert 'Date.now' in script

    # Audio noise
    assert 'createAnalyser' in script or 'AudioContext' in script

    # Footer
    assert "console.log('[Ghostline] Anti-fingerprinting protection active')" in script

    # Wrapped in IIFE
    assert script.startswith('(function()')
    assert script.endswith(');')


def test_fingerprint_injector_uses_container_settings():
    """Test that FingerprintInjector respects container-specific settings."""
    dashboard = PrivacyDashboard()

    # Create strict container (blocks more APIs)
    dashboard.ensure_container("strict", template="research")
    dashboard.record_navigation("strict", "https://strict.example.com")

    # Create balanced container (allows more APIs)
    dashboard.ensure_container("balanced", template="shopping")
    dashboard.record_navigation("balanced", "https://balanced.example.com")

    strict_injector = FingerprintInjector(dashboard, "strict")
    balanced_injector = FingerprintInjector(dashboard, "balanced")

    strict_script = strict_injector.generate_script("https://strict.example.com")
    balanced_script = balanced_injector.generate_script("https://balanced.example.com")

    # Both should have basic protections
    assert 'navigator.platform' in strict_script
    assert 'navigator.platform' in balanced_script

    # Strict mode should mention 'strict' preset
    assert 'strict' in strict_script

    # Balanced mode should mention 'balanced' preset
    assert 'balanced' in balanced_script


def test_fingerprint_injector_deterministic_per_origin():
    """Test that same origin gets same fingerprint values."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")

    injector = FingerprintInjector(dashboard, "test")

    # Generate script for same origin twice
    dashboard.record_navigation("test", "https://example.com")
    script1 = injector.generate_script("https://example.com")

    dashboard.record_navigation("test", "https://example.com")
    script2 = injector.generate_script("https://example.com")

    # Should be identical (deterministic)
    assert script1 == script2


def test_fingerprint_injector_different_per_origin():
    """Test that different origins get different fingerprint values."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")

    injector = FingerprintInjector(dashboard, "test")

    # Generate script for different origins
    dashboard.record_navigation("test", "https://example.com")
    script1 = injector.generate_script("https://example.com")

    dashboard.record_navigation("test", "https://different.com")
    script2 = injector.generate_script("https://different.com")

    # Should be different (different noise values)
    assert script1 != script2

    # But both should have the structure
    assert 'GHOSTLINE BROWSER' in script1
    assert 'GHOSTLINE BROWSER' in script2


def test_fingerprint_injector_updates_device_class_on_navigation():
    """Test that device class is randomized on navigation."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")

    injector = FingerprintInjector(dashboard, "test")

    # First navigation
    dashboard.record_navigation("test", "https://first.com")
    script1 = injector.generate_script("https://first.com")

    # Second navigation to different domain
    dashboard.record_navigation("test", "https://second.com")
    script2 = injector.generate_script("https://second.com")

    # Both should have navigator spoofing
    assert 'navigator.platform' in script1
    assert 'navigator.platform' in script2

    # Platform values might differ (randomized per origin)
    # At minimum, the origin in the comment should differ
    assert 'https://first.com' in script1
    assert 'https://second.com' in script2


def test_generated_javascript_is_syntactically_valid():
    """Test that generated JavaScript doesn't have obvious syntax errors."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")
    dashboard.record_navigation("test", "https://example.com")

    injector = FingerprintInjector(dashboard, "test")
    script = injector.generate_script("https://example.com")

    # Basic syntax checks
    assert script.count('(function()') == 1
    assert script.count('})();') == 1

    # Check for balanced braces
    assert script.count('{') == script.count('}')

    # Check for balanced parentheses (rough check)
    open_parens = script.count('(')
    close_parens = script.count(')')
    assert open_parens == close_parens

    # No obvious syntax errors
    assert 'undefined undefined' not in script
    assert 'function function' not in script
    assert ';;' not in script  # Double semicolons


def test_injector_handles_missing_device_gracefully():
    """Test that injector works even if device class not set."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")
    # Don't call record_navigation, so device class won't be set

    injector = FingerprintInjector(dashboard, "test")
    script = injector.generate_script("about:blank")

    # Should still generate valid script with defaults
    assert 'GHOSTLINE BROWSER' in script
    assert 'navigator.platform' in script
    assert 'Linux' in script or 'Windows' in script or 'macOS' in script


def test_injector_logs_protection_details():
    """Test that injector includes debug information in console logs."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="balanced")
    dashboard.record_navigation("test", "https://example.com")

    injector = FingerprintInjector(dashboard, "test")
    script = injector.generate_script("https://example.com")

    # Should have console.log statements for debugging
    assert "console.log('[Ghostline] Anti-fingerprinting protection active')" in script
    assert "console.log('[Ghostline] Platform:" in script
    assert "console.log('[Ghostline] Preset:" in script
    assert 'balanced' in script  # Preset name


def test_timezone_spoof_generator_produces_valid_javascript():
    """Test that TimezoneSpoofGenerator creates valid JS to spoof timezone."""
    js_code = TimezoneSpoofGenerator.generate(spoof_enabled=True)

    assert 'getTimezoneOffset' in js_code
    assert 'return 0' in js_code  # Should return 0 for UTC
    assert 'Intl.DateTimeFormat' in js_code
    assert "timeZone: 'UTC'" in js_code
    assert 'OriginalDate' in js_code
    assert 'Object.defineProperty' in js_code


def test_timezone_spoof_generator_can_be_disabled():
    """Test that timezone spoofing can be disabled."""
    js_code = TimezoneSpoofGenerator.generate(spoof_enabled=False)

    assert js_code == ""  # Should return empty string when disabled


def test_screen_dimension_spoof_generator_produces_valid_javascript():
    """Test that ScreenDimensionSpoofGenerator creates valid JS with screen dimensions."""
    screen_config = {
        'width': 1920,
        'height': 1080,
        'availWidth': 1920,
        'availHeight': 1040,
        'colorDepth': 24,
        'pixelDepth': 24
    }

    js_code = ScreenDimensionSpoofGenerator.generate(screen_config)

    assert 'screen' in js_code
    assert 'width' in js_code
    assert '1920' in js_code
    assert 'height' in js_code
    assert '1080' in js_code
    assert 'availHeight' in js_code
    assert '1040' in js_code
    assert 'colorDepth' in js_code
    assert 'pixelDepth' in js_code
    assert 'devicePixelRatio' in js_code
    assert 'Object.defineProperty' in js_code


def test_screen_dimension_spoof_generator_uses_defaults():
    """Test that ScreenDimensionSpoofGenerator uses defaults when config is empty."""
    screen_config = {}

    js_code = ScreenDimensionSpoofGenerator.generate(screen_config)

    # Should use default 1920x1080
    assert '1920' in js_code
    assert '1080' in js_code
    assert 'devicePixelRatio' in js_code


def test_language_spoof_generator_produces_valid_javascript():
    """Test that LanguageSpoofGenerator creates valid JS with language settings."""
    js_code = LanguageSpoofGenerator.generate(locale="fr-FR")

    assert 'navigator' in js_code
    assert 'language' in js_code
    assert 'languages' in js_code
    assert 'fr-FR' in js_code
    assert 'Object.freeze' in js_code  # Languages array should be frozen
    assert 'Object.defineProperty' in js_code


def test_language_spoof_generator_defaults_to_en_us():
    """Test that LanguageSpoofGenerator defaults to en-US."""
    js_code = LanguageSpoofGenerator.generate()

    assert 'en-US' in js_code


def test_media_devices_spoof_generator_blocks_enumeration():
    """Test that MediaDevicesSpoofGenerator blocks device enumeration in strict mode."""
    js_code = MediaDevicesSpoofGenerator.generate(block_enumeration=True)

    assert 'mediaDevices' in js_code
    assert 'enumerateDevices' in js_code
    assert '[]' in js_code  # Should return empty array
    assert 'Promise.resolve' in js_code


def test_media_devices_spoof_generator_returns_generic_devices():
    """Test that MediaDevicesSpoofGenerator returns generic devices in balanced mode."""
    js_code = MediaDevicesSpoofGenerator.generate(block_enumeration=False)

    assert 'mediaDevices' in js_code
    assert 'enumerateDevices' in js_code
    assert 'audioinput' in js_code
    assert 'audiooutput' in js_code
    assert 'videoinput' in js_code
    assert 'default' in js_code  # Generic device IDs


def test_api_gate_generator_blocks_battery_when_disabled():
    """Test that APIGateGenerator blocks Battery API when gating is False."""
    gating = {'battery': False}

    js_code = APIGateGenerator.generate(gating)

    assert 'Battery API' in js_code or 'battery' in js_code.lower()
    assert 'getBattery' in js_code
    assert 'Promise.reject' in js_code


def test_device_randomizer_screen_dimensions():
    """Test that DeviceRandomizer generates screen dimensions."""
    from ghostline.privacy.entropy import DeviceRandomizer

    randomizer = DeviceRandomizer()
    screen1 = randomizer.screen_dimensions(window_id=1)
    screen2 = randomizer.screen_dimensions(window_id=1)
    screen3 = randomizer.screen_dimensions(window_id=100)

    # Same window ID should get same dimensions
    assert screen1 == screen2

    # Different buckets might get different dimensions (not guaranteed, but likely)
    assert 'width' in screen1
    assert 'height' in screen1
    assert 'availWidth' in screen1
    assert 'availHeight' in screen1
    assert 'colorDepth' in screen1
    assert 'pixelDepth' in screen1

    # Dimensions should be from common buckets
    assert screen1['width'] in [1920, 1366, 1440, 1536, 2560]


def test_injector_includes_new_protections():
    """Test that FingerprintInjector includes all new protections."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="strict")
    dashboard.record_navigation("test", "https://example.com")

    injector = FingerprintInjector(dashboard, "test")
    script = injector.generate_script("https://example.com")

    # Should include timezone protection
    assert 'TIMEZONE SPOOFING' in script or 'getTimezoneOffset' in script

    # Should include screen dimension protection
    assert 'SCREEN DIMENSION' in script or 'screen.width' in script

    # Should include language protection
    assert 'LANGUAGE' in script or 'navigator.language' in script

    # Should include media devices protection
    assert 'MEDIA DEVICES' in script or 'mediaDevices' in script


def test_dashboard_provides_screen_dimensions():
    """Test that PrivacyDashboard provides screen dimensions for containers."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test", template="research")
    dashboard.record_navigation("test", "https://example.com")

    screen = dashboard.screen_dimensions_for("test")

    assert 'width' in screen
    assert 'height' in screen
    assert screen['width'] > 0
    assert screen['height'] > 0


def test_dashboard_stores_container_locales():
    """Test that PrivacyDashboard stores locale for each container."""
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("test1", template="research", locale="en-US")
    dashboard.ensure_container("test2", template="shopping", locale="fr-FR")

    assert dashboard._container_locales.get("test1") == "en-US"
    assert dashboard._container_locales.get("test2") == "fr-FR"
