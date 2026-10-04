class InputError(ValueError):
    pass


def check(body):
    if not isinstance(body, dict):
        raise InputError("body must be an object")
    failed = []

    role = str(body.get("role", "")); action = str(body.get("action", "")); allowed = {"viewer": {"read"}, "member": {"read", "create"}, "admin": {"read", "create", "delete"}}; perms = allowed.get(role); failed.append("unknown_role") if perms is None else None; failed.append("forbidden") if perms is not None and action not in perms else None
    return {"passed": not failed, "failed": failed, "applied": False}
