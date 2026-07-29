#!/usr/bin/env python3
"""Validate root ACP/MCP/agent contracts against runtime registrations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))


def _contract_tool_names(payload: object) -> set[str]:
    if isinstance(payload, list):
        names: set[str] = set()
        for item in payload:
            if isinstance(item, str):
                names.add(item)
            elif isinstance(item, dict) and "name" in item:
                names.add(str(item["name"]))
        return names
    if isinstance(payload, dict):
        if "tools" in payload:
            return _contract_tool_names(payload["tools"])
        if "tools_in_process" in payload:
            return _contract_tool_names(payload["tools_in_process"])
    return set()


def main() -> int:
    errors: list[str] = []

    import careerpilot.acp.workflows  # noqa: F401
    from careerpilot.acp.orchestrator import acp
    from careerpilot.mcp.linkedin.server import linkedin_mcp
    from careerpilot.mcp.resume.server import resume_mcp
    from careerpilot.mcp.storage.server import storage_mcp

    runtime_workflows = set(acp.list_workflows())
    expected_implemented = {"resume_parse", "job_discovery", "tailor_resume"}
    missing = expected_implemented - runtime_workflows
    if missing:
        errors.append(f"ACP runtime missing workflows: {sorted(missing)}")

    contract_dir = ROOT / "acp" / "workflows"
    for name in expected_implemented:
        yaml_name = name.replace("_", "-")
        if not (contract_dir / f"{yaml_name}.yaml").exists() and not (
            contract_dir / f"{name}.yaml"
        ).exists():
            errors.append(f"Missing ACP contract YAML for {name}")

    checks = [
        ("resume", ROOT / "mcp" / "servers" / "resume" / "tools.json", resume_mcp),
        ("linkedin", ROOT / "mcp" / "servers" / "linkedin" / "tools.json", linkedin_mcp),
        ("storage", ROOT / "mcp" / "servers" / "storage" / "tools.json", storage_mcp),
    ]
    for server_name, tools_path, server in checks:
        if not tools_path.exists():
            errors.append(f"Missing tools.json for {server_name}")
            continue
        payload = json.loads(tools_path.read_text(encoding="utf-8"))
        contract_tools = _contract_tool_names(payload)
        runtime_tools = {t["name"] for t in server.list_tools()}
        missing_tools = contract_tools - runtime_tools
        extra = runtime_tools - contract_tools
        if missing_tools:
            errors.append(f"{server_name} MCP missing runtime tools: {sorted(missing_tools)}")
        if extra:
            errors.append(f"{server_name} MCP tools.json missing: {sorted(extra)}")

    registry = ROOT / "agents" / "registry.yaml"
    if registry.exists():
        text = registry.read_text(encoding="utf-8")
        current_id = None
        current_status = None
        current_runtime = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- id:"):
                if current_id and current_status == "implemented" and current_runtime:
                    path = ROOT / current_runtime
                    if not path.exists():
                        errors.append(f"Agent {current_id} runtime missing: {current_runtime}")
                current_id = stripped.split(":", 1)[1].strip()
                current_status = None
                current_runtime = None
            elif stripped.startswith("status:"):
                current_status = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("runtime:"):
                current_runtime = stripped.split(":", 1)[1].strip()
        if current_id and current_status == "implemented" and current_runtime:
            path = ROOT / current_runtime
            if not path.exists():
                errors.append(f"Agent {current_id} runtime missing: {current_runtime}")

    if errors:
        print("check-contracts FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("check-contracts OK")
    print(f"  workflows: {sorted(runtime_workflows)}")
    print(f"  resume tools: {[t['name'] for t in resume_mcp.list_tools()]}")
    print(f"  linkedin tools: {[t['name'] for t in linkedin_mcp.list_tools()]}")
    print(f"  storage tools: {[t['name'] for t in storage_mcp.list_tools()]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
