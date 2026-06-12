---
name: personal-assistant
description: "General-purpose personal assistant orchestrator. Automatically routes development (code writing/bug fixing/UI), content (writing/translation/editing), data analysis (CSV/statistics/charts), research (web search/info gathering), design (UX planning/wireframing/image generation/Figma), and GitHub (commit/push/repo creation) requests to specialized agents. Use this skill for any task request. Also handles re-run, update, fix, supplement, and redo requests."
---

# Personal Assistant — General-Purpose Personal Assistant Orchestrator

This harness is maintained as a local graph + audit + feedback + cleanup loop. Before routing a task, inspect `.claude/harness/harness.graph.json` when the request concerns harness structure, agent routing, plugin cleanup, or workflow drift.

## Agent Tree Structure

```
router-agent (sonnet — fixed)
    ↓
planner-agent (opus — fixed)
    ↓
┌──────────────────────────────────────────────────┐
│ Upper-tier agents — can be called in parallel     │
├────────────┬─────────────┬──────────┬────────────┤
│ dev-agent  │content-agent│data-agent│github-agent│
│            │    ↓        │          │            │
│            │(research-   │          │            │
│            │ agent opt.) │          │            │
└────────────┴──────┬──────┴──────────┴────────────┘
                    │
             design-agent
                    ↓
             research-agent (required prerequisite)

security-agent (independent — security audits, hardening, CVE, incident response)
```
```
[Post-processing agents — fixed order]
test-agent
├── Phase A: immediately on each agent completion → individual output unit test
└── Phase B: after all agents complete → integration test
    ↓
optimizer-agent
├── Review Phase B report → identify and improve performance/quality issues (P0/P1)
└── Re-run Phase B if improvements made (max 1 time)
    ↓ (after optimizer-agent completes)
deploy-agent
└── Execute deployment → health check → deployment report
```

**Core Rules:**
- `research-agent` is not an independent upper-tier agent. It is a required prerequisite sub-agent for design-agent and an optional sub-agent for content-agent.
- `test-agent` is not an independent upper-tier agent. It is a post-processing agent automatically called by the orchestrator after upper-tier agents complete.
- `optimizer-agent` is not an independent upper-tier agent. It is a post-processing agent automatically called by the orchestrator after test-agent Phase B completes.
- `deploy-agent` only runs after optimizer-agent completes. If test-agent Phase B FAILs, neither optimizer-agent nor deploy-agent is called.
- router-agent always runs with the `sonnet` model.
- planner-agent always runs with the `opus` model.
- Upper-tier agents run with the model assigned by router-agent.

---

## Workflow

### Phase 0: Context Check

Before starting, check for existing work:
- `_workspace/` exists + partial modification request → **Partial re-run** (re-call only the relevant agent)
- `_workspace/` exists + new input provided → **New run** (move existing to `_workspace_prev/`)
- `_workspace/` does not exist → **Initial run**

Also perform a harness maintenance check when the request mentions harness structure, audit, cleanup, plugin/skill weight, or recurring failures:

```bash
python3 scripts/harness_audit.py --root /Users/ku/claude
python3 scripts/harness_report.py --root /Users/ku/claude
```

The maintenance report classifies plugins and skills as keep, conditional keep, disable candidate, or remove candidate. Do not uninstall or delete anything automatically. First report the item name, current purpose, reason, impact, recovery path, and the exact command, then wait for explicit user approval before running commands such as:

```bash
claude plugin uninstall watch@claude-video
```

If uninstall is unavailable, tell the user to set the plugin to `false` in `~/.claude/settings.json` under `enabledPlugins`, then restart Claude Code or run `/reload-plugins`.

---

### Phase 1: Routing Decision (router-agent)

Call router-agent first in every request.

```
Agent(
  agent_file: ".claude/agents/router-agent.md",
  prompt: [full text of original user request],
  model: "sonnet"
)
```

router-agent outputs:
- List of upper-tier agents to call
- Model assigned to each agent (haiku / sonnet / opus)
- Execution order (parallel / sequential)
- Sub-agent chains (design-agent → research-agent, etc.)

---

### Phase 2: Execution Plan Report (planner-agent)

Call planner-agent with router-agent results as input.

```
Agent(
  agent_file: ".claude/agents/planner-agent.md",
  prompt: [original user request + router-agent routing decision result],
  model: "opus"
)
```

planner-agent outputs an execution plan report including model information to the user.

- **Auto-approval mode**: Automatically proceed to Phase 3 immediately after reporting
- **Normal mode**: Wait for user response after reporting, then proceed to Phase 3

---

### Phase 3: Upper-Tier Agent Execution

Call the agents decided by router-agent with **the model assigned by router**.

**Single agent:**
```
Agent(
  agent_file: ".claude/agents/{agent-name}.md",
  prompt: [request content + context],
  model: "{model assigned by router}"
)
```

**Parallel team (independent tasks):**
```
Call simultaneously in parallel:
Agent(agent_file: "dev-agent.md",     model: "{router assignment}")
Agent(agent_file: "data-agent.md",    model: "{router assignment}")
```

**Sequential team (dependency relationship):**
```
1. Agent(agent_file: "design-agent.md", model: "{router assignment}")
   → design-agent automatically calls research-agent internally (model: sonnet)
2. Agent(agent_file: "dev-agent.md",    model: "{router assignment}")
   → Uses design-agent results as input
```

**Sub-agent chains (handled automatically):**
- `design-agent` calls research-agent first internally (no explicit instruction needed)
- `content-agent` calls research-agent internally when research is needed

---

### Phase 3.5: Test Execution (test-agent)

Call test-agent in all cases where upper-tier agent outputs exist. Exception: pure research/translation-only requests.

**Phase A — Individual tests (immediately on each agent completion):**
```
On each agent completion signal:
Agent(
  agent_file: ".claude/agents/test-agent.md",
  prompt: [completed agent name + output path + scope assigned to that agent],
  model: "sonnet"
)
```
- Phase A FAIL (Critical/High): Request rework from that agent, then re-test
- Phase A PASS or FAIL (Medium/Low): Proceed to next agent, include defects in Phase B report

**Phase B — Integration test (after all agents complete):**
```
Agent(
  agent_file: ".claude/agents/test-agent.md",
  prompt: [full original request + all Phase A report paths + full output list],
  model: "sonnet"
)
```
- Phase B FAIL (Critical): Rework related agents then re-run integration test
- After Phase B completes, notify user of final quality report (`_workspace/test_integration_report.md`)

---

### Phase 3.7: Optimization (optimizer-agent)

Automatically runs after test-agent Phase B completes. Skip for pure analysis/content requests with no deployable output.

```
Agent(
  agent_file: ".claude/agents/optimizer-agent.md",
  prompt: [Phase B report path + all Phase A report paths + full output list],
  model: "opus"
)
```

- **Phase B FAIL**: Prohibit optimizer-agent call. Request rework then re-run test.
- **P0/P1 improvements complete**: Re-run test-agent Phase B (1 cycle limit).
- **No improvements (P2/P3 only)**: Generate recommendation report then proceed directly to Phase 4.
- After optimization completes, notify user of `_workspace/optimizer_report.md`.

---

### Phase 4: Deployment (deploy-agent)

Automatically runs after optimizer-agent completes. Skip for pure analysis/content requests with no deployable output.

```
Agent(
  agent_file: ".claude/agents/deploy-agent.md",
  prompt: [optimizer_report path + Phase B report path + project root path + deployment environment (production/staging)],
  model: "sonnet"
)
```

- **Phase B FAIL or optimizer-agent incomplete**: Prohibit deploy-agent call. Request rework then re-run test.
- **Deployment success**: Deliver deployment URL + health check results to user.
- **Deployment failure**: deploy-agent performs automatic rollback then delivers failure report.

---

### Phase 5: Result Delivery

- Deliver outputs + test-agent quality report + deploy-agent deployment report together
- State deployment URL and health check status clearly
- Confirm whether follow-up work is needed
- Gather improvement feedback (if needed)
- When feedback identifies harness drift, repeated agent failure, or plugin/skill bloat, record it with `scripts/harness_feedback.py` so the next audit can surface improvement candidates.

---

## Model Assignment Quick Reference

| Model | When to Use |
|-------|-------------|
| `haiku` | Simple translation, format conversion, short text cleanup |
| `sonnet` | Code, analysis, research, general content, GitHub (default) |
| `opus` | Complex design, multi-domain, creative design, planner |

router-agent always makes the final decision, so the orchestrator follows the router output as-is.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Agent failure | Retry once; if it fails again, proceed without results and note the omission |
| Unclear domain | router-agent assigns the closest matching agent |
| Complex request failure | Preserve each agent's results independently; cite sources when conflicting |
| research-agent failure | Retry with modified search terms; if it fails again, proceed with general knowledge |
| test-agent Phase A FAIL (Critical/High) | Immediately request rework from that agent, re-run Phase A after completion |
| test-agent Phase B FAIL (Critical) | Rework related agents then re-run full integration test. Prohibit deploy-agent call |
| test-agent failure (agent itself errors) | Retry once; if it fails again, recommend manual review and proceed to Phase 5 |
| optimizer-agent improvement then Phase B re-fails | No additional cycle. Record in report and wait for user decision (confirm whether to proceed with deploy) |
| optimizer-agent failure (agent itself errors) | Retry once; if it fails again, skip optimizer and proceed to Phase 4, note the omission |
| deploy-agent deployment failure | deploy-agent performs automatic rollback. Deliver failure report and wait for user decision |
| deploy-agent health check failure | Immediate rollback then root cause report. Redeployment proceeds after user confirmation |

---

## Execution Examples

```
# Single: "Add a Next.js feature and deploy"
router → frontend(sonnet) → test PhaseA → optimizer → deploy

# Parallel: "Implement frontend and backend, then deploy"
router → frontend(sonnet) + backend(sonnet) [parallel]
       → test PhaseA each → test PhaseB → optimizer → deploy

# Sequential: "Design the app, implement, deploy"
router → design(opus) [research inside] → frontend(sonnet)
       → test PhaseA×2 → test PhaseB → optimizer → deploy
```
