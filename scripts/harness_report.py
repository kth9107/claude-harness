#!/usr/bin/env python3
"""Generate a human-readable harness status report."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


DEFAULT_STATE_SUBDIR = Path(".claude/harness/state")


def load_local_script(name: str):
    path = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def format_plugin_items(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.append("- 없음")
        return lines
    for item in items:
        required_by = ", ".join(item.get("required_by", [])) or "직접 참조 없음"
        lines.append(
            f"- `{item['label']}` ({item.get('weight', 'medium')}) — {item.get('purpose', '')}; required_by: {required_by}"
        )
        if item["cleanup_policy"] in {"disable_candidate", "remove_candidate"}:
            lines.append(f"  - 삭제 명령 예시: `{item['uninstall_command']}`")
            lines.append("  - 대체: `~/.claude/settings.json`의 `enabledPlugins` 값을 `false`로 변경 후 Claude Code 재시작 또는 `/reload-plugins`")
        if item["cleanup_policy"] == "disabled":
            lines.append("  - 상태: `~/.claude/settings.json`에서 `enabledPlugins`가 `false`")
            lines.append("  - 다시 활성화: 해당 값을 `true`로 변경 후 Claude Code 재시작 또는 `/reload-plugins`")
    return lines


def generate_report(root: str | Path, state_dir: str | Path | None = None, write_report: bool = True) -> str:
    root = Path(root).resolve()
    state_path = Path(state_dir).resolve() if state_dir else root / DEFAULT_STATE_SUBDIR
    state_path.mkdir(parents=True, exist_ok=True)

    audit_module = load_local_script("harness_audit.py")
    audit = audit_module.run_audit(root, state_dir=state_path, write_state=True)
    feedback_summary = read_json(state_path / "feedback-summary.json", {"improvement_candidates": [], "feedback_count": 0})
    cleanup = audit["cleanup_candidates"]

    lines = [
        "# Claude Harness Status Report",
        "",
        "## 요약",
        f"- Agent files: {audit['summary']['agent_files']}",
        f"- Skill entries: {audit['summary']['skill_entries']}",
        f"- Graph nodes/edges: {audit['summary']['graph_nodes']} / {audit['summary']['graph_edges']}",
        f"- Installed plugins: {audit['summary']['installed_plugins']}",
        f"- Errors: {len(audit['errors'])}",
        f"- Warnings: {len(audit['warnings'])}",
        "",
        "## 감사 결과",
    ]
    if audit["errors"]:
        lines.extend(f"- ERROR: {item}" for item in audit["errors"])
    else:
        lines.append("- 오류 없음")
    if audit["warnings"]:
        lines.extend(f"- WARNING: {item}" for item in audit["warnings"])

    lines.extend(["", "## 피드백 기반 개선 후보"])
    candidates = feedback_summary.get("improvement_candidates", [])
    if candidates:
        for item in candidates:
            lines.append(f"- `{item['target']}` ({item['target_type']}): {item['count']}회 반복")
    else:
        lines.append("- 반복 피드백 없음")

    lines.extend(["", *format_plugin_items("유지", cleanup.get("keep", []))])
    lines.extend(["", *format_plugin_items("조건부 유지", cleanup.get("conditional_keep", []))])
    lines.extend(["", *format_plugin_items("비활성화 완료", cleanup.get("disabled", []))])
    lines.extend(["", *format_plugin_items("비활성화 후보", cleanup.get("disable_candidate", []))])
    lines.extend(["", *format_plugin_items("삭제 후보", cleanup.get("remove_candidate", []))])
    lines.extend(
        [
            "",
            "## 정리 원칙",
            "- 이 리포트는 삭제 후보와 명령을 안내할 뿐 자동 삭제하지 않는다.",
            "- 실제 `claude plugin uninstall ...` 실행이나 캐시 삭제는 사용자 승인 후 수행한다.",
        ]
    )

    report = "\n".join(lines) + "\n"
    if write_report:
        (state_path / "harness-report.md").write_text(report, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Harness repository root")
    parser.add_argument("--state-dir", default=None, help="State output directory")
    args = parser.parse_args()

    print(generate_report(args.root, state_dir=args.state_dir), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
