from src.core.preflight import missing_required_secrets


def test_all_missing_returns_both():
    assert missing_required_secrets({}) == ["ANTHROPIC_API_KEY", "TAVILY_API_KEY"]


def test_none_missing_returns_empty():
    assert missing_required_secrets(
        {"ANTHROPIC_API_KEY": "x", "TAVILY_API_KEY": "y"}
    ) == []


def test_partial_missing_returns_only_missing():
    assert missing_required_secrets({"ANTHROPIC_API_KEY": "x"}) == ["TAVILY_API_KEY"]


def test_empty_string_counts_as_missing():
    assert missing_required_secrets(
        {"ANTHROPIC_API_KEY": "", "TAVILY_API_KEY": "y"}
    ) == ["ANTHROPIC_API_KEY"]
