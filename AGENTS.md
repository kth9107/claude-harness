# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

This is a personal workspace at `/Users/ku/claude`. A multi-agent harness is configured for development, content, data analysis, and research tasks.

---

## Code Review Rules

When asked to review code, use the **codex-reviewer** agent which runs `~/workspace/scripts/codex_review.py` via OpenAI API.

### Review Priorities (in order)

1. **Correctness** — Logic bugs, off-by-one errors, wrong assumptions
2. **Security** — Injection, auth bypass, sensitive data exposure, insecure defaults
3. **Concurrency** — Race conditions, deadlocks, missing locks, non-atomic operations
4. **Performance** — N+1 queries, unnecessary allocations, missing indexes
5. **Error Handling** — Unhandled exceptions, missing retries, swallowed errors
6. **Testing** — Critical paths with no test coverage

### Reporting Rules

- Report findings first, ordered by severity: critical > high > medium > low > info
- Include exact file path and line reference for every finding
- Avoid style-only comments unless they hide a real bug
- If no issues are found, say so clearly: "No issues found"
- One finding = one real problem (no duplicates)

### How to Run

```bash
# 특정 경로 리뷰
~/workspace/scripts/.venv/bin/python ~/workspace/scripts/codex_review.py \
  --path ./backend/services/ --pretty

# git diff 리뷰
git diff HEAD~1 | ~/workspace/scripts/.venv/bin/python \
  ~/workspace/scripts/codex_review.py --diff - --pretty
```

### Required Environment

- `OPENAI_API_KEY` must be set
- Script location: `~/workspace/scripts/codex_review.py`
- Python env: `~/workspace/scripts/.venv/bin/python`
