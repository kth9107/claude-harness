#!/usr/bin/env python3
"""Record harness feedback and surface repeated improvement candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_STATE_SUBDIR = Path(".claude/harness/state")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def improvement_candidates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((entry["target_type"], entry["target"]) for entry in entries)
    candidates = []
    for (target_type, target), count in counts.items():
        if count < 2:
            continue
        candidates.append({"target_type": target_type, "target": target, "count": count})
    return sorted(candidates, key=lambda item: (-item["count"], item["target"]))


def record_feedback(
    root: str | Path,
    *,
    state_dir: str | Path | None = None,
    target_type: str,
    target: str,
    summary: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    state_path = Path(state_dir).resolve() if state_dir else root / DEFAULT_STATE_SUBDIR
    state_path.mkdir(parents=True, exist_ok=True)
    feedback_path = state_path / "feedback.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_type": target_type,
        "target": target,
        "summary": summary,
    }
    with feedback_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    entries = read_jsonl(feedback_path)
    result = {
        "feedback_path": str(feedback_path),
        "recorded": entry,
        "feedback_count": len(entries),
        "improvement_candidates": improvement_candidates(entries),
    }
    (state_path / "feedback-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Harness repository root")
    parser.add_argument("--state-dir", default=None, help="State output directory")
    parser.add_argument("--target-type", default="agent", choices=["agent", "skill", "edge", "plugin", "workflow"])
    parser.add_argument("--target", default=None, help="Feedback target")
    parser.add_argument("--agent", default=None, help="Shortcut for --target-type agent --target NAME")
    parser.add_argument("--summary", required=True, help="Feedback summary")
    args = parser.parse_args()

    target_type = "agent" if args.agent else args.target_type
    target = args.agent or args.target
    if not target:
        parser.error("--target or --agent is required")

    result = record_feedback(
        args.root,
        state_dir=args.state_dir,
        target_type=target_type,
        target=target,
        summary=args.summary,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
