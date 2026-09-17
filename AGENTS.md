# AI instructions: YeaHub Test Automation

Shared instructions for Python API and UI test automation in this repository. The main workflow is to turn a supplied manual test case into an automated test.
This file is the single source of shared AI instructions. Tool-specific files reference it.
Respond in the user's language. Follow the project's conventions for code and identifiers.

## Before making changes

- Read the task, relevant README sections, configuration, and nearby tests. Before changing shared code, find its callers and read the setup and teardown of affected fixtures.
- For a non-trivial task, briefly state the expected outcome, affected files, and validation plan. Ask about ambiguities that change the contract or scope; resolve routine details using existing examples.
- A request to implement a change authorizes the necessary edits within that scope. Review, explanation, and research requests do not authorize project edits. Do not change these instructions without an explicit user request.
- Do not invent APIs, response fields, locators, dependencies, TestIT IDs, or requirements. Verify them against the code, contract, or official documentation for the installed version. Point out conflicting sources.

## When given a manual test case

- Treat the complete case as the task specification: ID, preconditions, user role, data, steps, expected results, and postconditions. Read the supplied text or accessible source in full. If a link is inaccessible or an image is unreadable, request the missing content instead of guessing.
- Check whether the case supports unambiguous assertions. Clarify missing expected results or contradictions before implementing the dependent part. Investigate technical details already available in the project yourself.
- Search for an existing automated test by case ID and scenario, along with suitable fixtures, clients, and page objects. Extend the existing implementation of the same case rather than creating a duplicate under a new name.
- Before coding, briefly map significant steps and expected results to checks. For a long case, use a table: case step or result, automated action and assertion, setup or limitation. A click, API call, or absence of exceptions alone does not confirm the expected result.
- Preserve the path under test. If the case checks UI registration, creating a user through the API does not replace that scenario. API setup and cleanup are appropriate when they are not the behavior being tested. Keep meaningful roles, statuses, tariffs, and boundary data consistent with the case.
- Separate technical setup from tested actions. A logout or account deletion required by the case is not covered merely because a fixture deletes the user during teardown.
- Do not mock the system whose behavior the manual end-to-end case checks. If only partial automation or a different test level is feasible, state its boundaries. Do not rewrite the manual case to fit the implementation without a user request.
- Usually keep one coherent scenario in one test. Independent variants may be split or parameterized while retaining their link to the original case and coverage of its expected results.
- For TestIT, obtain the manual case ID from the source and check the existing `externalId`. Follow project conventions for metadata and `workItemIds`; do not invent IDs of existing entities. A missing ID does not prevent local implementation, but the TestIT link must remain explicitly unverified.
- In the result, identify the case and automated test, list covered expected results and remaining manual checks, and provide the exact run command and its actual outcome. Label incomplete coverage as partial automation. If the test was not run, state that the implementation is unverified.

## Where to find current information

- `pyproject.toml` and `uv.lock`: Python version, dependencies, pytest markers, and Ruff settings. Do not upgrade the stack as an unrelated change.
- `README.md`: environment setup, CI Strategy, and pre-PR checks. `.env.example`: variable names without secrets.
- `.github/workflows/ci.yml` and `.github/workflows/integration.yml`: actual CI commands and test selections.
- `api/`, `custom_requester/`, and `models/`: API clients, transport, and models. `pages/`: UI actions and expectations.
- Root and nested `conftest.py` files, `tests/mail/`, `tests/ui/flows/`, and `utils/`: fixtures, data preparation, retries, and cleanup.

Read the parts relevant to the task. If the README disagrees with configuration, verify actual behavior and correct the documentation affected by the task.

## Write tests that detect failures

- Before writing a test, identify a concrete product defect that should make it fail. Derive expected results from requirements rather than copying the system's current response.
- Keep one scenario per test. Multiple assertions are appropriate when they check that scenario's result. Separate setup, action, and assertions; parameterize variants with the same steps.
- For APIs, check the status and meaningful data or state changes. Schema validation does not replace a business outcome check. For UI tests, assert the observable result of the action.
- Do not weaken assertions, broaden accepted statuses, or remove checks just to make CI green. First distinguish a test defect from a product or environment failure.
- Document known product defects with a task reference and a specific condition. If `xfail` is needed, keep strict behavior. Do not hide new failures behind `skip`, `xfail`, or broad exception handling.
- For a regression in a shared helper, add a check of the real implementation. Where feasible, show it failing before the fix and passing afterward. Do not add tests merely to increase the count.
- In unit tests, mock external boundaries such as HTTP, IMAP, and time. Do not mock the function under test or reimplement its logic inside the test. A mock should allow incorrect arguments or response handling to be detected.
- Give every test an explicit type marker. Product tests need `api` or `ui`; live scenarios also need `integration`. Add the applicable priority: `smoke`, `critical`, or `regression`. Register new markers in configuration. Do not assign `pr_safe` without checking suitability for Fast CI.

## Isolation, fixtures, and waits

- Do not depend on test order, an existing user, or mail from a previous run. Create data for the scenario and delete only resources owned by that test.
- Use explicit values for the conditions being checked. Generate unique emails and usernames with the project's shared generators; randomness must not change the meaning of the scenario.
- Choose fixture scope to match the resource lifetime. Avoid sharing mutable state between tests unless necessary.
- Handle cleanup after test failures and partially completed setup, including failures before `yield`. Close HTTP and IMAP sessions and other open resources. Cleanup errors must not obscure the original failure.
- In Playwright, use stable locators and built-in `expect` assertions. Wait for a specific state with a bounded timeout instead of adding fixed sleeps.
- Bound the total time spent polling external systems. Retry only transient errors; do not rerun an entire test just to obtain a passing result. Before retrying a write operation, check whether it could create duplicates.
- Trace all callers before changing retries. Do not invoke a callback that prepares another attempt after the final failure. Do not stack independent retry loops without accounting for their total duration.
- If an extra fetch only refines an already successful result, a transient failure must not discard that first result. Handle expected exceptions without hiding failure of a required step.

## External services and CI results

- Local integration tests without required credentials should skip with an actionable reason before contacting the service. Use existing prerequisite checks.
- A missing required secret for an explicitly selected CI scope must produce a clear configuration failure. Do not turn authentication errors or an unavailable configured service into a successful test.
- Check `MAIL_*` for IMAP and verified-user fixtures. `RUN_MAIL_INTEGRATION=1` enables explicit mail and UI end-to-end tests; subscription API tests use `MAIL_*` without that flag. Confirm exact prerequisites in the README and the fixture being called.
- Inspect imports and hooks before running commands: even `pytest --collect-only` executes Python code. Remember that `pr_safe` tests in this project may call a live API.
- Do not run payments with real payment details or use other people's accounts. Keep secrets out of code, terminal output, logs, Allure attachments, and messages.
- When changing CI or TestIT, check every affected manual and scheduled path, the selected tests, missing required variables, and repeat runs. Exit code 0 without the expected tests and results does not prove successful validation.
- When changing reporting integration, verify delivery to the intended run. If TestIT is unavailable, state that only local behavior was checked. Preserve existing `externalId` values and manual case links unless changing them is part of the task.

## Keep changes focused

- Reuse existing clients, page objects, and helpers. Extract shared code when it has clear responsibilities and real callers. Do not add speculative generic wrappers or base classes.
- Use clear names and straightforward code. Add type hints where they clarify a contract. Comments should explain a reason or constraint rather than restating the code.
- Avoid dependencies, bulk formatting, and unrelated fixes unless required by the task. Do not leave placeholders, commented-out code, or unused helpers.
- Preserve other people's uncommitted changes. Do not commit, push, or publish comments without a user request. Destructive Git operations require explicit permission.
- Name branches `<type>/<TRACKER-ID>-<description>` (`feature`, `fix`, `refactor`, or `docs`) and commits `<TRACKER-ID>: <English summary>`. If no ID is available, use `YH-XXX` and flag that a tracker task is needed. Before a PR or merge, update the branch with `git fetch origin` and `git merge origin/master`; do not substitute a force-push.
- Document changes to environment requirements, fixture contracts, CI scopes, and TestIT links in the README. Add new variables to `.env.example` without secret values. Record dependencies in `pyproject.toml` and `uv.lock`.

## Validate before finishing

Run commands from the repository root. Check the changed scenario first, then callers of shared code. Take full live-suite commands from the README and workflows.

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -m "unit or pr_safe"
```

- The last command matches Fast CI and includes API calls. For available offline checks, use `uv run pytest -m unit` and explicitly report that the full Fast CI selection was not run.
- For UI auth and interview changes, use the workflow's `run_ui_auth_smoke` selection. Onboarding changes also require checking the related mail-registration scenario when prerequisites are available.
- For mail, subscription, and verified-user helpers, select the relevant API and UI suites from the README. Check the final retry attempt, missing environment variables, and cleanup after failure.
- For documentation-only changes, check the diff, links, and command accuracy. Live tests are unnecessary without a related behavior change.
- Review the final diff for task scope, weakened checks, and unrelated edits. Never report tests as passed if they were not run, were skipped, or were excluded by a filter.

## Report the outcome

Briefly explain what changed and why. Give the commands actually run and their results; list limitations and unverified scenarios separately. One successful run is not proof of stability.
For a significant change, explain one useful practice using the affected code. In reviews, identify the location, failure condition, consequence, smallest useful fix, and how to verify it. Discuss the code rather than the author's abilities.
