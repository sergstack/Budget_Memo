from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_claim_freeze_diff import check_claim_freeze


def main() -> int:
    parser = argparse.ArgumentParser(description="Release gate wrapper for claim-freeze diff.")
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--revised", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = check_claim_freeze(args.frozen, args.revised)
    result["release_allowed"] = result["status"] == "pass"
    result["release_guard"] = "do_not_create_release_artifact" if result["status"] != "pass" else "release_may_continue"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
