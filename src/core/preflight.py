"""Pre-flight checks that run before the heavy import chain.

This module deliberately does NOT import src.core.settings (which constructs a
Settings object at import time and would crash on missing keys). It only reads
the environment, so it is safe to import first and produce a friendly message.
"""
import os
from typing import Optional, Mapping, List

REQUIRED_SECRETS = ("ANTHROPIC_API_KEY", "TAVILY_API_KEY")


def missing_required_secrets(env: Optional[Mapping[str, str]] = None) -> List[str]:
    """Return the names of required secrets that are absent or empty."""
    env = os.environ if env is None else env
    return [name for name in REQUIRED_SECRETS if not env.get(name)]
