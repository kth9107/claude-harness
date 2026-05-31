---
name: personal-assistant
description: "범용 개인 어시스턴트 오케스트레이터. 개발(코드 작성/버그픽스/UI), 콘텐츠(글쓰기/번역/편집), 데이터 분석(CSV/통계/차트), 리서치(웹검색/정보수집), 디자인(UX기획/와이어프레임/이미지생성/Figma), GitHub(커밋/푸시/레포생성) 작업 요청을 전문 에이전트에게 자동 라우팅한다. 어떤 작업 요청이든 이 스킬을 사용하라. 재실행, 업데이트, 수정, 보완, 다시 해줘 요청도 이 스킬이 처리한다."
---

# Personal Assistant — 범용 개인 어시스턴트 오케스트레이터

planner-agent가 항상 먼저 실행 계획을 보고하고, 이후 6개 전문 에이전트(dev, content, data, research, design, github)가 작업을 처리한다.

## 실행 모드

**단일 도메인 요청** → 해당 에이전트만 서브 에이전트로 호출 (오버헤드 최소화)

**복합 도메인 요청** → 에이전트 팀 구성 후 협업

> 판단 기준: 2개 이상의 에이전트가 서로의 결과물을 참조해야 한다면 팀 모드, 독립적으로 처리 가능하면 서브 에이전트 모드.

## 에이전트 팀

| 에이전트 | 역할 |
|---------|------|
| `planner-agent` | **항상 첫 번째** — 모든 요청의 실행 계획을 분석·보고 |
| `dev-agent` | 코드 작성, UI 구현, 버그픽스, 아키텍처 설계 |
| `content-agent` | 글쓰기, 번역, 편집, 기획서, 이메일, SNS |
| `data-agent` | CSV/Excel 분석, 통계, 시각화, 리포트 |
| `research-agent` | 웹 검색, 정보 수집, 팩트체크, 트렌드 분석 |
| `design-agent` | UX 기획, 와이어프레임, 시각 디자인, 이미지 생성, Figma |
| `github-agent` | GitHub 업로드, 커밋 메시지 작성, 푸시, 오류 해결 |

## 워크플로우

### Phase 0: 컨텍스트 확인

시작 전 기존 작업 여부를 확인한다:

- `_workspace/` 존재 + 부분 수정 요청 → **부분 재실행** (해당 에이전트만 재호출)
- `_workspace/` 존재 + 새 입력 제공 → **새 실행** (기존을 `_workspace_prev/`로 이동)
- `_workspace/` 미존재 → **초기 실행**

### Phase 1: 실행 계획 보고 (planner-agent)

모든 요청에서 planner-agent를 먼저 호출하여 실행 계획을 사용자에게 보고한다.

```
Agent(
  agent_file: ".claude/agents/planner-agent.md",
  prompt: [사용자 원본 요청 전문],
  model: "opus"
)
```

planner-agent는 실행 계획 보고서를 출력한다. 이후 실행은 Claude 모드에 따라 분기:
- **자동 승인 모드**: 보고 직후 Phase 2로 자동 진행
- **일반 모드**: 보고 후 사용자 응답을 기다린 뒤 Phase 2 진행

### Phase 2: 요청 분석 및 라우팅

요청을 분석하여 담당 에이전트와 실행 모드를 결정한다.

**단일 에이전트 라우팅 기준:**

| 요청 유형 | 담당 에이전트 |
|---------|------------|
| 코드 작성, 버그 수정, UI 구현, 앱 개발 | `dev-agent` |
| 글쓰기, 번역, 편집, 기획서, 이메일, SNS | `content-agent` |
| 데이터 파일 분석, 통계, 차트, 리포트 | `data-agent` |
| 웹 검색, 정보 조사, 팩트체크 | `research-agent` |
| UX 기획, 와이어프레임, 디자인, 이미지 생성, Figma | `design-agent` |
| GitHub 업로드, 커밋, 푸시, 레포 생성 | `github-agent` |

**팀 모드 트리거 예시:**
- "경쟁사 조사 후 분석 리포트 작성" → research + data + content
- "데이터 분석 결과를 대시보드로 구현" → data + dev
- "시장 조사 기반 블로그 포스트 작성" → research + content
- "앱 디자인하고 구현해줘" → design + dev
- "경쟁사 앱 조사 후 디자인 기획해줘" → research + design
- "코드 짜고 GitHub에 올려줘" → dev + github
- "작업 완료 후 GitHub 푸시해줘" → github (단독)

### Phase 2: 실행

**서브 에이전트 모드 (단일 도메인):**

```
Agent(
  agent_file: ".claude/agents/{agent-name}.md",
  prompt: [요청 내용 + 컨텍스트],
  model: "opus"
)
```

**에이전트 팀 모드 (복합 도메인):**

1. 각 에이전트를 `run_in_background: true`로 병렬 호출 (독립 작업인 경우)
2. 또는 의존 관계가 있으면 순차 호출 (예: research 완료 후 content 시작)
3. 결과를 `_workspace/` 에 저장
4. 최종 통합 산출물 생성

**데이터 전달:**
- 에이전트 간 중간 산출물: `_workspace/{phase}_{agent}_{artifact}.{ext}`
- 최종 산출물: 사용자 요청 경로 또는 대화로 직접 전달

### Phase 3: 결과 전달

- 산출물을 사용자에게 직접 전달하거나 파일 경로 안내
- 후속 작업 필요 여부 확인
- 개선 피드백 수렴 (필요 시)

## 에러 핸들링

| 상황 | 처리 방침 |
|------|---------|
| 에이전트 실패 | 1회 재시도, 재실패 시 결과 없이 진행하고 누락 명시 |
| 도메인 불명확 | 가장 근접한 에이전트로 라우팅 후 처리 |
| 복합 요청 실패 | 각 에이전트 결과를 독립적으로 보존, 상충 시 출처 병기 |

## 테스트 시나리오

**정상 흐름 — 단일 도메인:**
```
요청: "Python으로 CSV 파일을 읽어서 평균값을 출력하는 코드 작성해줘"
→ dev-agent 단독 호출
→ 코드 파일 반환
```

**정상 흐름 — 복합 도메인:**
```
요청: "Claude 4 신기능을 조사하고 블로그 포스트로 써줘"
→ research-agent (조사) → content-agent (작성) 순차 실행
→ _workspace/research_claude4.md → _workspace/content_blog.md
→ 최종 블로그 포스트 반환
```

**에러 흐름:**
```
research-agent 검색 실패
→ 검색어 변형 후 재시도
→ 재실패 시 "검색 결과 없음" 명시하고 content-agent는 일반 지식 기반으로 진행
```
