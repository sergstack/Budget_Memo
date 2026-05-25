from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def log_progress(
    *,
    memo_profile: str,
    stage: str,
    depth_mode: str = "not_applicable",
    status: str = "start",
    details: dict[str, Any] | None = None,
) -> None:
    payload = {
        "event": "memo_generation_progress",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memo_profile": memo_profile,
        "depth_mode": depth_mode,
        "stage": stage,
        "status": status,
    }
    if details:
        payload["details"] = details
    print(json.dumps(payload, ensure_ascii=False), flush=True)
