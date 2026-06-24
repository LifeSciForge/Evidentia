"""Import smoke-test.

This imports the exact chain that broke twice in production (missing wheel,
missing import). conftest.py has already set dummy secrets, so Settings()
constructs cleanly. We do NOT import streamlit_app (it would start Streamlit);
we import the workflow factory, which pulls settings, tools, and all agents.
"""


def test_workflow_chain_imports():
    from src.agents.gtm_workflow import create_gtm_workflow

    assert callable(create_gtm_workflow)


def test_settings_constructs_with_keys():
    from src.core.settings import settings

    assert settings.ANTHROPIC_API_KEY  # set to dummy by conftest
