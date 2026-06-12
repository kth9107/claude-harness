# claude-harness

Claude Code 멀티 에이전트 하네스. 이 레포를 클론하면 동일한 개인 어시스턴트 환경을 그대로 사용할 수 있다.

---

## 에이전트 구조

```
사용자 요청
    ↓
router-agent (sonnet)        도메인 분류 + 모델 배정
    ↓
planner-agent (opus)         실행 순서·병렬 여부 계획 보고
    ↓
┌──────────────────────────────────────────────────────────┐
│ 상위 에이전트 — 병렬 실행 가능                              │
├──────────────┬───────────────┬──────────────┬────────────┤
│ dev-agent    │ frontend-agent│ backend-agent│ api-agent  │
│ content-agent│ data-agent    │ design-agent │            │
│ security-agent│ github-agent │              │            │
└──────────────┴───────┬───────┴──────────────┴────────────┘
                       │ (내부 선행 호출)
                  research-agent
                  └ design-agent, content-agent가 필요 시 호출
    ↓
test-agent                   Phase A: 각 에이전트 완료 즉시 단위 테스트
                             Phase B: 전체 완료 후 통합 테스트
    ↓ (Phase B PASS 시만)
optimizer-agent              성능·품질 문제 식별 → P0/P1 개선 → Phase B 재실행(1회)
    ↓
deploy-agent                 배포 실행 → 헬스체크 → 실패 시 자동 롤백
```

---

## 프로세스 타입

| 타입 | 설명 | 사용 예 |
|------|------|---------|
| **General chat** | 단순 질문 → 직접 응답 (에이전트 없음) | "OSM이 뭐야?" |
| **Skill** | 스킬 호출 → 전문 처리 | personal-assistant 라우팅 |
| **Subagent** | Coordinator → 전문 에이전트 → 결과 합산 | 기능 추가 + 보안 검토 동시 |
| **Batch** | 독립 작업 목록 → 병렬 에이전트 → 개별 결과 | 여러 파일 분석 |
| **Deep Research** | plan → search → verify → report | 기술 조사, 경쟁사 분석 |
| **Goal** | plan → build → review → refine → complete | 전체 기능 개발 파이프라인 |

---

## 에이전트 역할

| 에이전트 | 모델 | 역할 |
|----------|------|------|
| `router-agent` | sonnet | 도메인 분류, 모델 배정, 실행 순서 결정 |
| `planner-agent` | opus | 실행 계획 보고 (누가·어떤 순서로·무엇을) |
| `dev-agent` | sonnet | 범용 개발 (코드 작성, 버그픽스, 아키텍처) |
| `frontend-agent` | sonnet | UI 컴포넌트, 상태 관리, 반응형, 성능, 접근성 |
| `backend-agent` | sonnet | 서버 로직, DB 모델링, 인증, 캐싱, 인프라 |
| `api-agent` | sonnet | REST/GraphQL 설계, OpenAPI 명세, 버전 관리 |
| `content-agent` | sonnet | 글쓰기, 편집, 번역, 기획서, SNS 콘텐츠 |
| `data-agent` | sonnet | 데이터 분석, CSV/통계, 시각화, 리포트 |
| `design-agent` | opus | UX 기획, 와이어프레임, 이미지 생성, Figma |
| `security-agent` | sonnet | 보안 감사, CVE 스캔, 서버 하드닝, 인시던트 대응 |
| `github-agent` | sonnet | 커밋, 푸시, 레포 생성, 오류 해결 |
| `research-agent` | sonnet | 웹 검색, 정보 수집, 팩트체크 (서브 에이전트) |
| `test-agent` | sonnet | Phase A 단위 테스트 + Phase B 통합 테스트 |
| `optimizer-agent` | opus | 테스트 결과 기반 성능·품질 개선 |
| `deploy-agent` | sonnet | 배포, 헬스체크, 롤백 |

---

## 실행 흐름 예시

```
# 단순 작업: "Next.js에 기능 추가 후 배포"
router → frontend(sonnet) → test PhaseA → optimizer → deploy

# 병렬: "프론트엔드 + 백엔드 동시 구현 후 배포"
router → frontend(sonnet) + backend(sonnet) [병렬]
       → test PhaseA 각각 → test PhaseB → optimizer → deploy

# 순차: "앱 디자인 후 구현, 배포"
router → design(opus) [내부에서 research 선행] → frontend(sonnet)
       → test PhaseA×2 → test PhaseB → optimizer → deploy

# 보안 포함: "API 장애 분석 + 보안 영향 확인"
router → backend(sonnet) + security(sonnet) [병렬]
       → test PhaseA 각각 → test PhaseB
```

---

## 하네스 운영 (graph + audit + feedback + cleanup)

하네스는 선언형 파일만으로 유지하지 않고 4가지 루프로 관리한다.

```bash
# 1. 감사: 파일 ↔ 그래프 일치 확인
python3 scripts/harness_audit.py --root /Users/ku/claude

# 2. 피드백 기록: 반복 실패 패턴 집계
python3 scripts/harness_feedback.py --root /Users/ku/claude --agent <agent> --summary "<내용>"

# 3. 리포트: 유지/비활성화 후보/삭제 후보 분류
python3 scripts/harness_report.py --root /Users/ku/claude
```

플러그인·스킬 삭제는 자동 실행하지 않는다. 리포트 확인 후 사용자 승인 시에만 실행:
```bash
claude plugin uninstall <plugin-id>
```

---

## Claude 하네스 vs Hermes 역할 경계

| 역할 | Claude 하네스 | Hermes |
|------|-------------|--------|
| 실행 트리거 | 사용자 대화 요청 | cron, 이벤트, 자율 루틴 |
| 오케스트레이션 | router→planner→agents 체인 | agent/ + batch_runner.py |
| 메모리 | agentmemory (세션 간 지속) | memory/ (장기 기억) |
| IT 개발 | 코드 작성/테스트/배포 파이프라인 | 시장 데이터, 자동화 루틴 |

**원칙:** 코드 작성·리뷰·배포 → Claude 하네스 / 장기 모니터링·스케줄 자동화 → Hermes

---

## 다른 컴퓨터에서 설치

```bash
git clone https://github.com/kth9107/claude-harness.git
cd claude-harness
bash setup.sh
```

설치 후 Claude Code 재시작 → `/reload-plugins`

---

## 파일 구조

```
.claude/
├── agents/          에이전트 정의 15개
├── skills/          스킬 9개 (personal-assistant + 심볼릭 링크 8개)
└── harness/
    ├── harness.graph.json   35 node / 27 edge 그래프
    ├── schema.json          그래프 유효성 검증
    └── state/               감사·피드백·리포트 런타임 산출물
scripts/
├── harness_audit.py
├── harness_feedback.py
└── harness_report.py
tests/
└── test_harness_tools.py
```
