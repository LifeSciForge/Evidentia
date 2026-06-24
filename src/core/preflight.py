"""Pre-flight checks that run before the heavy import chain.

This module deliberately does NOT import src.core.settings (which constructs a
Settings object at import time and would crash on missing keys). It only reads
the environment, so it is safe to import first and produce a friendly message.
"""
import os
from pathlib import Path
from typing import Optional, Mapping, List, Union

REQUIRED_SECRETS = ("ANTHROPIC_API_KEY", "TAVILY_API_KEY")


def missing_required_secrets(env: Optional[Mapping[str, str]] = None) -> List[str]:
    """Return the names of required secrets that are absent or empty."""
    env = os.environ if env is None else env
    return [name for name in REQUIRED_SECRETS if not env.get(name)]


def load_dotenv_into_environ(path: Union[str, Path]) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ for local runs.

    Dependency-free. Does NOT override variables already set in the environment
    (so Streamlit Cloud's injected secrets always win). No-op if the file is
    absent — which is the case on Streamlit Cloud, where there is no .env.
    """
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
