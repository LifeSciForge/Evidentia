import os
from src.core.preflight import missing_required_secrets, load_dotenv_into_environ


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


def test_load_dotenv_loads_keys_and_respects_existing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        '# comment line\n'
        'ANTHROPIC_API_KEY="from-dotenv"\n'
        'TAVILY_API_KEY=tavily-val\n'
        'ALREADY_SET=should-not-override\n'
        '\n'
        'MALFORMED_LINE_NO_EQUALS\n'
    )
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setenv("ALREADY_SET", "real-env-wins")

    load_dotenv_into_environ(env_file)

    assert os.environ["ANTHROPIC_API_KEY"] == "from-dotenv"   # quotes stripped
    assert os.environ["TAVILY_API_KEY"] == "tavily-val"
    assert os.environ["ALREADY_SET"] == "real-env-wins"        # not overridden
    assert missing_required_secrets(os.environ) == []          # both now present


def test_load_dotenv_missing_file_is_noop(tmp_path):
    load_dotenv_into_environ(tmp_path / "does-not-exist.env")  # must not raise
