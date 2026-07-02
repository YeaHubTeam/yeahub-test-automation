# AGENTS.md - YeaHub Test Automation

Version: 1.2
Last updated: 2026-06-28
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
8. Before changing shared helpers (`tests/mail/`, `conftest.py`, page objects used by multiple suites), **trace all callers** and edge cases (last retry attempt, missing env, teardown).
9. When a fixture or helper gains new **external prerequisites** (IMAP, live API, secrets), use **`pytest.skip` / `skipif` with a clear reason** for integration tests—not a bare `assert` in setup unless the test is explicitly unit-only.
10. Document **breaking changes** to fixture contracts or env requirements in `README.md` (CI Strategy + relevant test section), not only in PR text.

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
- new or changed **env prerequisites** (`MAIL_*`, `RUN_MAIL_INTEGRATION`, secrets) when applicable

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

### Integration prerequisites (project-wide)
- **Live mail / IMAP** (`MAIL_HOST`, `MAIL_EMAIL`, `MAIL_PASSWORD`, optional `MAIL_FOLDER`, `MAIL_PORT`): required for mail e2e, subscription/payment flows that provision verified users via IMAP, and related fixtures (`verified_registered_user`, `verified_subscription_user`, mail quartet in CI `scope=mail`).
- **`RUN_MAIL_INTEGRATION=1`**: gates explicit live mail e2e tests (see mail/UI tests with `skipif`); subscription API integration in CI uses `MAIL_*` secrets without this flag.
- **Skip vs fail**: if creds are missing locally, integration tests should **skip** with an actionable message (pattern: `tests/mail/test_mail_client_integration.py`, `require_mail_creds` + `skipif` where appropriate)—not fail mid-fixture with an opaque assert.
- **CI**: Integration workflow secrets are documented in README CI Strategy; do not assume local `.env` matches CI.

### Shared retry and polling helpers
- **Retry callbacks** (`on_retry`, refresh identity): invoke only when `attempt < max_attempts - 1`. Do not regenerate users/emails/tags on the **last** failed attempt.
- **Polling / settle-after-wait**: if a second fetch can fail (e.g. IMAP `find_message` after `wait_for_message`), wrap in `try/except` and **keep the first successful result** so the whole chain does not fail on a race.
- After changing retry/polling logic, grep callers (`register_user_with_retries`, `wait_imap_verification_link`, fixtures in `conftest.py`).

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

## 12) Task Intake (before coding)

When starting a non-trivial task, clarify (with the user if needed):
1. **Done means** — which tests/scopes must be green (Fast CI, Integration `scope=…`, local commands).
2. **Prerequisites** — `MAIL_*`, `RUN_MAIL_INTEGRATION`, Playwright, secrets; what should **skip** vs **fail** without them.
3. **Blast radius** — which fixtures, workflows, and README sections are affected.
4. **Breaking changes** — e.g. replacing static creds with ephemeral/IMAP users; document in README.

If the user did not specify, infer from the ticket and state assumptions before large diffs.

## 13) Pre-commit / Pre-PR Checklist (Agent)

Run this checklist when the user asks to **commit**, open a **PR**, or says the work is **ready to commit** (e.g. "готово к коммиту"), unless they explicitly skip checks.

1. **Scope** — Inspect `git diff` / changed paths; list affected areas (ui-auth, mail, subscription, `pages/`, CI, docs).
2. **Caller impact** — For changes in `tests/mail/`, `conftest.py`, shared `pages/`, or workflows: grep callers; check last-retry behavior and missing-env paths.
3. **Lint** — `uv run ruff check .` and `uv run ruff format . --check` on touched paths (whole repo if the diff is small).
4. **Tests** (minimal by area; see also README "Проверки перед PR"):
   - UI auth / interview / `onboarding_modal` → same paths as `run_ui_auth_smoke` in `.github/workflows/integration.yml`.
   - Changes to `onboarding_modal` or specialization → also mail `test_register_and_verify_email_e2e` when `RUN_MAIL_INTEGRATION=1` is feasible.
   - Mail / IMAP helpers or TC 422/466/115/52 → `scope=mail` quartet or the subset documented in README.
   - Subscription API/UI / `verified_*` fixtures → `tests/api/subscription/` and/or `tests/ui/subscription/` with `MAIL_*` as documented.
   - Unit / `pr_safe` only → `pytest -m "unit or pr_safe"`.
5. **Local without secrets** — When env-dependent: confirm tests **skip** with a clear reason (or document that mail is required); do not rely only on CI green.
6. **Docs** — If CI scopes, test names, `externalId`, fixture contracts, or env vars changed → update `README.md` (CI Strategy + affected test section).
7. **Lead-style self-review** — Before PR: retry semantics, skip vs assert, defensive fallbacks in helpers, README for new prerequisites, no unrelated diff.
8. **Git** — Branch `type/TRACKER-id-description`; commit `TRACKER: English summary`; remind `git fetch origin` + `git merge origin/master` before PR.
9. **Report** — Summarize pass/fail, commands run, and any skipped live runs. Do **not** `git commit` unless the user explicitly asked to commit.

If live pytest cannot run in the agent environment (e.g. Playwright browsers missing), state that clearly and give the exact commands for the user to run locally.
