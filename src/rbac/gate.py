class InputError(ValueError):
    pass


ALLOWED = {
    "viewer": {"read"},
    "member": {"read", "create"},
    "admin": {"read", "create", "delete"},
}


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
