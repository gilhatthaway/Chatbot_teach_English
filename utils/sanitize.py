import json
import math
from typing import Any


def sanitize(obj: Any) -> Any:
    """Recursively sanitize an object for JSON serialization.

    - Remove any dict key named 'redacted_thinking'.
    - Replace NaN/Inf floats with None.
    - Convert unknown objects to str as a last resort.
    - Return None for values that cannot be serialized.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "redacted_thinking":
                continue
            sv = sanitize(v)
            if sv is not None:
                out[k] = sv
        return out

    if isinstance(obj, list):
        res = []
        for x in obj:
            sx = sanitize(x)
            if sx is not None:
                res.append(sx)
        return res

    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj

    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj

    # Try to convert unknown objects to something JSON-friendly
    try:
        return str(obj)
    except Exception:
        return None


def safe_invoke(llm, *args, **kwargs):
    """Sanitize inputs (args/kwargs) then call llm.invoke.

    Keeps behavior minimal: tries to preserve first positional arg (prompt) and
    will remove problematic fields like `redacted_thinking`.
    """
    clean_args = []
    for a in args:
        clean_args.append(sanitize(a))

    clean_kwargs = sanitize(kwargs) or {}

    # Quick JSON validation; if it fails, drop kwargs and pass first arg as string
    try:
        json.dumps({"args": clean_args, "kwargs": clean_kwargs}, ensure_ascii=False)
    except Exception:
        if clean_args:
            try:
                return llm.invoke(str(clean_args[0]))
            except Exception:
                return llm.invoke(clean_args[0])
        return llm.invoke(*args, **kwargs)

    return llm.invoke(*clean_args, **clean_kwargs)
