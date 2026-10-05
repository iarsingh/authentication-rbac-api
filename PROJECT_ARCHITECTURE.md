# authentication-rbac-api — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

Check that a role is allowed to perform an action. Unknown roles fail. Nothing is written to a user store.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/rbac/__init__.py"]
    M1["src/rbac/gate.py"]
    M2["src/rbac/main.py"]
    M2 -->|imports| M1
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/rbac/main.py`](src/rbac/main.py) | HTTP handlers: `GET /healthz`, `POST /check` |
| [`src/rbac/gate.py`](src/rbac/gate.py) | Functions: `check` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/rbac/__init__.py`](src/rbac/__init__.py) | Implementation or supporting configuration |
| [`tests/test_gate.py`](tests/test_gate.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/rbac/main.py`](src/rbac/main.py#L8) |
| `POST /check` | `post_check` | [`src/rbac/main.py`](src/rbac/main.py#L13) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `check(body)`

Source: [`src/rbac/gate.py`](src/rbac/gate.py#L12).

Calls visible in this function: `ALLOWED.get`, `InputError`, `body.get`, `failed.append`, `isinstance`, `str`.

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

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `InputError('body must be an object')` | [`src/rbac/gate.py`](src/rbac/gate.py#L14) |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/rbac/main.py`](src/rbac/main.py#L17) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/rbac/gate.py`](src/rbac/gate.py) defines module-level containers: `ALLOWED`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `check`

In [`src/rbac/gate.py`](src/rbac/gate.py#L12), `check(body)` receives the inputs. The function computes these intermediate values:

- `failed = []`
- `role = str(body.get('role', ''))`
- `action = str(body.get('action', ''))`
- `perms = ALLOWED.get(role)`

Its result is defined by:

- `{'passed': not failed, 'failed': failed, 'applied': False}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/rbac/gate.py`](src/rbac/gate.py#L12) branches on:

- `not isinstance(body, dict)`
- `perms is None`
- `action not in perms`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_gate.py`](tests/test_gate.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
