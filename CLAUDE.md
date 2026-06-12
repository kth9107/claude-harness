# CLAUDE.md

This is a personal workspace at `/Users/ku/claude` with a multi-agent harness.

## 하네스

**트리거:** 작업 요청 → `personal-assistant` 스킬. 단순 질문은 직접 응답.

**에이전트:** router(sonnet) → planner(opus) → 상위 에이전트 → test → optimizer → deploy

상위: `dev` `frontend` `backend` `api` `content` `data` `design` `security` `github`
서브: `research` (design/content 내부 호출)
후처리: `test`(Phase A/B) → `optimizer` → `deploy`

**하네스 운영:** 점검 시 `scripts/harness_audit.py` / `harness_feedback.py` / `harness_report.py` 사용. 플러그인 삭제는 사용자 승인 후에만.

## CodeGraph

`codegraph_*` 도구로 심볼 탐색. 구조 질문엔 grep보다 codegraph 우선.
