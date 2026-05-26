# ResearchPartner × Claude Code 교훈 — 통합 반영 계획 (Unified Implementation Plan)

> **Canonical docs copy**: this is the promoted implementation plan under `docs/harness/`.
> The review drafts under `References/claude-code-review/` remain source inputs; implementation work should track this file unless it is explicitly superseded.

- **통합 출처**:
  - Claude: `claude-code/claude_code_lessons.md`, `claude-code/implementation_plan.md` (근거 기반·정정)
  - Codex: `codex/claude_code_lessons.md`, `codex/researchpartner_adoption_plan.md` (Checkpoint·검증)
- **통합일**: 2026-05-26
- **운영 모드**: `maintenance` (harness 자체 정비 — research gate는 기록만, 과학 claim 무관)
- **대상 저장소**: `C:\ResearchPartner` (harness 소스 본체)

이 문서는 두 독립 계획을 합친 **단일 실행 기준**이다. 골격은 Codex의 **Checkpoint(=PR 단위)** 를 쓰고,
여기에 Claude 측의 **코드 검증 사실(§3)·상세 작업 카드·핵심 정정(spawn tools 강제 메커니즘)** 을 통합했다.
두 계획이 독립 수렴한 항목은 고신뢰로 간주한다. 이 문서가 두 하위 계획을 대체한다.

---

## 0. 핵심 통찰

- (Codex) 문제는 *기능 부족*이 아니라 **강한 부품들 사이의 연결 drift**다. 목표는 자동화 추가가 아니라
  기능(skill·gate·checker·workflow·test·docs)을 *검증 가능한 contract*로 묶는 것.
- (양쪽 합의) **표면화 ↔ 차단 분리**: 과학적 hard 차단은 deterministic checker만 담당. prompt-based hook은
  soft 경고/리뷰어 질문까지(차단권 없음).
- (Claude 정정) subagent 권한은 *문서 계약*만으로 강제되지 않는다. 런타임 강제는
  **agent 정의(`tools:`) + `subagent_type` 스폰**이 필요하고, JSON 계약은 *정합검사* 역할이다(§7).

---

## 1. 적용 원칙

1. 문서만 추가하지 않는다 — 중요한 규칙은 checker / evaluator / fixture / workflow artifact 중 하나로 검증 가능해야 한다.
2. hard 과학 게이트는 deterministic script가 담당. prompt hook은 soft detector / researcher decision까지만.
3. 새 feature는 `README.md` + `README.ko.md`에 함께 반영.
4. `AGENTS.md` 수정 시 `GEMINI.md`를 byte-identical로 동기화(`check_contract_sync.py`).
5. vertical slice로 시작(Orient / Interview / Claim Promotion / Sync Workflow 먼저), 통과 후 확장.
6. subagent 권한 = prompt 신뢰가 아니라 `tools:` / scope contract. **단, 실제 강제는 agent 정의로 한다(§7).**
7. claim promotion 전 Lead가 subagent 요약이 아니라 인용 artifact 경로를 **직접** 확인하고, checker가 이를 강제(§8).
8. **hook 계층(L7)**: PreToolUse엔 *싼 hard 차단*만; lineage-coverage·manifest-completeness·spawn-log-reconciliation 같은
   무거운 cross-cutting 검사는 Stage Checkpoint/CI(§11B)로. slow path는 prompt-block이 아니라 deterministic.

---

## 2. 비목표

- Claude Code marketplace plugin으로 **즉시 패키징하지 않는다**(내부 레이아웃 정렬만 — §12).
- prompt-based hook을 과학 hard gate로 승격하지 않는다.
- researcher judgment를 건너뛰는 full auto runner를 만들지 않는다.
- `References/` 리뷰 문서를 public project docs처럼 다루지 않는다.
- 모든 skill을 한 번에 재구성하지 않는다.

---

## 3. 실행 전 확정 사실 — 코드 직접 검증 ★

(이 절은 Claude 측 계획의 고유 grounding. Codex 계획엔 없던 코드 검증 사실로, 잘못된 전제를 미리 제거한다.)

1. **harness `scripts/*.py` 편집은 cross-tier hook에 안 걸린다.** `check_src_write_authorization.py`의
   `find_run_root()`는 `ResearchPartner-runs/<run>/` 경로 세그먼트가 있을 때만 발동 → harness 루트의
   `scripts/`·`docs/`는 대상 아님. **Lead가 직접 편집 가능**(Implementation Agent 스폰 불필요).
2. **이 repo 루트에 `.research-harness` marker 존재.** 따라서 `Agent()` 스폰은 `enforce_gate_sequence.py` /
   `workflow_hooks.py pre` / `check_peer_review_invocation.py`를 거친다(harness-dev엔 스폰이 보통 불필요).
3. **`AGENTS.md` 편집은 `path_check_hooks.py pre → check_contract_sync`로 차단**됨 → `GEMINI.md` 동시 수정 필수.
4. **우리 spawn 역할은 agent 정의가 아니라 skill이다.** `graduate-student`/`scientific-validator`/
   `implementation-agent`/`cache-log-auditor`/`peer-review-professor`는 `skills/<role>/SKILL.md` + prose 스폰.
   `.claude/agents/`에 역할 정의 없음(`.agents/workflows/*`는 slash-command 등록). → `tools:` 강제는
   정의 파일 신설이 필요(§7). **Codex의 spawn_contracts.json만으론 런타임 강제가 안 됨.**
5. **`init_research_project.py` hook 등록은 `_CLAUDE_SETTINGS_CONTENT` 단일 리터럴(line 115–172).**
   12개 command 전부 상대경로 `python scripts/…`. → 한 곳 수정으로 신규 프로젝트 전체 반영(§6).
6. **`evaluate_harness.py`는 시나리오/존재검사 기반** → manifest 교차링크 검증은 별도 스크립트가 적합(§6).

---

## 4. Checkpoint ↔ lessons 매핑 개요

| CP | 내용 | lessons § | PR | 규모 |
|----|------|-----------|----|------|
| 0 | 베이스라인·브랜치·재개성 + 선결질문(subagent_type) | — | (선행) | S |
| 1 | capability manifest + 최소 hook registry + **hook 경로 이식성 fix** | §8·§3.5·§3.1 | PR1 (P0) | L |
| 2 | hook registry 확장 + spawn contracts(**agent정의=강제 / JSON=검사**) | §3.5·§4.1 | PR2 | M |
| 3 | finding lifecycle 2-pass + **Lead 직접읽기 강제** | §4.2·§4.5 | PR3 | M |
| 4 | skill metadata linter + operating profiles | §2.2·§2.3·§8 | PR4 | M |
| 5 | safe wrappers + gate example fixtures | §8·§2.3 | PR5 | M |
| 6 | doc sync(+ **AGENTS.md 슬림화**) + full validation | §2.1 | PR6 | M |
| 7 | CI: PR마다 deterministic checker (M-2 보완, 대체 아님) | §11B(L5) | PR7 | M |
| 12 | 후순위: prompt-hook soft, research-rule DSL, loop promise, plugin layout, CHANGELOG, L1·L3·L9·L11·L13; **L12 incident log = P1** | §3.2·§6·§7·§9·§12(L1·L3·L9·L11·L12·L13) | 선택(L12 제외) | — |

**모든 CP 착수 전 §5 Checkpoint 0를 1회 수행한다.**

---

## 5. Checkpoint 0 — 베이스라인·안전 (+ 선결질문)

**읽기**: `docs/orchestration_protocol.md`, `docs/hooks_reference.md`, `scripts/evaluate_harness.py`,
`scripts/check_contract_sync.py`, 4개 출처 문서.

**단계**
- [x] 진행 중 연구 task가 harness 정비와 섞이지 않는지 확인(maintenance 모드 선언). (2026-05-26: harness maintenance로 분리)
- [x] 브랜치 분기(예: `harness/claude-code-lessons-adoption`). (2026-05-26: `codex/claude-code-plan-promotion`)
- [x] 세션·연산 재개성 점검 → in-flight 스폰 / blocked gate 없음 확인(있으면 *명시 문서화* 후 착수).
- [x] 현재 테스트 베이스라인 기록.
- [x] **선결질문(blocker)**: 우리 `Agent()` 스폰이 `subagent_type`을 지정할 수 있는가? → §7(tools 강제)의 전제.
  불가하면 §7 범위가 "agent 정의 + 스폰 호출 변경"까지 커진다.

**CP0 결과(2026-05-26)**: `check_session_resumable.py`는 in-flight task 0 / blocking gate 0, `check_computation_resumable.py`는 checkpoint 없음,
`check_contract_sync.py` 통과, `pytest tests/test_check_contract_sync.py tests/test_evaluate_harness.py -q`는 14 passed.
루트 `scripts/workflow_hooks.py`와 `scripts/check_peer_review_invocation.py`가 이미 `tool_input["subagent_type"]`을 읽으므로 PR2 전제는 지원됨으로 기록한다.

```powershell
python scripts/check_session_resumable.py --project C:\ResearchPartner
python scripts/check_computation_resumable.py --project C:\ResearchPartner
python scripts/check_contract_sync.py
python -m pytest tests/test_check_contract_sync.py tests/test_evaluate_harness.py -q
```

**수용 기준**: 재개성 점검이 in-flight·blocking 없음 보고(또는 명시 문서화), contract sync 통과,
기존 평가 테스트가 *변경 전* 통과, subagent_type 지원 여부 확정.
**실패 처리**: contract sync 실패 → AGENTS/GEMINI drift 우선 수정. 베이스라인 테스트 실패 → 먼저 분류, CP1에 무관 수정 섞지 않기.

---

## 6. Checkpoint 1 — Capability Manifest + 최소 Hook Registry + hook 경로 이식성 fix  [PR1, P0]

> 두 계획 공통 1순위. 단순 문서가 아니라, 첫 PR에서 **최소 hard-hook registry까지 checker로 검증**하고,
> **실제 hook 경로 이식성 fix**(Claude P1-A)를 함께 출하해 registry 메타와 실물을 일치시킨다.

**파일**
- Create: `docs/harness/capability_manifest.json`, `docs/harness/hook_registry.md`,
  `scripts/check_harness_manifest.py`, `tests/test_check_harness_manifest.py`
- Modify: `scripts/init_research_project.py`(`_CLAUDE_SETTINGS_CONTENT` 경로 fix), 이 repo `.claude/settings.local.json`(동기화),
  `scripts/evaluate_harness.py`, `docs/harness/harness_evaluation_scenarios.md`, `docs/hooks_reference.md`,
  `README.md`, `README.ko.md`

**(a) 실제 hook 경로 이식성 fix (Claude §3.1)** — `_CLAUDE_SETTINGS_CONTENT`의 12개 command를
`python scripts/…` → `python "$CLAUDE_PROJECT_DIR/scripts/…"`. Claude Code가 셸 무관하게 치환. 이미 깔린 프로젝트는 재init/수동.

**(b) manifest v0 (8 게이트)**: `orient / interview / literature / model / baseline-strategy / baseline /
claim-promotion / workflow-sync`. **(c) 최소 hard-hook registry**: `cross-tier-write / bash-code-write /
claim-promotion / workflow-sync`. 단, v0는 "전체 계약 완성"이 아니라 "검증 가능한 vertical slice"다. 최종 목표는
`.claude/settings.local.json`에 wired된 모든 hook과 AGENTS/GEMINI의 gate script를 manifest/registry에 역방향으로 포착하는 것이다.

```json
{ "schema_version": 1,
  "capabilities": [
    { "id": "interview-gate", "stage": "Interview", "kind": "gate",
      "skill": "skills/professor-interview/SKILL.md",
      "artifact": "docs/gates/interview_notes.md",
      "checker": "scripts/check_interview_recorded.py",
      "workflow_gate_keys": ["interview_gate"],
      "tests": ["tests/test_evaluate_harness.py"],
      "user_docs": ["README.md","README.ko.md","docs/hooks_reference.md"],
      "claim_ceiling_effect": "blocks Seed/Execute when missing",
      "waiver": null, "hooks": ["interview-gate-status"] } ],
  "hooks": [
    { "hook_id": "cross-tier-write", "class": "hard",
      "script": "scripts/check_src_write_authorization.py",
      "path_base": "CLAUDE_PROJECT_DIR", "interpreter": "python",
      "windows_supported": true, "posix_supported": true,
      "startup_validation": "script_exists_and_imports",
      "tests": ["tests/test_enforcement_hooks.py"] } ] }
```

**checker(`check_harness_manifest.py`) fail 조건**: skill/artifact/checker 경로 없음(artifact는 template/created_by 없을 때만);
checker에 test 없음; test 파일 없음; `workflow_gate_keys`가 실제 workflow gate key(`interview_gate` 등)와 불일치;
waiver 가능 capability에 claim_ceiling_effect 없음; **hard hook에 script/test/path_base/interpreter/startup_validation 누락**;
**prompt/heuristic hook이 deterministic checker 없이 `hard`로 표기**; hook script 경로가 project-relative 아님(=경로 fix 검사); 중복 id.
warn: 내부 전용 capability의 user_docs 불완전; live JSON 미생성.

`startup_validation` 값은 script 성격과 맞아야 한다. `argparse --help`를 제공하는 CLI형 script는
`script_exists_and_runs_help`를 쓸 수 있지만, `check_src_write_authorization.py`처럼 hook stdin을 전제로 하는 script는
`script_exists_and_imports` 또는 별도 `--self-test` 추가 후 `script_runs_self_test`를 사용한다. PR1은 이 값을 실제 script 동작과 맞추는 것을 포함한다.

workflow 검사는 literal Cytoscape node id가 아니라 gate key 기준으로 한다. `generate_workflow_map.py`는 `interview_gate` 같은 key와
`gate_id or f"gate_{index}"` 형태의 node id를 분리하므로, manifest가 `gate_interview` 같은 추정 id를 쓰면 spurious fail이 난다.

Wired hook 역방향 검사: PR1에서는 `known_uncovered_wired_hooks`를 허용하되, `.claude/settings.local.json`에 wired된 hook이
registry에도 `known_uncovered_wired_hooks`에도 없으면 fail한다. 최종 DoD에서는 `known_uncovered_wired_hooks`가 비어야 한다.

(주의: active live workflow JSON은 **루트 `workflow_map.live.json`** 기준. `docs/workflow_map.live.json`이 있더라도 stale/template 성격일 수 있으므로 checker는 source를 명시해야 한다.)

**테스트(named + `tmp_path`, 실제 repo 비의존)**: `test_manifest_accepts_canonical_gate_slice` /
`test_missing_checker_fails` / `test_missing_test_file_fails` / `test_duplicate_capability_id_fails` /
`test_waiver_without_claim_ceiling_effect_fails` / `test_hard_hook_without_test_fails` /
`test_hard_hook_without_path_or_interpreter_metadata_fails` /
`test_workflow_gate_key_uses_real_key_not_node_id` /
`test_wired_hook_missing_from_registry_or_known_uncovered_fails`. 각 테스트는 `tmp_path`에 최소 트리 구성.

```powershell
python scripts/check_harness_manifest.py --project C:\ResearchPartner
python -m pytest tests/test_check_harness_manifest.py tests/test_enforcement_hooks.py tests/test_install_harness.py -q
python scripts/evaluate_harness.py --fail-on-partial
python scripts/check_contract_sync.py
```

**수용 기준**: 의도적 malformed fixture(checker만/test 없음/README엔 있고 manifest엔 없음/workflow node 누락/hard hook 메타 누락)는 모두 fail,
canonical slice는 pass. evaluate_harness에 manifest drift 시나리오 포함. README/README.ko에 "manifest = harness 계약 checker" 명시.
`tests/test_install_harness.py`에는 clean init 후 generated `.claude/settings.local.json`의 hook command가
`$CLAUDE_PROJECT_DIR` 기반인지 확인하는 regression을 추가한다.
**위험/롤백**: manifest 자체가 stale 되지 않도록 *양방향 검증*(실물↔manifest). 경로 fix는 변경 후 hook 1회 실발동 확인.
이미 설치된 외부 프로젝트는 "재init/수동"만으로 끝내지 말고, release note 또는 refresh 절차에서
기존 `.claude/settings.local.json`을 어떻게 갱신할지 명시한다.

**CP1 결과(2026-05-26)**: `capability_manifest.json`, readable `hook_registry.md`, `check_harness_manifest.py`,
hook path fix, current `.claude/settings.local.json` sync, README/README.ko, AGENTS/GEMINI, hooks reference, evaluator scenario,
and regression tests were implemented. `check_harness_manifest.py --project C:\ResearchPartner`, `check_contract_sync.py`,
and `pytest tests -q` pass. `evaluate_harness.py` passes in normal mode and the new `capability_manifest_and_hook_registry`
scenario passes; `--fail-on-partial` still fails on pre-existing partial scenarios outside CP1 scope.
Manager review follow-up: the evaluator scenario now calls `check_harness_manifest.validate_project()` directly rather than only checking file/keyword presence.
In PR1 this is a local deterministic gate through pytest/evaluator; PR-by-PR automatic enforcement belongs to CP7 CI (`harness-checks.yml`).

---

## 7. Checkpoint 2 — Hook Registry 확장 + Spawn Contracts  [PR2]

### 7.1 Hook Registry (4분류)

| class | 의미 | 허용 행동 |
|---|---|---|
| `hard` | deterministic 강제 | non-zero exit로 차단 |
| `soft` | prompt/heuristic 경고 | 리뷰어 질문/`ask`, claim을 조용히 승격·차단 금지 |
| `meeting_recommendation` | 논의 필요 표시 | meeting 제안 + 사유 기록 |
| `workflow_helper` | 상태 갱신 | sync/checkpoint/log만 |

정책: hard 과학 게이트는 script만. prompt hook은 `soft` 등으로만, claim "supported" 표기 불가.
waiver 가능 hook은 waiver artifact + claim-ceiling 강등 경로가 선언될 때만 `permissionDecision:"ask"`.

### 7.2 Spawn Contracts — ★ 핵심 통합 (강제 + 검사)

> 두 계획의 단 하나의 정면 차이를 여기서 해소한다. **강제는 agent 정의, 검사는 JSON 계약 — 둘 다 둔다.**

**(런타임 격리) leaf agent 정의 (Claude §4.1 정정)** — `.claude/agents/<role>.md` 신설 + `tools:` frontmatter + `subagent_type` 스폰.
본문은 기존 skill 위임("Load skills/<role>/SKILL.md"). Claude Code의 문서화된 agent frontmatter 기능과 Lead/Manager의 라이브 관측을
런타임 격리 근거로 둔다. 우리 repo의 오프라인 작업은 이 기능을 호출해 실연하지 않고, 아래 JSON/checker로 정합성만 결정론적으로 검사한다.
**2026-05-26 정정**: spawned subagent는 `Agent` tool을 받지 못하므로 중첩 스폰은 불가. Lead Agent가 유일 스포너이고,
Graduate Student는 Lead가 seed task마다 로드하는 역할이다. `.claude/agents/graduate-student.md`는 두지 않는다.
권장 tools:

| 역할 | tools | 효과 |
|---|---|---|
| Scientific Validator | `Read, Grep, Glob, Bash` | Write/Edit 없음 → 코드 수정 *불가* |
| Cache-Log Auditor | `Read, Grep, Glob, Bash` | 단일 audit 명령만 |
| Implementation Agent | `Read, Write, Edit, Grep, Glob` | code/figure file 작성만; 실행은 validator handoff |
| Peer-Review Professor | `Read, Grep, Glob` | 읽기 전용 |

**계층 정리(§5 정정)**: `subagent_type` → `.claude/agents/<name>.md` 바인딩과 `tools:` 적용은 타깃 Claude Code 런타임의 속성이다.
로컬 `claude -p` smoke는 이 harness PR의 선결이 아니다. 남은 실연은 Manager/Lead가 별도 라이브 spawn으로 확인하며 PR2의 오프라인
정합성 구현을 막지 않는다.
추가 선결: `.claude/agents/`의 `description`이 오케스트레이션 밖 자동 호출을 유발하지 않는지 확인한다. 해결책은
description을 "Explicitly spawned only"로 시작하고 자동 trigger 예시를 제거하는 것이다.
`check_spawn_contracts.py`는 각 역할 description에 명시 스폰 전용 문구가 있는지 검사한다.

**(생성, L2) agent 정의 작성 — Claude Code 메타프롬프트 차용** — `.claude/agents/*.md`를 손으로 산발 작성하지 않고,
`agent-development/references/agent-creation-system-prompt.md`의 6단계 규칙(intent→persona→instructions→
self-verification/fallback→identifier→트리거 예시)으로 일관 생성한다. 특히 **"리뷰 agent는 *최근/현재 범위*만
가정(전체 코드베이스 X)"** 규칙을 Scientific Validator에 적용(해당 task 산출물만 검증). **단, 생성 결과를 신뢰하지
않는다** — 아래 `check_spawn_contracts.py`가 `allowed_tools`·`write_scope`·명시-스폰-전용 description을 *재검증*해야 통과(생성은 편의, 강제는 checker).

**(정합성 검사) `spawn_contracts.json` + `scripts/check_spawn_contracts.py` (Codex)** — 정의가 무엇을 선언하는지 기계검사·drift 방지.
실시간 도구 차단은 agent-file `tools:`의 런타임 속성이고, `spawn_contracts`는 오프라인/CI 정합성 게이트다.

```json
{ "schema_version": 1, "contracts": [
  { "role": "implementation-agent",
    "allowed_tools": ["Read","Write","Edit","Grep","Glob"],
    "forbidden_tools": ["WebSearch","WebFetch","Bash","Agent"],
    "write_scope": ["src/","outputs/figures/"],
    "must_report": ["changed_files","validation_commands","evidence_paths"],
    "validator_handoff_required": true,
    "completion_promise": ["증거 파일이 실재하지 않으면 완료 선언 금지",
                           "검증 미실행 시 'not run'으로 보고하고 claim은 provisional 유지"] } ] }
```

checker fail: 필수 leaf role 누락; agent file 부재; `name`이 `subagent_type`과 불일치; frontmatter `tools`와 JSON `allowed_tools` 불일치;
role agent가 `Agent` tool을 포함; child spawn 목록이 비어 있지 않음; `.claude/agents/graduate-student.md`가 존재;
description이 `Explicitly spawned only`로 시작하지 않거나 trigger 문구를 포함; `orchestration_protocol.md`가 명명한 leaf `subagent_type`이 빠짐.

```powershell
python scripts/check_spawn_contracts.py --project C:\ResearchPartner
python -m pytest tests/test_check_spawn_contracts.py -q   # check_cross_tier_compliance.py 수정 시 tests/test_check_cross_tier_compliance.py 신설 후 함께 실행
python scripts/check_cross_tier_compliance.py --project C:\ResearchPartner --strict
```

**수용 기준**: Lead만 `Agent`를 사용한다; leaf role agent는 모두 `Agent` tool이 없다; Scientific Validator 스폰이 코드 수정을
*수단 부재*로 못 함; 역할별 tool/scope가 실제로 다름; Implementation Agent는 Validator handoff로만 완료; completion_promise가
증거 없는 "완료" 차단.

---

## 8. Checkpoint 3 — Finding Lifecycle 2-pass + Lead 직접읽기 강제  [PR3]

> 과학 claim 거동을 바꾸므로 **격리 PR + 신중 리뷰**.

**파일**: Create `docs/harness/finding_lifecycle.md`, `docs/run_templates/finding_lifecycle_template.md`;
Modify `skills/{claim-to-evidence,anomaly-debugging,peer-review-professor,scientific-verification-before-claim}/SKILL.md`,
`scripts/check_claim_promotion.py`, `scripts/check_claim_promotion_freshness.py`; **create** `tests/test_check_claim_promotion.py`
and `tests/test_check_claim_promotion_freshness.py` if absent.

**finding 상태**: `candidate → independently_checked → validated_blocker / validated_limitation /
false_alarm / needs_researcher_judgment / evidence_linked / researcher_reviewed`.

**최소 finding 포맷**:

```markdown
## Finding
Status: candidate
Claim affected: <claim_id>
Evidence paths:
- docs/gates/validation_log.md
## Independent Check
Checker: scientific-validator     # 읽기전용(§7)
Result: independently_checked
## Evidence Paths Read Directly
- docs/gates/validation_log.md
## Decision
Decision: needs_researcher_judgment
Claim ceiling effect: no promotion beyond interpretation
```

**두 enforcement 층을 구분한다.**

- `check_claim_promotion.py`: agent/Lead가 mechanism/generalization으로 올리려 할 때 명시적으로 실행하는 promotion gate.
- `check_claim_promotion_freshness.py`: 현재 wired된 docs/claims write freshness hook 경로. `path_check_hooks.py`가 `docs/claims/*.md` write에서 발동한다.

따라서 finding-state 강제는 `check_claim_promotion.py`에만 넣으면 부족하다. PR3은 freshness hook에도 최소한의 candidate/direct-read 검사를 얹어, claim 문서가
write될 때 stale/candidate-only 상태를 조용히 통과시키지 않게 한다.

**승격 규칙(`check_claim_promotion.py`)** — mechanism/generalization 타깃에서 `candidate` 증거 거부.
인정 조건: `independently_checked` + `evidence_linked` + **비어있지 않은 `Evidence Paths Read Directly`** + `false_alarm` 아님.
mechanism/generalization은 **Lead가 직접 읽었다고 선언한 구체 artifact 경로**가 최소 1개 있어야 하며(§4.5), 직접읽기 기록 누락은 *warning이 아니라 blocker*.
단, checker가 검증하는 것은 선언된 state와 경로 존재뿐이다. 실제로 읽었는지는 skill prose의 정직성 요구이지 기계검증 대상이 아니다.

**reviewer 산출물 4절 강제**: `## High-Signal Findings` / `## Rejected False Positives` /
`## Needs Researcher Judgment` / `## Evidence Paths Read Directly`. reviewer엔 false-positive 제외 목록 명시(이미 면제된 가정, caveat의 한계, 범위 밖 사전존재 이슈, 표기 취향 등).

**confidence threshold (L10)** — peer-review/reviewer는 "**confidence ≥ 임계(예: 80) AND scientific impact AND evidence path**"만 raise
(`feature-dev/agents/code-reviewer.md`). **단 임계값은 soft/advisory가 *surface*하는 것만 좌우 — hard 차단은 deterministic checker가**(§3.2). confidence checker를 만들지 않는다. 모든 의심을 쏟으면 연구 흐름을 망침.

**테스트(named)**: `test_candidate_finding_cannot_promote_mechanism` /
`test_validated_finding_without_direct_evidence_paths_fails` / `test_validated_evidence_linked_directly_read_finding_can_promote`.

```powershell
python -m pytest tests/test_check_claim_promotion.py tests/test_check_claim_promotion_freshness.py -q
python scripts/check_claim_promotion.py --project C:\ResearchPartner --target mechanism
python scripts/check_claim_promotion.py --project C:\ResearchPartner --target generalization
```

---

## 9. Checkpoint 4 — Skill Metadata Linter + Operating Profiles  [PR4]

### 9.1 Skill metadata linter
Create `scripts/check_skill_metadata.py`, `tests/test_check_skill_metadata.py`; Modify `evaluate_harness.py`, scenarios.
**fail**: description 없음 / 트리거 조건 미명시한 generic description / hard gate인데 checker 미명시 /
gate artifact 쓰는데 경로 미명시 / 존재하지 않는 `references|examples|scripts` 참조.
**warn**: SKILL.md가 임계 초과인데 `references/` 없음 / gate artifact 좋은·나쁜 예시 없음.
(Claude §2.2: description을 3인칭 + 정확한 트리거 구문(국문 포함)으로 통일하는 것도 이 린터로 견인.)

### 9.2 Operating profiles
Create `docs/harness/operating_profiles.md`, `docs/harness/profile_change_log.md`; Modify
`capability_manifest.json`, `write_stage_checkpoint.py`, README×2.

| profile | 목적 | 정책 |
|---|---|---|
| `research-strict` | mechanism/generalization claim, 최종 figure, manuscript | 관련 gate 전부 hard |
| `exploration` | 초기 아이디어, toy run, literature scan | 일부 waiver 허용, claim ceiling 자동 제한 |
| `maintenance` | docs/scripts/installer/workflow UI | research gate는 기록만, 과학 gate는 claim 변경 시에만 |
| `external-project-refresh` | 설치된 외부 harness 업데이트 | 외부 literature/run state 보존이 hard |
| `teaching-demo` | harness 데모 | synthetic 예시 허용, real claim 금지 |

**switch 규칙**: profile 전환 = task 분류 항목 필요; 활성 profile은 stage checkpoint·workflow state에 *가시*;
**`maintenance`는 과학 claim 승격·promotion check 완화 불가**(claim/model/figure/manuscript 변경 시 `research-strict`/`exploration`으로 전환 후 진행);
전환은 `profile_change_log.md`에 일시·이전·이후·사유·claim-ceiling 효과 기록; **숨은 env 변수만으로 두지 않음**.
(주: *지금 이 정비 작업이 `maintenance`* — 단, bypass가 아님.)

중요한 runtime 현실: 현재 wired gate/hook scripts는 profile을 읽지 않는다. 따라서 PR4의 profile v0는 **advisory/display 전용**이다.
`maintenance`가 "research gate 기록만"으로 실제 차단 동작을 바꾸려면 별도 작업이 필요하다:

1. 공유 profile state 파일(예: `docs/harness/active_profile.json`)을 정의한다.
2. `path_check_hooks.py`, `check_seed_before_full_run.py`, `check_src_write_authorization.py`, `check_bash_code_write.py` 등 wired hook/gate script가 해당 파일을 읽게 한다.
3. profile별로 어떤 gate가 warning/ask/fail인지 명시한 matrix와 regression test를 추가한다.
4. profile-aware gate가 구현되기 전까지는 profile이 차단 정책을 완화하지 않는다고 README/README.ko에 명시한다.

**구현 패턴 (L8)** — `plugin-settings/examples/read-settings-hook.sh` 방식: profile state를 `docs/harness/active_profile.json`
(repo·공유 기록) + `.claude/research-harness.local.md`(머신 override, 없거나 disabled면 quick-exit)로 두고, profile-aware
gate가 둘을 명시 우선순위로 읽는다. **머신 override는 hard 과학 게이트를 floor 아래로 완화 불가**(bypass 방지) — 강화/표시만.

### 9.3 리뷰 렌즈 — enforcement-design + behavioral (L4)

> 근거: `pr-review-toolkit/agents/type-design-analyzer.md`(invariant **enforcement** 1–10),
> `pr-test-analyzer.md`(behavior-first 테스트).

`evaluate_harness.py --lens <name>`로 선택하는 *상시 아닌* 리뷰 모드 2종(상시 agent로 만들면 harness가 무거워짐 → 선택형):

- **enforcement-design lens** — 각 gate/rule/profile을 **"wired 강제 vs 문서뿐"** 으로 평가. type-design-analyzer의
  안티패턴 *"invariants enforced only through documentation"*이 우리 P-1/P-2의 정확한 병명. 항목별 산출:
  (wired? / 어느 hook이 강제? / 문서뿐이면 왜?).
- **behavioral-validation lens** — 검증이 *물리 거동*(극한·보존·스케일·차원)을 잡는가, 아니면 구현 우연(리팩터에
  깨지는)을 잡는가. "좋은 검증은 코드 리팩터가 아니라 *물리가 틀렸을 때* 실패한다." 누락 검사에 criticality 1–10 + "어떤 실패를 잡나".

**판정 규칙(중요)** — 1–10 점수는 **보조지표일 뿐**이다. 최종 판정은 **"wired 강제인가 / 문서뿐인가 / 어떤 실패를 잡는가"**로 내린다.
reviewer 산출물에 `Positive Observations` 절을 포함해 비난 일변도를 방지.

---

## 10. Checkpoint 5 — Safe Wrappers + Gate Example Fixtures  [PR5]

**Safe wrappers**: `scripts/safe_workflow_sync.py`, `scripts/safe_git_status.py`(후속: `safe_external_refresh.py`,
`safe_literature_discovery.py`) + tests. 공통 규칙: `--project` 수용, `.research-harness` 확인, 모호한 source/run root 거부,
출력 요약(raw 덤프 금지), 불안전 경로 상태 시 non-zero.

기존 설치본 hook 경로 migration은 PR1의 release note만으로 충분하지 않다. CP5는 다음 중 하나를 구현해야 한다.

- `scripts/init_research_project.py --upgrade-hooks --project <project>`: 기존 project의 `.claude/settings.local.json` hook block만 안전하게 재작성.
- 또는 `scripts/safe_external_refresh.py --upgrade-hooks`: installed project refresh 과정에서 hook block을 재작성하고 dry-run diff를 남김.

수용 기준: 이미 초기화된 임시 project에서 구버전 `python scripts/...` hook command를 넣은 뒤 upgrade를 실행하면
`$CLAUDE_PROJECT_DIR` 기반 command로 바뀌고, project-specific literature/run artifacts는 건드리지 않는다.

**Gate fixtures**: `docs/run_templates/examples/{orient_good, orient_bad_missing_researcher_answer, interview_good,
literature_waived_claim_ceiling, claim_bad_no_supports_edge}.md` + `evaluate_harness.py`/`test_evaluate_harness.py` 확장.
규칙: 좋은 artifact는 pass, 나쁜 artifact는 *의도한 이유로* fail, waived는 claim ceiling 강등 시에만 pass,
lineage support 없는 claim은 strict lineage coverage에서 fail.

```powershell
python scripts/safe_workflow_sync.py --project C:\ResearchPartner --validate-edges
python -m pytest tests/test_safe_workflow_sync.py tests/test_safe_git_status.py tests/test_evaluate_harness.py tests/test_check_lineage_coverage.py -q
```

---

## 11. Checkpoint 6 — Doc Sync (+ AGENTS.md 슬림화) + Full Validation  [PR6]

**README 필수 갱신**(README.md + README.ko.md): capability manifest = harness 계약 checker; hook registry =
hard/soft 맵; operating profiles; skill metadata linter; finding lifecycle.

**AGENTS.md 슬림화 (Claude §2.1, P0-context)** — ~40개 hook 카탈로그의 *상세*를 `docs/hooks_reference.md`로 이전,
`AGENTS.md`엔 이름+한 줄+링크만(목표 4,944→~2,000 단어). **중요 규칙은 잔류**(hard gate·필수 skill 순서·면제 시
claim ceiling 강등) — progressive disclosure ≠ 은닉. `GEMINI.md` 동시 수정. (독립 실행 가능하나 doc-sync와 함께가 안전.)
회귀 방지: `scripts/check_contract_sync.py` 또는 `scripts/evaluate_harness.py`에 `AGENTS.md`/`GEMINI.md` 단어수 상한(예: 2,200 words)을
검사하는 시나리오를 추가한다. 목표 수치를 문서에만 남기면 다시 비대해진다.

**AGENTS/GEMINI 갱신**: 지침/필수 gate가 바뀔 때만. 바꾸면 양쪽 동일 텍스트 + `check_contract_sync.py`.

```powershell
python scripts/check_contract_sync.py
python scripts/check_harness_manifest.py --project C:\ResearchPartner
python scripts/check_spawn_contracts.py --project C:\ResearchPartner
python scripts/check_skill_metadata.py --project C:\ResearchPartner
python scripts/check_cross_tier_compliance.py --project C:\ResearchPartner --strict
python scripts/check_spawn_log_integrity.py --project C:\ResearchPartner
python scripts/sync_workflow.py --project C:\ResearchPartner --validate-edges
python scripts/evaluate_harness.py --fail-on-partial
python -m pytest tests/ -q
```

---

## 11B. Checkpoint 7 — CI: PR마다 deterministic checker (L5)  [PR7]

> 근거: `.github/workflows/claude-issue-triage.yml`(`anthropics/claude-code-action@v1`, slash-command 프롬프트, OIDC 인증, `CLAUDE_CODE_SCRIPT_CAPS` 스크립트 상한).

**목표** — 결정론 checker를 PR마다 CI로 실행해 *repo 레벨*에서 강제. settings.local.json이 머신 로컬이라 배포 안 되는 문제(M-2)를 **보완**.

**파일**: Create `.github/workflows/harness-checks.yml`(+ 필요 시 `@claude` PR 트리거 워크플로).

```powershell
python scripts/check_contract_sync.py
python scripts/check_harness_manifest.py --project .
python scripts/check_spawn_contracts.py --project .
python scripts/evaluate_harness.py --fail-on-partial
python scripts/check_lineage_coverage.py --project . --strict
python scripts/check_spawn_log_integrity.py --project .
python -m pytest tests/ -q
```

**계층/한계(중요)** — CI는 **gitignored local `.claude/settings.local.json`을 고치지 못한다.** 따라서 §11B는
M-2(`--upgrade-hooks`)의 *대체가 아니다*. CI의 역할은 **generator/template/fixture가 올바른지**(새 init이 올바른 hook을
깔고, manifest/registry/계약이 정합한지)를 검증하는 것. 보너스: `claude-dedupe-issues`/`claude-issue-triage` 패턴 →
`docs/logs/anomaly_log.md` 중복제거·자동 분류에 이식.

**수용 기준**: PR이 contract/manifest/spawn/lineage/test 중 하나라도 깨면 CI red, fixture 기반이라 머신 독립.
(§4 매핑표·§13 PR표에 CP7/PR7 행 반영됨.)

---

## 12. 후순위(선택) — 나머지 lessons 항목

**2차 정독에서 추가된 신규 항목(L1·L3):**

- **[L1, 신규 capability] researcher-decision-point 프로토콜** — 과학 판단 지점(가정 선택, claim ceiling, waiver,
  anomaly가 physical인지 numerical인지, 해석)에서만 멈춰 선택지+trade-off를 제시하고 **연구자 결정을 요청**; 검증·figure·
  boilerplate 분석코드는 자동 수행. 근거: learning/explanatory-output-style. **전역 SessionStart output style이 아니라**
  `researcher-decision-point` 프로토콜/skill로 설계(지정 지점에서만 발동). 콜아웃은 `★ Assumption`/`★ Caveat`.
- **[L3, UX 층] interactive 결정 커맨드(AskUserQuestion)** — `baseline-strategy`·waiver·claim-ceiling·profile 선택을
  trade-off 설명이 달린 구조화 선택지로(`command-development/references/interactive-commands.md`). **hard gate 근거 아님**:
  답변은 반드시 `docs/gates/*.md`·`docs/harness/active_profile.json`·`.local.md`에 *파일로 저장*되고, checker가 그 파일을 읽어 판정.
- **[L9, → L1 deferral] "알아서 해"라도 추천+확인** — claim ceiling/waiver/anomaly 해석/baseline target은 자동결정 금지(`feature-dev.md`).
- **[L11, → §5 commands] single-purpose 커맨드 allowed-tools 극단 최소화** — `/sync-workflow`·`/upgrade-hooks`·`/record-waiver` 등 + "do nothing else"(`commit.md`).
- **[L12, 신규 capability·P1] harness incident log** — `docs/logs/harness_incident_log.md`로 gate 뚫림/과차단/workflow drift/subagent 범위이탈을 `anomaly_log`와 *분리* 기록, harness-evaluation으로 피드백(`model_behavior.yml`).
- **[L13, 정책·P2] 외부 접근 allowlist** — literature/API 허용 소스 + rate-limit + raw dump 금지 + PDF→`literature/pdfs/`. firewall이 아닌 정책(`init-firewall.sh`).

핵심 contract 조각(CP1–6)이 자리잡은 뒤 착수. 누락 방지를 위해 명시:

- **prompt-hook soft 경고**(lessons §3.2) — Claim Strength 1건부터. PostToolUse(prompt, `Write|Edit`)가 과장 표현을
  *surface*(차단권 없음); 차단은 CP3 checker가.
- **패턴 hook**(lessons §3.3) — `plt.show(` 작성 차단(이미 금지 규칙 → command hook 경화), seed 없는 stochastic 경고,
  단위 무단변경 의심 경고. 세션당 1회 dedup(security-guidance 패턴).
- **선언형 research-rule DSL**(lessons §7) — `docs/rules/*.md`(event/pattern/action/message)를 디스패처가 로드.
  연구자가 코드 없이 프로젝트 가드 추가. *커밋 대상* 경로(=공유 규칙).
- **자율 루프 completion-promise**(lessons §6) — `/loop` 종료 조건을 검증형 명제로("baseline 통과 AND ceiling 정당화
  AND 미해결 anomaly 없음"). "탈출용 거짓말 금지" + max-iterations.
- **플러그인 레이아웃 정렬**(lessons §8) — `.claude-plugin/plugin.json` + `hooks/hooks.json`(`${CLAUDE_PLUGIN_ROOT}`)로
  *내부 구조만* 정렬(비목표와 정합 — marketplace 공개는 후순위). CP1 경로 fix와 합치면 이식성 동시 해결.
- **CHANGELOG 신기능**(lessons §9) — 무거운 skill에 `effort:`, `context: fork`(2.1.145 버그 이력 확인 후),
  background-task Stop hook, `/usage` 비용 모니터링, `CLAUDE_CODE_SUBAGENT_MODEL`.

---

## 13. PR 분할 & 순서

| PR | 범위 | 이유 |
|----|------|------|
| **PR1** | manifest + 최소 hook registry + **hook 경로 fix** + checker + tests + evaluate 시나리오 + README 최소 + `workflow_gate_keys` 검사 + wired-hook 역방향 커버리지 | 이후 작업이 등록해 들어올 *계약 척추*. registry가 stale doc이 되지 않게 첫 PR에서 실물↔manifest↔wired hook을 함께 검증. |
| PR2 | hook registry 확장 + spawn contracts(agent 정의 + JSON) + orchestration 스폰 갱신 + tests + auto-trigger 억제 검사 | 가장 운영적인 교훈을 강제 구조로. 역할 agent는 오케스트레이션 밖 자동 호출을 막는 계약까지 확인. |
| PR3 | finding lifecycle + claim/anomaly/review skill 변경 + `check_claim_promotion.py` + `check_claim_promotion_freshness.py` + tests | 과학 claim 거동 변경 → 격리·신중. explicit promotion gate와 wired claim-write hook을 분리해 둘 다 강화. |
| PR4 | skill metadata linter + operating profiles(advisory/display v0) + fixtures + evaluate 확장 | hard contract 이후 유지보수성·사용성. profile은 wired hook이 읽기 전까지 차단 의미가 없음을 명시. |
| PR5 | safe wrappers + 기존 설치본 hook upgrade 경로 | manifest/profile 정착 후 반복작업 안정화. 신규 init뿐 아니라 기존 프로젝트의 `.claude/settings.local.json`도 안전하게 갱신. |
| PR6 | doc sync + AGENTS.md 슬림화 + 단어수 회귀 체크 + child plan superseded 포인터 + full validation | 공개 동작 문서 동기화·최종 검증. 세 계획 문서 공존으로 인한 편집 혼선을 제거. |
| PR7 | CI 워크플로(`harness-checks.yml`)로 contract/manifest/spawn/lineage/spawn-log/pytest를 PR마다 실행 | repo 레벨 강제. generator/template/fixture 정합을 검증하되 머신 로컬 settings는 못 고침(→ PR5 `--upgrade-hooks`와 분담). |

```
Checkpoint 0 (선행, 모든 PR 전)
   └─ PR1(manifest+registry+경로fix)─┬─ PR2(spawn/hook) ─ PR3(finding) ─ PR4(linter/profile) ─ PR5(wrapper) ─ PR6(doc/validate)
                                      └─ (PR2의 spawn tools 강제는 §5 subagent_type 선결 통과 시)
```

> **PR1 순서 메모**: Claude 초안은 "최저 위험(경로 fix+registry) 먼저", Codex는 "manifest 먼저". Codex 최신본이
> 경로 메타+최소 registry를 manifest PR1에 합치면서 **두 안이 수렴** → PR1에 셋(manifest·최소 registry·경로 fix)을 함께 담는다.

---

## 14. 모든 변경에 공통 적용되는 게이트

1. **AGENTS.md/GEMINI.md 동시 수정** → `python scripts/check_contract_sync.py`(미통과 시 Write hook exit 2).
2. **관련 테스트** → `python -m pytest tests/ -q`(변경 모듈 우선).
3. **user-facing capability 추가/변경**(manifest·registry·profile·wrapper) → `README.md`+`README.ko.md` 갱신.
4. **워크플로 상태/게이트/lineage 변경** → `/sync-workflow`.
5. **coherent checkpoint마다 commit**(scope 분리). harness `scripts/` 편집은 cross-tier hook 비대상(§3.1) → 직접 편집·커밋 가능.

---

## 15. 리스크 레지스터 (병합)

| 리스크 | 발생 지점 | 완화 |
|---|---|---|
| manifest가 또 다른 stale 문서가 됨 | CP1 | checker가 경로·test 누락 시 fail(양방향: 실물↔manifest). |
| workflow node id를 추측해 spurious fail 발생 | CP1 | manifest는 Cytoscape node id가 아니라 실제 gate key(`workflow_gate_keys`, 예: `interview_gate`)를 선언하고 checker가 key 기준으로 검증. |
| hook registry가 stale 문서가 됨 | CP1 | 첫 PR에서 최소 registry를 manifest checker로 검증하고, `.claude/settings.local.json` wired hook이 registry/`known_uncovered_wired_hooks` 어디에도 없으면 fail. |
| prompt hook이 실수로 hard 과학 게이트가 됨 | CP2 | registry가 prompt hook을 `soft`로 분류, 차단은 checker만. |
| **spawn `tools:`가 JSON 계약뿐(런타임 미강제)** | CP2 | **agent 정의(`tools:`)로 강제 + contract JSON으로 검사 — 둘 다. §5에서 subagent_type 선확인.** |
| role agent가 오케스트레이션 밖에서 자동 호출됨 | CP2 | `.claude/agents/` description은 "명시 스폰 전용" 계약을 갖고, broad auto-trigger 문구를 `check_spawn_contracts.py`가 fail. |
| Implementation Agent가 자기 작업 검증 불가 | CP2 | 좁은 validation Bash 또는 read-only Validator handoff 요구. |
| checker 남발로 유지비 증가 | 전 구간 | vertical slice, 가능하면 `evaluate_harness.py`에 흡수. |
| claim lifecycle이 초기 탐색 과차단 | CP3 | 엄격 lifecycle은 우선 mechanism/generalization 승격에만. |
| Lead 직접읽기 요구가 prose뿐 | CP3 | `check_claim_promotion.py`가 explicit promotion을 거부하고, wired `check_claim_promotion_freshness.py`도 claim 파일 write 시 stale/candidate/direct-read 누락을 잡는다. |
| maintenance profile이 실제 hook을 바꾸는 것처럼 오해됨 | CP4 | profile v0는 advisory/display 전용으로 문서화. blocking 완화가 필요하면 별도 profile-aware wired hook 작업과 matrix test를 먼저 구현. |
| 기존 설치본의 hook 경로가 영구히 낡음 | CP5 | `init_research_project.py --upgrade-hooks` 또는 `safe_external_refresh.py --upgrade-hooks`로 settings hook 블록을 재작성하되 프로젝트 산출물은 보존. |
| README/AGENTS drift | CP6·전 구간 | `check_contract_sync.py` + 같은 checkpoint에서 README×2 동시 갱신. AGENTS/GEMINI 단어수 상한도 회귀 체크로 고정. |
| 하위 implementation plan을 누군가 계속 편집 | CP6 | child 문서 상단에 `SUPERSEDED` 포인터를 두고 통합본만 편집 대상으로 지정. |
| 소스 repo가 run 산출물로 오염 | 전 구간 | 실험은 임시 fixture/형제 run workspace에서. |

---

## 16. 연구자 리뷰 체크포인트

1. **PR1 설계 후** — manifest 필드 + 첫 8개 capability + 최소 hook registry + wired-hook 역방향 커버리지 + workflow gate key 규칙 승인.
2. **PR2/§5 후** — subagent_type 지원 결과 + 역할별 `tools:` 허용집합 + hard/soft hook 분류 + auto-trigger 억제 규칙 승인.
3. **PR3 머지 전** — finding 상태 + claim-ceiling 동작 + Lead 직접읽기 강제 + explicit/wired claim checker 분리 승인.
4. **profile 롤아웃 전** — profile v0가 advisory/display 전용인지, 또는 profile-aware wired hook까지 구현할지 승인.

---

## 17. Definition of Done

- [ ] `check_harness_manifest.py` 존재·테스트됨·harness 평가에 포함.
- [ ] 첫 8개 canonical capability + 최소 hard-hook registry가 manifest에 표현·기계검사됨.
- [ ] manifest workflow 검사는 추측 node id가 아니라 실제 `workflow_gate_keys`를 사용.
- [ ] `.claude/settings.local.json` wired hook은 registry에 있거나 `known_uncovered_wired_hooks`에 명시됨. 최종 릴리스 전 uncovered 목록은 0.
- [ ] hard hook의 path/interpreter 메타 검증 + **실제 hook 경로가 `$CLAUDE_PROJECT_DIR` 기반**.
- [ ] 기존 설치본을 위한 hook upgrade 경로(`--upgrade-hooks`)가 있고 프로젝트별 연구 산출물을 보존하는 fixture로 검증됨.
- [ ] spawn 계약이 allowed tools·write scope·completion promise 명시(JSON) + 역할은 **agent 정의로 강제**.
- [ ] role agent description이 명시 스폰 전용이며 broad auto-trigger 문구를 린터가 차단.
- [ ] Implementation 검증이 좁은 Bash 또는 명시 validator handoff로 가능.
- [ ] `candidate` finding이 claim 승격 불가; mechanism/generalization은 직접읽기 경로 강제. 이 동작은 explicit `check_claim_promotion.py`와 wired `check_claim_promotion_freshness.py` 양쪽에서 검증.
- [ ] reviewer 산출물 4절(High-Signal/Rejected/Needs-Judgment/Evidence-Paths) 포함.
- [ ] skill metadata 린트가 누락 trigger/checker/artifact를 잡음.
- [ ] operating profile v0 범위가 advisory/display 전용으로 명시됨. blocking 의미를 부여하려면 profile-aware wired hook과 matrix test가 먼저 통과.
- [ ] AGENTS.md/GEMINI.md 슬림화 목표는 단어수 상한 체크로 회귀 방지.
- [ ] 하위 implementation plan 문서들은 `SUPERSEDED` 포인터를 갖고 통합본을 유일한 편집 대상으로 가리킴.
- [ ] README·README.ko가 새 공개 동작과 동기화; 지침 변경 시 AGENTS≡GEMINI.
- [ ] (L7) PreToolUse hook은 싼 hard 차단만; lineage-coverage·manifest-completeness·spawn-log-reconciliation 같은 무거운 검사는 Stage Checkpoint/CI에서 실행.
- [ ] (L5/CP7) `harness-checks.yml` CI가 PR마다 contract/manifest/spawn/lineage/spawn-log/pytest를 실행하고 generator/template/fixture 정합을 검증(머신 로컬 settings 미수정 → `--upgrade-hooks`와 분담).
- [ ] (L8) profile state를 `active_profile.json`(repo) + `.claude/research-harness.local.md`(머신 override, quick-exit)로 읽되, override가 hard 과학 게이트를 floor 아래로 완화 못 함.
- [ ] (L1) researcher-decision-point 프로토콜이 가정/claim ceiling/waiver/anomaly 해석 지점에서 자동결정 대신 "추천+확인"을 요청(전역 output style 아님).
- [ ] (L10) peer-review/reviewer가 "confidence≥임계 AND scientific impact AND evidence path"만 raise(임계는 surface만, hard 차단은 deterministic).
- [ ] (L12) `docs/logs/harness_incident_log.md`가 harness 자체 실패(gate 뚫림/과차단/workflow drift/subagent 범위이탈)를 research anomaly와 *분리* 기록하고 harness-evaluation으로 피드백.
- [ ] (L13) 외부 literature/API 접근 allowlist + rate-limit + raw dump 금지 + PDF→`literature/pdfs/` 정책이 문서화됨.

---

## 18. 부록 — 출처 · 매핑

**출처 문서**
- `claude-code/claude_code_lessons.md`, `claude-code/implementation_plan.md`
- `codex/claude_code_lessons.md`, `codex/researchpartner_adoption_plan.md`

**lessons § ↔ Checkpoint ↔ PR 매핑**

| lessons § | 내용 | CP | PR |
|---|---|---|---|
| §2.1 | AGENTS.md 슬림화 | 6 | PR6 |
| §2.2/2.3 | skill description/린터 | 4 | PR4 |
| §3.1 | hook 경로 이식성 | 1 | PR1 |
| §3.2 | 표면화↔차단 분리(prompt=soft) | 2·12 | PR2/선택 |
| §3.5 | hard/soft hook registry | 1·2 | PR1/PR2 |
| §4.1 | spawn tools 최소권한(agent 정의) | 2 | PR2 |
| §4.2 | 2-pass + finding 상태머신 | 3 | PR3 |
| §4.5 | Lead 직접읽기 강제 | 3 | PR3 |
| §6 | 자율 루프 completion-promise | 12 | 선택 |
| §7 | 선언형 research-rule DSL | 12 | 선택 |
| §8 | capability manifest / profile / wrapper / plugin layout | 1·4·5·12 | PR1/PR4/PR5/선택 |
| §9 | CHANGELOG 신기능 | 12 | 선택 |

**최소 1-슬라이스(딱 하나만 한다면)**: manifest(`orient/interview/claim-promotion/workflow-sync`) +
최소 hook registry + `check_harness_manifest.py` + tests + evaluate 시나리오 + hook 경로 fix. 중심 아이디어를 전면 리팩터 없이 증명.
