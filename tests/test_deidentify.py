from src.service.security.deidentify import deidentify


def test_strips_age_phrases():
    assert "[AGE]" in deidentify("a 67 year-old male")
    assert "67" not in deidentify("a 67 year-old male")


def test_strips_mrn_ssn_phone_email():
    out = deidentify("MRN: 12345678, SSN 123-45-6789, call 415-555-1212 or a@b.com")
    assert "12345678" not in out and "123-45-6789" not in out
    assert "415-555-1212" not in out and "a@b.com" not in out


def test_strips_patient_name_phrase_only():
    out = deidentify("patient John Smith presented with dyspnea")
    assert "John Smith" not in out
    assert "[NAME]" in out


def test_preserves_kol_and_drug_names():
    text = "Dr. Roy Herbst discussed sotorasib for KRAS G12C NSCLC"
    out = deidentify(text)
    assert "Roy Herbst" in out
    assert "sotorasib" in out
    assert "KRAS G12C NSCLC" in out


def test_empty_and_none_safe():
    assert deidentify("") == ""
    assert deidentify(None) == ""
