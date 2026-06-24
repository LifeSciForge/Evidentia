from src.ui.components import source_chip_html, metric_card_html


def test_verified_tier_renders_link_with_label_and_class():
    html = source_chip_html("verified", "ClinicalTrials.gov", url="https://clinicaltrials.gov/study/NCT04685135")
    assert "ev-chip-verified" in html
    assert "ClinicalTrials.gov" in html
    assert 'href="https://clinicaltrials.gov/study/NCT04685135"' in html
    assert "<a " in html  # has url -> anchor


def test_unavailable_tier_renders_span_without_link():
    html = source_chip_html("unavailable", "Unavailable")
    assert "ev-chip-unavailable" in html
    assert "<a " not in html  # no url -> span, not a link


def test_label_is_html_escaped():
    html = source_chip_html("web", '<script>alert(1)</script>', url="https://x.test")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_unknown_tier_falls_back_to_unavailable_class():
    html = source_chip_html("bogus", "X")
    assert "ev-chip-unavailable" in html


def test_metric_card_shows_label_value_and_no_gradient():
    html = metric_card_html("Addressable patients", "~13,000")
    assert "Addressable patients" in html
    assert "~13,000" in html
    assert "linear-gradient" not in html  # retired the purple gradient
    assert "ev-metric-card" in html


def test_metric_card_embeds_optional_source_chip():
    chip = source_chip_html("verified", "SEER/NCI", url="https://seer.cancer.gov")
    html = metric_card_html("Addressable patients", "~13,000", source_html=chip)
    assert "ev-chip-verified" in html
    assert "SEER/NCI" in html
