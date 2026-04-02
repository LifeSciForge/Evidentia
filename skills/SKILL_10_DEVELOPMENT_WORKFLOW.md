# SKILL_10 — Development Workflow

**Source:** [obra/superpowers](https://github.com/obra/superpowers) — `skills/writing-plans`, `skills/executing-plans`,
`skills/brainstorming`, `skills/dispatching-parallel-agents`, `skills/verification-before-completion`
**Applies to:** Every implementation task in Evidentia

---

## The 3-Phase Local-First Workflow

This is the global standard for all Evidentia work (also defined in `~/.claude/CLAUDE.md`):

| Phase | Tool | Purpose |
|-------|------|---------|
| **1 — Explore** | `qwen3-coder:30b` (local Ollama) | Map codebase, find relevant files, understand current logic |
| **2 — Plan** | Claude cloud → `PLAN.md` | Document exact files + functions to change; wait for approval |
| **3 — Implement** | Claude cloud | Only what `PLAN.md` specifies; test after every file; stop on failure |

**Rationale:** Local model handles free exploration. Cloud model reserved for coding that requires deep reasoning.

---

## Phase 1 — Exploration Template

Run this with Ollama before any implementation:

```
Use qwen3-coder:30b to:
1. Find all files relevant to [feature/bug]
2. Read and summarise the current logic in each file
3. Identify: which functions to change, what they currently do, and what side effects a change might have
4. Note any tests that exist for this code

Do NOT write any implementation code. Return a plain-text summary.
```

---

## Phase 2 — PLAN.md Template

```markdown
# PLAN.md — [Skill Name]: [One-line objective]

**Objective:** [One sentence]
**Status:** Awaiting approval
**Test command:** [exact command to run after implementation]

## Files to Create
### 1. `path/to/new_file.py`
[Purpose + key functions/classes with signatures]

## Files to Modify
### 2. `path/to/existing_file.py`
**Function:** `function_name` (line N)
**Change:** [Exact description]
Before: [code block]
After: [code block]
**Test:** [import check or unit test command]

## Execution Order
1. [step]
2. [step]
...
N. Final smoke test: `streamlit run streamlit_app.py`

## Rollback
If any step fails: `git checkout -- <file>`. Do not proceed to the next step.

## Out of Scope
- [explicit list of things NOT being changed]
```

**Rules for PLAN.md:**
- Every file listed must include exact line numbers and code blocks — no vague descriptions
- Never use "TBD", "add validation", or "handle edge cases" without showing exactly how
- Include explicit "Out of Scope" section to prevent scope creep
- Save plan to project root as `PLAN.md`; archive completed plans to `docs/plans/YYYY-MM-DD-skill.md`

---

## Phase 3 — Implementation Rules

- **One file per step** — do not modify two files simultaneously
- **Test import after every file** — `python3 -c "from path.to.module import Class; print('ok')"`
- **Run full test suite after every agent file change** — `python3 -m pytest tests/ -v`
- **Stop immediately on test failure** — do not attempt to fix without re-planning
- **Never modify files not listed in PLAN.md** — even if adjacent code looks wrong

---

## Brainstorming New Features

Before writing a PLAN.md for a new feature, do a design pass:

1. Explore existing code (Phase 1)
2. Ask clarifying questions **one at a time** — never a list of 5 questions at once
3. Present 2–3 alternative approaches with tradeoffs
4. Get approval on the chosen approach
5. **Then** write PLAN.md

Never start writing implementation plans for a feature that hasn't been approved.

---

## Parallel Agents — When to Use

Use parallel subagents when:
- There are 3+ independent issues in different files
- Fixing one issue won't affect another
- Research tasks can run simultaneously (e.g. fetching content from multiple repos)

Format for parallel dispatch:
```
Agent 1: Investigate [specific_file.py] — find why JSON parsing fails on nested objects
  Context: [exact error], [file path], [relevant lines]
  Deliver: root cause + minimal fix

Agent 2: Investigate [other_file.py] — find why retry logic is not triggering
  Context: [exact error], [file path], [relevant lines]
  Deliver: root cause + minimal fix
```

Do NOT dispatch parallel agents for:
- Tasks that share state or modify the same files
- Exploratory debugging where full context is needed
- Tasks where output of one informs the other

---

## Verification Before Completion

Before claiming any task is complete:

```bash
# 1. Run the specific test(s) for what you changed
python3 -m pytest tests/test_<relevant>.py -v

# 2. Run the full test suite
python3 -m pytest tests/ -v

# 3. Verify the app still starts
streamlit run streamlit_app.py &
sleep 5 && kill %1
```

**Never say "this should work" without running the verification command and showing the output.**

If a test passes, show the terminal output. If it fails, show the exact failure message.

---

## Git Workflow

```bash
# Before any SKILL_XX work:
git checkout -b feat/skill-05-data-quality

# After each file change:
git add src/service/validators/json_validator.py
git commit -m "SKILL_05: add extract_json_from_text with balanced-brace finder"

# After full skill complete and all tests pass:
git push origin feat/skill-05-data-quality
# Then open PR — never push directly to main
```

Branch naming: `feat/skill-XX-short-description` or `fix/agent-name-short-description`

---

## Finishing a Development Branch

Before merging any skill branch:

- [ ] All PLAN.md steps completed
- [ ] Full test suite passes: `python3 -m pytest tests/ -v`
- [ ] App starts without errors: `streamlit run streamlit_app.py`
- [ ] No files in PLAN.md's "Out of Scope" were modified (check with `git diff main`)
- [ ] `evidentia.db` not committed (must be in `.gitignore`)
- [ ] `data/chroma/` not committed
- [ ] PLAN.md archived to `docs/plans/YYYY-MM-DD-skill-XX.md`
- [ ] PR description includes: what changed, test evidence, and any deviations from PLAN.md
