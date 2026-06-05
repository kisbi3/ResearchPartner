# Research Partner: 물리 연구 하네스

Research Partner는 AI가 보조하는 물리 연구를 위한 저장소 하네스입니다. 연구 사슬을 눈에 보이게 유지하고, 근거 없는 claim 승격을 막으며, 과학적 판단을 자동화 뒤에 숨기지 않고 연구자에게 남깁니다.

## 무엇인가

Research Partner는 다음 사슬을 보호합니다:

```text
physical assumptions -> model definition -> analytical checks -> numerical implementation -> validation -> figures -> manuscript claims
```

워크플로우 루프는 다음과 같습니다:

```text
Orient -> Interview -> Specify -> Seed -> Validate -> Execute -> Evaluate -> Review -> Retrospect
    ^                                                                                 |
    +----------------------------- Evolutionary Loop ---------------------------------+
```

각 단계는 `docs/`, `literature/`, `outputs/`, 또는 live workflow 파일에 지속 가능한 산출물을 남깁니다. `workflow_hooks.py`는 agent spawn을 자동 기록하고, `/sync-workflow`(`python scripts\sync_workflow.py --project <project-dir>`)가 live workflow 데이터와 `workflow_map.live.json`을 갱신하는 1차 경로입니다. `generate_workflow_map.py`는 필요할 때 HTML 셸을 다시 만드는 용도이며, 주 상태 갱신 경로가 아닙니다.

## 설치

선결 조건:

- `python`으로 실행 가능한 Python 3.10 이상.
- 로컬 연구 프로젝트 디렉토리.
- Git은 필수는 아니지만 checkpoint에 권장됩니다.
- 테스트와 CI 의존성은 `requirements.txt`에 선언되어 있습니다.

현재 프로젝트 루트에 설치:

```powershell
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/kisbi3/ResearchPartner/main/scripts/install.py').read())"
python scripts\init_research_project.py
```

설치 검증:

```powershell
python -m pip install -r requirements.txt
python scripts\evaluate_harness.py --fail-on-partial
python scripts\check_harness_manifest.py
python scripts\check_spawn_contracts.py
python scripts\check_contract_sync.py
python scripts\check_harness_version.py
```

설치는 owned-file hash가 들어 있는 `harness.lock.json`을 써서 프로젝트가 설치된 harness stamp와 로컬 harness 수정을 보고할 수 있게 합니다. `install.py --force`는 harness-owned 파일만 갱신하며 `docs/gates/`, `docs/plan/`, `docs/process/` 아래 연구 산출물은 보존합니다. `python scripts\update_harness.py --project <project-dir> --source <harness-source>`는 선택적 업데이트를 dry-run으로 보여주고, `--apply`를 붙이면 harness-owned 업데이트만 쓰며 충돌은 `.harness-new` sidecar로 남깁니다. 적용 후 live hook을 갱신하려면 프로젝트 루트에서 `python scripts\init_research_project.py`를 다시 실행하거나, `--apply`와 함께 `--upgrade-hooks`를 붙여 업데이트 중 hook 등록을 머지합니다. `--adopt`는 stamp가 없는 legacy 프로젝트를 먼저 stamp할 때만 사용합니다.

첫 실행은 assistant에게 task intake부터 시작하라고 요청합니다. 초기화는 `.research-harness`, `docs\process\live_workflow_diagram.md`, 문헌 작업 공간, project packet, `outputs/`를 scaffold합니다. gate, evidence, lineage가 바뀌면 `/sync-workflow`를 실행하세요.

live enforcement hook은 `.claude/settings.local.json`에 있습니다. 이 파일이 없으면 초기화가 새로 쓰고, 이미 있으면(이미 Claude Code를 쓰던 프로젝트에 harness를 도입할 때 흔함) harness hook을 그 파일에 **머지**합니다 — 기존 권한과 커스텀 hook은 보존하고, 이미 있는 harness hook은 건너뜁니다(멱등). 이 repo에 tracked되는 harness copy에는 portable hook 등록만 들어가야 하며 machine-local permission은 넣지 않습니다. 파일이 있지만 파싱할 수 없으면 초기화는 파일을 건드리지 않고 hook이 설치되지 않았다는 경고를 출력합니다. 파일을 고친 뒤 `python scripts\init_research_project.py`를 다시 실행하면 설치됩니다.

## 사용법

assistant는 모든 연구 task를 `skills/task-intake/SKILL.md`로 시작해야 합니다. 새 모델, simulation, analysis, manuscript claim, reproduction 작업은 다음 순서를 따릅니다:

```text
task-intake -> professor-interview -> literature-review-planning -> model-specification -> baseline-strategy -> seed-design -> baseline-validation
```

시나리오 A, 새 모델 또는 simulation:

1. 연구 질문, 가정, 단위, 첫 professor question을 기록합니다.
2. 문헌을 검토하거나 명시적으로 waive합니다. literature waiver는 claim ceiling을 `interpretation`으로 낮춥니다.
3. 모델을 명세합니다. model waiver는 claim ceiling을 `observation`으로 낮춥니다.
4. baseline strategy를 정하고, seed task를 설계하고, baseline을 검증한 뒤 해석을 바꿀 수 있는 가장 작은 iteration을 실행합니다.
5. evidence를 기록하고 `/sync-workflow`를 실행한 다음, claim promotion gate를 통해서만 claim을 승격합니다.

시나리오 B, 기존 프로젝트:

1. `python scripts\audit_existing_project.py <project-root>`로 scripts, figures, outputs, validation gaps를 inventory합니다.
2. 기존 파일을 보존하면서 하네스를 초기화합니다.
3. `/sync-workflow`로 artifact에서 live state를 다시 구성합니다.
4. 오래된 figure나 manuscript 문구를 강화하기 전에 validation, provenance, lineage, claim check를 실행합니다.

선택적 도메인 워크스페이스는 marker가 있는 프로젝트 하나 안에 reproduction, thread, subproblem, integration용 `domains/<name>/` 영역을 둡니다. Step 1에서는 project-level gate, claim check, lineage check, provenance check 동작을 바꾸지 않으며, `domains/`가 없는 프로젝트는 계속 프로젝트 루트가 기본 domain으로 resolve됩니다.

플랫폼 라우팅:

| 플랫폼 | 읽는 파일 | 메모 |
|---|---|---|
| Codex / Copilot 스타일 agent | `AGENTS.md` | 단어수 예산이 걸린 resident contract |
| Gemini CLI | `GEMINI.md` | `AGENTS.md`와 byte-identical이어야 함 |
| Claude Code | `AGENTS.md` 또는 프로젝트 `CLAUDE.md` | 설치 시 프로젝트 hooks와 `.claude/agents/<role>.md` 적용 |
| Slash commands | `python scripts\install_skills.py [--global]` | Claude Code, Gemini/Antigravity-cli, Codex surface에 skill 설치 |

## 연구 모델

Research Partner는 연구실(research group)을 본떠 설계되었습니다: 당신이 소유한 교수 연구실입니다. **PI**는 사람 연구자, 즉 당신입니다 — 과학과 게이트 결정을 소유합니다. **Lead Agent**는 교수입니다 — 메인 대화 컨텍스트로, 연구자 대화와 과학적 판단을 소유하고 subagent를 spawn하는 *유일한* 역할입니다. 연구실 구성원은 spawn되는 leaf agent들입니다.

전형적인 iteration은 체크리스트가 아니라 연구실 사이클로 읽힙니다: PI 요청 -> 교수 질문 -> 연구원 실행 -> 독립 검증 -> 교수 요약 -> PI 결정. 각 화살표는 지속 가능한 artifact를 남기며, 마지막 결정은 오직 당신만 사인할 수 있습니다(아래 브레이크 참조).

**브레이크(Human-Owned Decision Gate).** 하네스의 #1 원칙 — 과학적 판단은 연구자에게 남긴다 — 은 권고가 아니라 강제됩니다. 결정 파일 `docs/gates/{orient,interview,model,seed}_decision.md`(및 skip waiver)는 *모든* agent에게 쓰기 차단됩니다: 연구실은 대응하는 note/spec 파일에 제안 초안을 쓰지만, 결정은 오직 당신만 기록합니다. 해당 게이트는 — bypass 환경변수로도 당신의 사인오프를 면제할 수 없으며 — 당신이 `## Decision`을 채우기 전까지 닫혀 있습니다.

Leaf agent는 Lead가 `subagent_type`으로 직접 spawn합니다:

| Leaf agent | 목적 |
|---|---|
| Graduate Student | 하나의 bounded task에 대해 코드를 **작성하고 실행**(병렬 가능); 증거와 자기 해석을 가설로 보고; binding verdict는 내리지 않음 |
| Code Reviewer | 코드를 정적으로 리뷰 — 정확성, spec 준수, 재현성 위생; 실행하지 않음 |
| Scientific Validator | 독립적으로 재실행하고 고정된 기준으로 검증; 코드 수정이나 claim 강화는 하지 않음 |
| Cache-Log Auditor | log, cache, output hygiene를 기계적으로 감사 |
| Workflow Manager | workflow + lineage 상태 갱신; 게이트 상태와 끊긴 edge 보고 |
| Peer-Review Professor | `meeting --scope review` 또는 `--scope full` 안에서만 실행되는 단발성 adversarial review |

작성자 ≠ 검증자: 코드를 작성한 graduate student는 자기 결과를 스스로 인증하지 않습니다 — 독립적인 Scientific Validator가 당신이 model/seed 게이트에서 잠근 기준에 대해 pass/fail을 판정합니다.

Lead Agent는 별도 agent가 아니라 mental mode로 9개 stance를 사용합니다: Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, Architect. spawn block, stance 세부 내용, completion-conference 규칙은 `docs/orchestration_protocol.md`에 있습니다.

## 참조

명령어:

| 필요 | 명령어 | 목적 |
|---|---|---|
| 하네스 설치 | `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/kisbi3/ResearchPartner/main/scripts/install.py').read())"` | 현재 프로젝트에 관리되는 하네스 파일 설치 |
| 프로젝트 초기화 | `python scripts\init_research_project.py --project <project-dir>` | 연구 프로젝트 marker와 기본 구조 생성 |
| domain workspace scaffold | `python scripts\scaffold_domain.py --project <project-dir> --name <slug> --type reproduction` | project-level gate를 이동하지 않고 선택적 `domains\<slug>\` workspace와 typed manual 추가 |
| domain manifest 검증 | `python scripts\check_domain_manifest.py --project <project-dir>` | `domains/`가 있을 때 domain manual 구조를 검증하고 없으면 dormant 통과 |
| 기존 프로젝트 감사 | `python scripts\audit_existing_project.py <project-root>` | scripts, figures, outputs, validation gaps inventory |
| 하네스 평가 | `python scripts\evaluate_harness.py --fail-on-partial` | scenario coverage 확인; partial도 이제 CI 실패 |
| harness stamp 확인 | `python scripts\check_harness_version.py --project <project-dir>` | 설치된 harness stamp와 로컬에서 수정된 owned file 보고 |
| vendored harness 업데이트 | `python scripts\update_harness.py --project <project-dir> --source <harness-source> [--apply] [--upgrade-hooks]` | 비파괴 harness-owned 업데이트를 dry-run 또는 적용; 충돌은 `.harness-new` sidecar로 남김; `--apply`와 함께 `--upgrade-hooks`를 쓰면 hook도 갱신 |
| 테스트 의존성 설치 | `python -m pip install -r requirements.txt` | `pytest`, `PyYAML` 설치 |
| CI 하네스 검사 | `.github/workflows/harness-checks.yml` | push와 pull request에서 deterministic gate 실행 |
| live workflow 동기화 | `python scripts\sync_workflow.py --project <project-dir> [--validate-edges]` | gate status, lineage, live JSON 갱신 |
| workflow HTML 재생성 | `python scripts\generate_workflow_map.py [--central]` | 필요할 때 dashboard shell 재생성 |
| workflow map serve | `python scripts\serve_workflow_map.py --project <project-dir>` | workflow dashboard를 로컬에서 serve |
| manifest 검증 | `python scripts\check_harness_manifest.py` | capability manifest, hook registry, portable hook path 검증 |
| spawn contract 검증 | `python scripts\check_spawn_contracts.py` | leaf agent definition, tools, single-spawner contract 검증 |
| contract sync 검증 | `python scripts\check_contract_sync.py` | `AGENTS.md` == `GEMINI.md` 및 resident word budget 강제 |
| orient gate 검증 | `python scripts\check_orient_recorded.py --project <project-dir>` | downstream work 전 task-intake artifact 요구 |
| interview gate 검증 | `python scripts\check_interview_recorded.py --project <project-dir>` | crystallized question과 agreed direction 요구 |
| literature gate 검증 | `python scripts\check_literature_reviewed.py --project <project-dir>` | ready/waived literature status 요구 |
| model gate 검증 | `python scripts\check_model_specified.py --project <project-dir>` | model definition 또는 waiver 요구 |
| baseline strategy 검증 | `python scripts\check_baseline_strategy.py --project <project-dir>` | variation/new-model decision과 target 요구 |
| baseline gate 검증 | `python scripts\check_baseline_gate.py --project <project-dir>` | baseline pass 또는 명시 waiver 요구 |
| claim promotion 검증 | `python scripts\check_claim_promotion.py --project <project-dir> --target mechanism` | claim-ceiling promotion gate |
| claim freshness 검증 | `python scripts\check_claim_promotion_freshness.py --project <project-dir>` | stale 또는 candidate-only claim support 확인 |
| lineage coverage 검증 | `python scripts\check_lineage_coverage.py --project <project-dir> [--strict]` | unsupported claim과 lineage 기대 위반 탐지 |
| figure provenance 검증 | `python scripts\check_figure_provenance.py --root <project-dir>` | figure provenance 추적 요구 |
| session resumption 검증 | `python scripts\check_session_resumable.py --project <project-dir>` | interruption 후 in-flight task와 blocked gate 표면화 |
| computation checkpoint 검증 | `python scripts\check_computation_resumable.py --project <project-dir>` | orphaned long-run checkpoint 탐지 |
| stage checkpoint 작성 | `python scripts\write_stage_checkpoint.py --project <project-dir> --stage N` | 연구 stage를 compact하게 요약 |
| 논문 리뷰 scaffold | `python scripts\scaffold_paper_review.py --project <project-dir> --paper-id P1 --title "Title"` | paper review note와 index entry 생성 |
| 논문 PDF 처리 | `python scripts\process_paper_for_review.py --project <project-dir> --paper-id P1 --title "Title" --pdf <pdf-path>` | scaffold, text extraction, provisional note draft |
| 논문 리뷰 품질 검증 | `python scripts\check_paper_review_quality.py <review-path>` | 약한 literature note가 novelty 근거가 되기 전에 차단 |

설치된 skills:

| Skill | 목적 |
|---|---|
| `task-intake` | task 분류, 역할, 첫 professor question 기록 |
| `professor-interview` | 모호함을 연구 질문과 다음 단계로 전환 |
| `literature-review-planning` | literature access, PDF, novelty map, reproduction target 계획 |
| `model-specification` | 물리계, 방정식, 변수, 가정, regime 기록 |
| `baseline-strategy` | variation vs new model과 첫 verification target 선택 |
| `seed-design` | research seed를 testable task packet으로 변환 |
| `graduate-student` | spawn되는 작업자: 하나의 bounded task에 대해 코드를 작성하고 실행(병렬 가능); 증거와 가설 보고 |
| `code-reviewer` | graduate student 코드의 정적 리뷰(실행 없음) |
| `scientific-validator` | 독립 재실행 + 고정 기준에 따른 검증 |
| `cache-log-auditor` | cache, log, output의 기계적 감사 |
| `workflow-manager` | workflow + lineage 상태 갱신; 게이트 상태 보고 |
| `peer-review-professor` | claim과 evidence의 adversarial review |
| `baseline-validation` | toy model, known limit, reproduction, conservation check 검증 |
| `numerical-validation` | stability, convergence, uncertainty, sensitivity 확인 |
| `dimensional-analysis` | dimensions, units, nondimensionalization 확인 |
| `claim-to-evidence` | claim wording을 evidence 및 claim ceiling에 연결 |
| `scientific-verification-before-claim` | claim 강화 전 evidence 검증 |
| `anomaly-debugging` | 놀랍거나 실패한 결과를 수정 전 분류 |
| `research-plan-review` | plan completeness, assumptions, validation gaps 검토 |
| `researcher-review-loop` | 결정 checkpoint에서 연구자 검토 요청 |
| `research-retrospective` | outcome, reusable checks, failures, open questions 기록 |
| `meeting` | contested/high-stakes 단계에서 Lead/peer-review meeting convene |
| `sync-workflow` | filesystem state에서 live workflow artifact 갱신 |
| `existing-research-onboarding` | 기존 프로젝트에 하네스 retrofit |
| `harness-evaluation` | 하네스 자체가 제대로 작동하는지 평가 |

이름으로 호출하는 Dynamic Workflow:

`.claude/workflows/*.js`에 있는 자기완결형 멀티에이전트 워크플로우 스크립트는 전체 스크립트를 다시 보낼 필요 없이 이름만으로(세션 비종속) 호출할 수 있습니다. 각 파일은 `export const meta = { name, description, phases }` 리터럴로 시작하며 `name`이 파일명과 일치합니다.

| Workflow | 목적 |
|---|---|
| `harness-legacy-scan` | 하네스의 낡은 규칙, 중복, 전역 컨텍스트 세금, 과도하게 넓은 스킬, 제품 기능 중복, 위험한 권한을 읽기 전용으로 감사하고, KEEP/SHRINK/MOVE/SPLIT/CONVERT/DELETE로 분류한 리포트와 적대적 반박 검토를 생성합니다. 파일을 수정하지 않습니다. |

## 규율은 어떻게 강제되는가

Research Partner는 표면화와 차단을 분리합니다.

| 계층 | 예시 | 효과 |
|---|---|---|
| 표면화 | skills, prompts, reviewer questions, meetings | 가정, 위험, 결정을 보이게 함 |
| runtime hooks | cross-tier write hook, Bash code-write hook, peer-review invocation hook | live runtime에서 unsafe tool use 또는 invalid invocation 차단 |
| deterministic checkers | capability manifest, spawn contracts, finding lifecycle, lineage, contract sync | repository state drift를 로컬과 CI에서 실패시킴 |
| CI | `harness-checks.yml` + `evaluate_harness.py --fail-on-partial` | 모든 PR에서 새 failed/partial harness scenario를 red로 만듦 |

결정론적 척추는 `docs/hooks_reference.md`에 문서화되어 있습니다: capability manifest, spawn contracts, finding lifecycle, word budget이 포함된 contract sync, CI. 이 섹션은 연구자와 기여자를 위한 README에만 두며, 방금 줄인 resident contract인 `AGENTS.md`로 옮기지 않습니다.

이 source repo 안에서 작업하는 maintainer는 live hook이 harness source 수정을 과하게 막을 때 `docs/harness/self_hosting_development.md` 절차를 따릅니다.

## 비전

Research Partner의 목표는 AI assistance를 과학적으로 읽을 수 있게 만드는 것입니다. 좋은 run은 가정, evidence, validation, figures, claims, waivers, unresolved questions를 다른 연구자가 직접 검토할 수 있는 형태로 남깁니다. 목표는 더 많은 자동화가 아니라, 속이기 어려운 과학적 규율입니다.
