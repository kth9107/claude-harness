#!/usr/bin/env python3
"""Audit the local Claude Code harness graph against files on disk."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_STATE_SUBDIR = Path(".claude/harness/state")
GRAPH_PATH = Path(".claude/harness/harness.graph.json")
SCHEMA_PATH = Path(".claude/harness/schema.json")
ALLOWED_NODE_TYPES = {"agent", "skill", "plugin", "workflow_phase", "process_type"}
ALLOWED_EDGE_TYPES = {
    "routes",
    "depends_on",
    "requires",
    "post_processes",
    "feedback_updates",
    "cleanup_reviews",
    "uses",
}


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def collect_markdown_stems(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {file.stem for file in path.glob("*.md")}


def collect_skill_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    names: set[str] = set()
    for skill_file in path.glob("*/SKILL.md"):
        frontmatter = parse_frontmatter(skill_file)
        names.add(frontmatter.get("name") or skill_file.parent.name)
    for skill_file in path.glob("*.md"):
        frontmatter = parse_frontmatter(skill_file)
        names.add(frontmatter.get("name") or skill_file.stem)
    return names


def plugin_inventory() -> dict[str, Any]:
    installed = read_json(Path.home() / ".claude/plugins/installed_plugins.json", {"plugins": {}})
    settings = read_json(Path.home() / ".claude/settings.json", {"enabledPlugins": {}})
    return {
        "installed": sorted((installed.get("plugins") or {}).keys()),
        "enabled": {
            name: enabled
            for name, enabled in (settings.get("enabledPlugins") or {}).items()
        },
    }


def cleanup_candidates(graph: dict[str, Any], inventory: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "keep": [],
        "conditional_keep": [],
        "disabled": [],
        "disable_candidate": [],
        "remove_candidate": [],
    }
    installed = set(inventory["installed"])
    enabled = inventory["enabled"]
    for node in graph.get("nodes", []):
        if node.get("type") != "plugin":
            continue
        policy = node.get("cleanup_policy", "conditional_keep")
        label = node["label"]
        if policy == "remove_candidate" and label not in installed:
            continue
        if policy == "disable_candidate" and enabled.get(label) is False:
            policy = "disabled"
        groups.setdefault(policy, []).append(
            {
                "id": node["id"],
                "label": label,
                "purpose": node.get("purpose", ""),
                "weight": node.get("weight", "medium"),
                "required_by": node.get("required_by", []),
                "cleanup_policy": policy,
                "installed": label in installed,
                "enabled": enabled.get(label),
                "uninstall_command": f"claude plugin uninstall {label}",
            }
        )
    return groups


def validate_graph_shape(root: Path, graph: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not (root / SCHEMA_PATH).exists():
        warnings.append(f"Missing schema file: {SCHEMA_PATH}")
    for key in ("version", "nodes", "edges"):
        if key not in graph:
            errors.append(f"Graph missing required field: {key}")
    for node in graph.get("nodes", []):
        for key in ("id", "type", "label"):
            if key not in node:
                errors.append(f"Graph node missing required field {key}: {node}")
        if node.get("type") not in ALLOWED_NODE_TYPES:
            errors.append(f"Unsupported node type for {node.get('id')}: {node.get('type')}")
    for edge in graph.get("edges", []):
        for key in ("from", "to", "type"):
            if key not in edge:
                errors.append(f"Graph edge missing required field {key}: {edge}")
        if edge.get("type") not in ALLOWED_EDGE_TYPES:
            errors.append(f"Unsupported edge type {edge.get('type')}: {edge}")
    return errors, warnings


def run_audit(root: str | Path, state_dir: str | Path | None = None, write_state: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    state_path = Path(state_dir).resolve() if state_dir else root / DEFAULT_STATE_SUBDIR
    graph_file = root / GRAPH_PATH
    graph = read_json(graph_file)

    errors: list[str] = []
    warnings: list[str] = []
    if graph is None:
        errors.append(f"Missing graph file: {graph_file}")
        graph = {"nodes": [], "edges": []}
    shape_errors, shape_warnings = validate_graph_shape(root, graph)
    errors.extend(shape_errors)
    warnings.extend(shape_warnings)

    node_ids = {node.get("id") for node in graph.get("nodes", [])}
    agent_nodes = {
        node["id"]: node
        for node in graph.get("nodes", [])
        if node.get("type") == "agent" and node.get("id")
    }
    skill_nodes = {
        node["id"]: node
        for node in graph.get("nodes", [])
        if node.get("type") == "skill" and node.get("id")
    }
    edge_refs = {edge.get("from") for edge in graph.get("edges", [])} | {
        edge.get("to") for edge in graph.get("edges", [])
    }

    for ref in sorted(edge_refs - node_ids):
        errors.append(f"Graph edge references missing node: {ref}")

    agent_files = collect_markdown_stems(root / ".claude/agents")
    skill_names = collect_skill_names(root / ".claude/skills")

    for agent_id, node in sorted(agent_nodes.items()):
        path = root / node.get("path", "")
        if not path.exists():
            errors.append(f"Agent node path missing: {agent_id} -> {node.get('path')}")
        else:
            frontmatter = parse_frontmatter(path)
            declared_model = frontmatter.get("model")
            expected_model = node.get("model")
            if declared_model and expected_model and declared_model != expected_model:
                warnings.append(
                    f"Model mismatch for {agent_id}: graph={expected_model}, file={declared_model}"
                )

    for agent_file in sorted(agent_files - set(agent_nodes.keys())):
        warnings.append(f"Agent file is not represented in graph: {agent_file}")

    for skill_id, node in sorted(skill_nodes.items()):
        path = root / node.get("path", "")
        if not path.exists():
            errors.append(f"Skill node path missing: {skill_id} -> {node.get('path')}")

    if "personal-assistant" not in skill_nodes:
        errors.append("Graph must include personal-assistant skill node")

    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        claude_text = claude_md.read_text(encoding="utf-8")
        if "변경 이력" not in claude_text:
            warnings.append("CLAUDE.md has no change history section")
    else:
        errors.append("Missing CLAUDE.md")

    post_processing_agents = sorted(
        node["id"]
        for node in graph.get("nodes", [])
        if node.get("type") == "agent" and node.get("phase") == "post-processing"
    )

    inventory = plugin_inventory()
    result = {
        "root": str(root),
        "summary": {
            "agent_files": len(agent_files),
            "skill_entries": len(skill_names),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_edges": len(graph.get("edges", [])),
            "installed_plugins": len(inventory["installed"]),
        },
        "agent_files": sorted(agent_files),
        "skill_names": sorted(skill_names),
        "post_processing_agents": post_processing_agents,
        "plugin_inventory": inventory,
        "cleanup_candidates": cleanup_candidates(graph, inventory),
        "errors": errors,
        "warnings": warnings,
    }

    if write_state:
        state_path.mkdir(parents=True, exist_ok=True)
        (state_path / "audit-latest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Harness repository root")
    parser.add_argument("--state-dir", default=None, help="State output directory")
    args = parser.parse_args()

    result = run_audit(args.root, state_dir=args.state_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
