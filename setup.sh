#!/usr/bin/env bash
# claude-harness 환경 설치 스크립트
# 새 컴퓨터에서: bash setup.sh

set -e

echo "=== Claude Code 환경 설치 시작 ==="

# ── 1. 마켓플레이스 등록 ───────────────────────────────────────────────
echo "[1/4] 마켓플레이스 등록..."

claude plugin marketplace add anthropics/claude-plugins-official 2>/dev/null || true
claude plugin marketplace add revfactory/harness 2>/dev/null || true
claude plugin marketplace add forrestchang/andrej-karpathy-skills 2>/dev/null || true
claude plugin marketplace add bradautomates/claude-video 2>/dev/null || true
claude plugin marketplace add Lum1104/Understand-Anything 2>/dev/null || true

echo "  마켓플레이스 등록 완료"

# ── 2. 플러그인 설치 ───────────────────────────────────────────────────
echo "[2/4] 플러그인 설치..."

claude plugin install firecrawl@claude-plugins-official
claude plugin install skill-creator@claude-plugins-official
claude plugin install figma@claude-plugins-official
claude plugin install superpowers@claude-plugins-official
claude plugin install harness@harness-marketplace
claude plugin install andrej-karpathy-skills@karpathy-skills
claude plugin install watch@claude-video
claude plugin install understand-anything@understand-anything

echo "  플러그인 설치 완료"

# ── 3. agentmemory 설치 ────────────────────────────────────────────────
echo "[3/4] agentmemory 설치..."

# agentmemory worker 설치 및 Claude Code 연결
npx @agentmemory/agentmemory connect claude-code

# agentmemory 스킬 8개 설치
npx skills add rohitg00/agentmemory -y

echo "  agentmemory 설치 완료"

# ── 4. codegraph 설치 ─────────────────────────────────────────────────
echo "[4/4] codegraph 설치..."

if ! command -v codegraph &>/dev/null; then
  echo "  codegraph 바이너리가 없습니다."
  echo "  설치: https://github.com/adrianliechti/codegraph#installation"
  echo "  또는: brew install adrianliechti/tap/codegraph"
else
  echo "  codegraph 이미 설치됨: $(codegraph --version 2>/dev/null || echo 'version unknown')"
fi

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "다음 단계:"
echo "  1. Claude Code 재시작 후 /reload-plugins 실행"
echo "  2. agentmemory 시작: npx @agentmemory/agentmemory"
echo "  3. (선택) API 키 설정: npx @agentmemory/agentmemory init"
echo "     → ~/.agentmemory/.env 에 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 추가"
echo "  4. codegraph 미설치 시 위 링크 참고하여 설치"
