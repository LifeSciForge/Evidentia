from src.schema.gtm_state import Source, SourcedValue, unavailable, web_source, verified_source, modeled, GTMState


def test_unavailable_has_no_url_and_unavailable_tier():
    s = unavailable("No public figure")
    assert s.tier == "unavailable"
    assert s.url is None


def test_web_source_keeps_real_url_and_domain_label():
    s = web_source("https://www.drugs.com/price-guide/lumakras")
    assert s.tier == "web"
    assert s.url == "https://www.drugs.com/price-guide/lumakras"
    assert "drugs.com" in s.label


def test_verified_source_sets_verified_tier():
    s = verified_source("ClinicalTrials.gov", "https://clinicaltrials.gov/study/NCT04685135")
    assert s.tier == "verified"
    assert s.url.endswith("NCT04685135")


def test_modeled_carries_inputs_and_no_url():
    patients = SourcedValue(value=13000, display="~13,000", source=verified_source("SEER", "https://seer.cancer.gov"))
    sv = modeled(value=1_600_000_000, display="$1.2–1.8B", inputs=[patients])
    assert sv.source.tier == "modeled"
    assert sv.source.url is None
    assert sv.modeled_from and sv.modeled_from[0].value == 13000


def test_gtmstate_has_sources_map_default_empty():
    st = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
    assert st.sources == {}
