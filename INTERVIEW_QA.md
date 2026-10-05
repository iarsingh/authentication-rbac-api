# authentication-rbac-api — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does authentication-rbac-api address, and what can you demonstrate?

Check that a role is allowed to perform an action. Unknown roles fail. Nothing is written to a user store.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/rbac/main.py`](src/rbac/main.py): Implementation or supporting configuration.
- [`src/rbac/ops.py`](src/rbac/ops.py): Implementation or supporting configuration.
- [`src/rbac/gate.py`](src/rbac/gate.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/rbac/__init__.py`](src/rbac/__init__.py): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `check` and explain the decision it makes?

The main walkthrough here is `check(body)` in [`src/rbac/gate.py`](src/rbac/gate.py#L12).

```python
def check(body):
    if not isinstance(body, dict):
        raise InputError("body must be an object")
    failed = []
    role = str(body.get("role", ""))
    action = str(body.get("action", ""))
    perms = ALLOWED.get(role)
    if perms is None:
        failed.append("unknown_role")
    elif action not in perms:
        failed.append("forbidden")
    return {"passed": not failed, "failed": failed, "applied": False}
```

The implementation calls `ALLOWED.get`, `InputError`, `body.get`, `failed.append`, `isinstance`, `str`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `InputError('body must be an object')` in [`src/rbac/gate.py`](src/rbac/gate.py#L14).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/rbac/main.py`](src/rbac/main.py#L19).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/rbac/ops.py`](src/rbac/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/rbac/ops.py`](src/rbac/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/rbac/ops.py`](src/rbac/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/rbac/ops.py`](src/rbac/ops.py#L113).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_gate.py`](tests/test_gate.py#L7) contains `test_pass_and_fail`:

```python
def test_pass_and_fail():
    good = client.post("/check", json={'role': 'member', 'action': 'create'}).json()
    assert good["passed"] is True
    assert good["applied"] is False
    bad = client.post("/check", json={'role': 'viewer', 'action': 'delete'}).json()
    assert bad["passed"] is False
    assert "forbidden" in bad["failed"]
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/rbac/main.py`](src/rbac/main.py#L10).
- `POST /check` → `post_check` in [`src/rbac/main.py`](src/rbac/main.py#L15).
- `GET /readyz` → `readyz` in [`src/rbac/ops.py`](src/rbac/ops.py#L44).
- `POST /workspaces` → `create_workspace` in [`src/rbac/ops.py`](src/rbac/ops.py#L49).
- `GET /workspaces` → `list_workspaces` in [`src/rbac/ops.py`](src/rbac/ops.py#L66).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/rbac/ops.py`](src/rbac/ops.py#L73).
- `GET /jobs/{job_id}` → `get_job` in [`src/rbac/ops.py`](src/rbac/ops.py#L96).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/rbac/ops.py`](src/rbac/ops.py#L105).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. Where does state live, and what happens with multiple workers?

Module-level containers include `ALLOWED` in [`src/rbac/gate.py`](src/rbac/gate.py); `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/rbac/ops.py`](src/rbac/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `check`?

In [`src/rbac/gate.py`](src/rbac/gate.py#L12), `check(body)` receives the inputs. The function computes these intermediate values:

- `failed = []`
- `role = str(body.get('role', ''))`
- `action = str(body.get('action', ''))`
- `perms = ALLOWED.get(role)`

Its result is defined by:

- `{'passed': not failed, 'failed': failed, 'applied': False}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/rbac/gate.py`](src/rbac/gate.py#L12) branches on:

- `not isinstance(body, dict)`
- `perms is None`
- `action not in perms`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 13. What does the operations plane add, and where is its limit?

[`src/rbac/ops.py`](src/rbac/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
