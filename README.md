# claude-harness

Claude Code 멀티 에이전트 하네스 설정 모음. 이 레포를 다른 컴퓨터에 클론하면 동일한 개인 어시스턴트 환경(에이전트 7개 + 오케스트레이터 스킬)을 그대로 사용할 수 있다.

## 구성

```
.claude/
├── agents/                 # 에이전트 정의 7개
│   ├── planner-agent.md     # 실행 계획 보고 (항상 먼저 실행)
│   ├── dev-agent.md         # 개발 (코드 작성/리뷰/테스트/버그픽스)
│   ├── content-agent.md     # 콘텐츠 (글쓰기/번역/편집)
│   ├── data-agent.md        # 데이터 분석 (CSV/통계/차트/리포트)
│   ├── research-agent.md    # 리서치 (웹 검색/정보 수집/팩트체크)
│   ├── design-agent.md      # 디자인 (UI/UX/와이어프레임/Figma)
│   └── github-agent.md      # GitHub (커밋/푸시/레포 생성)
└── skills/
    └── personal-assistant/  # 오케스트레이터 스킬 (요청 자동 라우팅)
CLAUDE.md                    # 프로젝트 가이드 (하네스 운영 규칙)
AGENTS.md                    # Codex용 가이드
```

## 에이전트

| 에이전트 | 역할 |
|----------|------|
| `planner-agent` | 작업 시작 전 누가·어떤 순서로·무엇을 할지 구조화된 계획을 먼저 보고 |
| `dev-agent` | 코드 작성, 리뷰, 테스트, 리팩토링, UI/UX 구현, 디버깅 |
| `content-agent` | 글쓰기, 편집, 번역, 블로그/기획서/이메일/SNS 콘텐츠 |
| `data-agent` | 데이터 수집·정제·분석·시각화, 통계, 리포트 생성 |
| `research-agent` | 웹 검색, 정보 수집, 문서 분석, 팩트체크, 트렌드 분석 |
| `design-agent` | UI/UX 기획, 와이어프레임, 시각 디자인, 이미지 생성, 디자인 시스템 |
| `github-agent` | 프로젝트 GitHub 업로드, 커밋 메시지 작성, 푸시, 오류 해결 |

오케스트레이터(`personal-assistant` 스킬)가 요청을 분석해 단일 도메인이면 해당 에이전트만, 복합 도메인이면 에이전트 팀을 구성해 처리한다.

## 다른 컴퓨터에서 설치

1. 워크스페이스 디렉토리에서 클론한다.

   ```bash
   git clone https://github.com/kth9107/claude-harness.git
   cd claude-harness
   ```

2. `.claude/agents/`와 `.claude/skills/`가 그대로 인식된다. 해당 디렉토리에서 Claude Code를 실행하면 에이전트와 스킬이 자동 로드된다.

3. 작업 요청을 하면 `personal-assistant` 스킬이 적절한 에이전트로 자동 라우팅한다.

## 제외 항목

- `.claude/settings.local.json` — 로컬 머신 전용 경로 권한 설정이므로 버전 관리에서 제외된다. 새 머신에서는 그 머신에 맞게 새로 생성하면 된다.
- `_workspace/` — 테스트용 별도 git repo.
