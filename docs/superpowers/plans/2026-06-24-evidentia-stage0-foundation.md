# Evidentia Stage 0 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a test harness, CI, and graceful config-failure handling so every later stage is built behind a safety net — and so the two recent production outages (a missing wheel, a missing import) can never ship silently again.

**Architecture:** A `tests/` suite (pytest + pytest-asyncio) with dummy env keys set in `conftest.py` so the settings-dependent import chain loads without real secrets. A pure `preflight` helper checks for required secrets and is called by `streamlit_app.py` *before* the heavy import chain, replacing the white-screen crash with a clear message. A GitHub Actions workflow installs the slim requirements on Python 3.13 + 3.14, runs an import smoke-test, and runs pytest.

**Tech Stack:** Python, pytest, pytest-asyncio, GitHub Actions, Streamlit, Pydantic Settings.

---

## File Structure

- Create `requirements-dev.txt` — test-only dependencies (kept out of the production `requirements.txt` Streamlit Cloud installs).
- Create `pytest.ini` — pytest config (asyncio mode, test paths).
- Create `tests/conftest.py` — sets dummy env secrets at collection time; shared `demo_state` fixture.
- Create `tests/test_preflight.py` — unit tests for the secrets check.
- Create `tests/test_imports.py` — import smoke-test for the workflow chain.
- Create `src/core/preflight.py` — pure secrets-check helper (no Settings construction, safe to import early).
- Modify `streamlit_app.py` — call preflight before importing `ui.app`; show a friendly message + `st.stop()` if secrets are missing.
- Create `.github/workflows/ci.yml` — CI matrix (Py 3.13 + 3.14): install, smoke-test, pytest.

---

## Task 1: Test harness scaffolding

**Files:**
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the dev dependencies file**

Create `requirements-dev.txt`:

```
# Test-only dependencies. NOT installed on Streamlit Cloud (production uses requirements.txt).
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 2: Create the pytest config**

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 3: Create conftest with dummy env + shared fixture**

Create `tests/conftest.py`:

```python
"""Shared test fixtures.

Dummy secrets are set at import time so any module that constructs Settings
(src.core.settings) imports cleanly without real API keys. Tests never use
live keys and never make live API/LLM calls.
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

import pytest
from src.schema.gtm_state import GTMState


@pytest.fixture
def demo_state():
    """Standard working demo case used across the suite."""
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
```

- [ ] **Step 4: Install dev deps and confirm pytest collects cleanly**

Run: `pip install -r requirements-dev.txt && pytest -q`
Expected: pytest runs and reports `no tests ran` (exit code 5) — the harness works; tests come next.

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt pytest.ini tests/conftest.py
git commit -m "test: add pytest harness, dev deps, and demo_state fixture"
```

---

## Task 2: Preflight secrets check (graceful config failure)

**Files:**
- Create: `tests/test_preflight.py`
- Create: `src/core/preflight.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_preflight.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_preflight.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.preflight'`

- [ ] **Step 3: Write minimal implementation**

Create `src/core/preflight.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_preflight.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/test_preflight.py src/core/preflight.py
git commit -m "feat: add preflight required-secrets check"
```

---

## Task 3: Wire preflight into the entrypoint

**Files:**
- Modify: `streamlit_app.py`

- [ ] **Step 1: Add the preflight guard before the heavy import**

In `streamlit_app.py`, the current top adds `src` to `sys.path` then does `from ui.app import main`. Insert the guard *between* the `sys.path` line and the `from ui.app import main` line. After editing, the top of the file reads:

```python
"""
Evidentia - MSL Intelligence Platform
Entry point for Streamlit Cloud deployment
"""

import os
import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from src.core.preflight import missing_required_secrets

# Pre-flight: fail clearly (not a white-screen crash) if required secrets are absent.
_missing = missing_required_secrets(os.environ)
if _missing:
    st.set_page_config(page_title="Evidentia — Configuration needed", page_icon="🏥")
    st.error("⚠️ Evidentia isn't configured yet.")
    st.markdown(
        "Missing required secret(s): **"
        + ", ".join(_missing)
        + "**.\n\nAdd them in Streamlit Cloud → **Manage app → Settings → Secrets** "
        "(flat, top-level keys), then reboot."
    )
    st.stop()

# Run the main app
from ui.app import main
```

Leave the existing CSS `st.markdown(...)` block and the `if __name__ == "__main__": main()` block below unchanged.

- [ ] **Step 2: Verify the import chain still loads with secrets present**

Run: `pytest tests/test_preflight.py -v`
Expected: PASS (unchanged — this step is a manual edit; the smoke test in Task 4 covers the chain).

- [ ] **Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: friendly config-error screen instead of white-screen crash"
```

---

## Task 4: Import smoke-test for the workflow chain

**Files:**
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_imports.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes (chain currently imports)**

Run: `pytest tests/test_imports.py -v`
Expected: PASS (2 passed). If it FAILS, the import chain is broken — fix the underlying import before continuing; that is exactly the regression this test exists to catch.

- [ ] **Step 3: Run the whole suite**

Run: `pytest -v`
Expected: PASS (preflight + imports tests all green).

- [ ] **Step 4: Commit**

```bash
git add tests/test_imports.py
git commit -m "test: add import smoke-test for the workflow chain"
```

---

## Task 5: CI pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.13", "3.14"]
    env:
      # Dummy values so Settings() constructs and the import smoke-test runs.
      ANTHROPIC_API_KEY: test-key
      TAVILY_API_KEY: test-key
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          allow-prereleases: true
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: pytest -v
```

- [ ] **Step 2: Validate the workflow file is well-formed YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('ok')"`
Expected: prints `ok`

- [ ] **Step 3: Confirm the suite passes locally (what CI will run)**

Run: `pytest -v`
Expected: PASS (all preflight + import tests green)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add test + import smoke-test workflow on py3.13/3.14"
```

---

## Self-Review

**Spec coverage (Stage 0 only):**
- CI pipeline (install slim reqs on Py 3.13/3.14, import smoke-test, pytest) → Task 4 (smoke-test) + Task 5 (CI). ✓
- Test scaffolding (`tests/` + `conftest.py` + `sotorasib` fixture, mocked/no live calls) → Task 1. ✓
- Graceful config failure (clear message instead of white-screen crash) → Tasks 2 + 3. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete content; every command shows expected output. ✓

**Type consistency:** `missing_required_secrets(env)` is defined in Task 2 and called identically in Task 3 (`missing_required_secrets(os.environ)`). `REQUIRED_SECRETS` constant defined once. `demo_state` fixture defined in Task 1 (not yet consumed in Stage 0 — first used by later stages, intentional). ✓

**Note on the entrypoint edit (Task 3):** it is a manual integration step not covered by a unit test (it renders Streamlit UI). Its logic lives in the unit-tested `missing_required_secrets`; the wiring is verified manually by deploying with/without a secret, and the import smoke-test guards the chain it precedes.
