# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal workspace at `/Users/ku/claude`. A multi-agent harness is configured for development, content, data analysis, and research tasks.

---

## 하네스: 범용 개인 어시스턴트

**목표:** 개발·콘텐츠·데이터·리서치·디자인·GitHub 6개 도메인의 전문 에이전트(+ 실행 계획 보고 에이전트)를 통해 모든 작업 요청을 자동으로 처리한다.

**트리거:** 어떤 작업 요청이든 `personal-assistant` 스킬을 사용하라. 단순 질문(설명, 개념 문의)은 직접 응답 가능.

**에이전트 팀:**
- `planner-agent` — 항상 첫 번째 실행, 실행 계획 보고
- `dev-agent` — 개발 (코드 작성, UI, 버그픽스)
- `content-agent` — 콘텐츠 (글쓰기, 번역, 편집)
- `data-agent` — 데이터 분석 (CSV, 통계, 리포트)
- `research-agent` — 리서치 (웹 검색, 정보 수집)
- `design-agent` — 디자인 (UX 기획, 와이어프레임, 이미지 생성, Figma)
- `github-agent` — GitHub (업로드, 커밋, 푸시, 레포 생성, 오류 해결)

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-27 | 초기 구성 | 전체 | 범용 개인 어시스턴트 하네스 신규 구축 |
| 2026-05-31 | 오케스트레이터 스킬 생성 | skills/personal-assistant | 누락된 오케스트레이터 스킬 추가 |
| 2026-05-31 | design-agent 추가 | agents/design-agent.md, skills/personal-assistant | 디자인 기획·설계·이미지 생성 기능 강화 |
| 2026-05-31 | planner-agent 추가 | agents/planner-agent.md, skills/personal-assistant | 모든 요청 전 실행 계획 보고 기능 추가 |
| 2026-05-31 | github-agent 추가 | agents/github-agent.md, skills/personal-assistant | GitHub 업로드/커밋/푸시/오류해결 자동화 |
| 2026-05-31 | github-agent 수정 | agents/github-agent.md | 레포 기본값 private으로 변경, visibility 변경 기능(Step 5) 추가 |
| 2026-05-31 | github-agent 수정 | agents/github-agent.md | README.md 없을 시 자동 생성 기능 추가 (기존/신규 모두) |
| 2026-05-31 | 하네스 점검 | CLAUDE.md, skills/personal-assistant | drift 3건 수정: description에 design/github 추가, 목표 설명 업데이트 |
