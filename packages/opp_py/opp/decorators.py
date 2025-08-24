from __future__ import annotations

import os
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    from odin_sdk.client import OPEClient  # type: ignore
except Exception:  # pragma: no cover
    from .odin_shim import OPEClient

from .util import utcnow


def _get_client(explicit: OPEClient | None) -> OPEClient:
    if explicit is not None:
        return explicit
    gw = os.getenv("OPP_GATEWAY_URL", "http://127.0.0.1:8080")
    seed = os.getenv("ODIN_SENDER_PRIV_B64") or os.getenv("OPP_SENDER_PRIV_B64")
    kid = os.getenv("ODIN_SENDER_KID") or os.getenv("OPP_SENDER_KID", "opp-sender")
    if not seed:
        raise RuntimeError("Missing ODIN_SENDER_PRIV_B64 / OPP_SENDER_PRIV_B64 for stamping")
    return OPEClient(gateway_url=gw, sender_priv_b64=seed, sender_kid=kid)


def stamp(
    step_type: str,
    attrs: dict[str, Any] | None = None,
    *,
    inputs: Callable[[tuple[Any, ...], dict[str, Any]], Any] | None = None,
    outputs: Callable[[Any], Any] | None = None,
    client: OPEClient | None = None,
):
    """Decorator emitting start/end step receipts.

    Optional inputs/outputs callables allow hashing of function IO for provenance linking.
    """
    from .util import cid_of  # local import to avoid cycles

    attrs = attrs or {}

    def deco(fn: Callable[..., Any]):
        @wraps(fn)
        def wrapper(*f_args: Any, **f_kwargs: Any):
            _client = _get_client(client)
            start_payload: dict[str, Any] = {
                "step": step_type,
                "phase": "start",
                "ts": utcnow(),
                "attrs": attrs,
            }
            if inputs is not None:
                try:
                    inp_obj = inputs(f_args, f_kwargs)
                    start_payload["inputs_cid"] = cid_of(inp_obj)
                except Exception:  # pragma: no cover
                    start_payload["inputs_cid_error"] = True
            env1 = _client.create_envelope(start_payload, "opp.step.v1", "opp.step.v1")
            _client.send_envelope(env1)
            status = "ok"
            result: Any = None
            try:
                result = fn(*f_args, **f_kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                end_payload: dict[str, Any] = {
                    "step": step_type,
                    "phase": "end",
                    "ts": utcnow(),
                    "status": status,
                }
                if outputs is not None and status == "ok":
                    try:
                        out_obj = outputs(result)
                        end_payload["outputs_cid"] = cid_of(out_obj)
                    except Exception:  # pragma: no cover
                        end_payload["outputs_cid_error"] = True
                env2 = _client.create_envelope(end_payload, "opp.step.v1", "opp.step.v1")
                _client.send_envelope(env2)
        return wrapper

    return deco
