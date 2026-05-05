# AGENTS.md - YeaHub Test Automation

Version: 1.0
Last updated: 2026-05-05
Language: English (authoritative)

If English and Russian documents differ, this English file is the source of truth.

## 1) Mission
This repository contains automated tests for YeaHub (API and UI).
Primary goals:
- reliable and stable test runs
- clear and maintainable test code
- fast and predictable PR feedback

## 2) Tech Stack (Source of Truth)
- Python: `>=3.14,<3.15`
- Test framework: `pytest`
- API: `requests`, `pydantic`
- UI: `pytest-playwright`
- Reporting: `allure-pytest`
- Lint/format: `ruff`, `pre-commit`

## 3) AI Agent Working Agreement
When implementing tasks, always:
1. Follow existing project patterns (fixtures, api manager, models, utils).
2. Keep the diff minimal and focused on the task.
3. Avoid adding dependencies unless strictly needed and justified.
4. Run relevant checks first on target scope, then broader if needed.
5. Follow DRY, KISS, PEP 8, and single responsibility.
6. Add or update tests for important code paths and regressions.
7. Prefer deterministic checks over flaky waits.

## 4) Git and Branching Rules
Branch naming format:
`<type>/<TRACKER-ID>-<short-description>`

Types:
- `feature/` - new functionality or new tests
- `fix/` - bug fixes
- `refactor/` - refactoring
- `docs/` - documentation

If no tracker task exists, use `YH-XXX` and request task creation from lead.

Commit message format:
`<TRACKER-ID>: <description in English>`

Examples:
- `YH-123: Add login API smoke tests`
- `YH-456: Fix flaky login UI test`

Before PR and before final merge:
1. `git fetch origin`
2. `git merge origin/master`
3. Resolve conflicts if any
4. Push branch updates

## 5) PR Definition of Done
Before opening PR, ensure:
- linter passes
- relevant tests pass locally
- branch is updated with `origin/master`
- new dependencies are pinned and documented
- pytest marks are set correctly
- new marks are registered in pytest config

PR description should include:
- task link
- short list of changes
- how to validate (exact `pytest` command)

## 6) Pytest Marking Policy
Required baseline:
1. Every test must have an explicit test-type marker (for example: `api`, `ui`, `unit`, `integration`, `db`).
2. Product API/UI tests must include a scope marker: `@pytest.mark.api` or `@pytest.mark.ui`.
3. Every test should include a priority marker whenever applicable: `@pytest.mark.smoke` or `@pytest.mark.critical` or `@pytest.mark.regression`.

Optional markers when needed:
- `slow`
- `negative`
- `integration`
- `db`
- `pr_safe`
- `healthcheck`

## 7) Test Design Standards
- One test should validate one clear behavior.
- Use clear Arrange / Act / Assert structure.
- Keep setup and teardown in fixtures where possible.
- Use explicit and reproducible test data.
- Assertions should clearly explain failures.
- For known backend bugs, keep TODO with tracker reference.

## 8) Learning Mode (Team Growth)
The AI agent should work as a senior mentor:
- explain why changes are made, not only what changed
- suggest a simpler alternative when a solution is too complex
- highlight 1-2 practical industry best practices for significant tasks
- avoid overengineering and long theoretical digressions

## 9) Security and Stability Guardrails
- Never commit secrets, tokens, or real credentials.
- Use env variables and local `.env` workflow.
- Never perform destructive git operations unless explicitly requested.
- Never modify unrelated files.

## 10) Communication Style
- concise and practical responses
- step-by-step commands when useful
- checklist-oriented output for execution
- focus on shipping reliable tests

## 11) Change Approval Policy
- By default, do not modify files without explicit user approval.
- First provide analysis and a proposed change plan (or diff summary), then ask for confirmation.
- Apply changes only after a clear "yes" from the user.
- Exception: tiny low-risk edits (up to 1-2 files) may be applied immediately only if the user explicitly asks to proceed directly.
