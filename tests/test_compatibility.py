from ghostline.privacy.compatibility import CompatibilityAdvisory, StreamingCompatibilityAdvisor


def test_netflix_advisory_matches_domains_and_subdomains():
    advisor = StreamingCompatibilityAdvisor()
    advisory = advisor.advisory_for("https://www.netflix.com/watch/123")
    assert advisory is not None
    assert advisory.error_code == "M7701-1003"
    assert "Widevine" in advisory.symptom

    subdomain_advisory = advisor.advisory_for("assets.netflix.com")
    assert subdomain_advisory == advisory


def test_custom_advisories_can_be_injected():
    advisory = CompatibilityAdvisory(
        host="drm.example", error_code="X1", symptom="Missing EME", remediation="enable it"
    )
    advisor = StreamingCompatibilityAdvisor([advisory])
    assert advisor.advisory_for("drm.example") == advisory
    assert advisor.advisory_for("unknown.test") is None
