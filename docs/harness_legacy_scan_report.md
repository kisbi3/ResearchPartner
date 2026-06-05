# harness-legacy-scan — 읽기 전용 하네스 감사 리포트

- **실행 방식**: Dynamic Workflow (`harness-legacy-scan`), 7개 관점 에이전트, 읽기 전용
- **상태**: 완료 (agents=7, subagent_tokens≈342K, tool_uses=86, 약 16분)
- **변경 사항**: 없음 — 파일/hook/MCP/권한 미수정. 본 리포트(`docs/harness_legacy_scan_report.md`)만 신규 작성
- **분류 결과**: 40개 항목 — KEEP 18 · SHRINK 11 · MOVE 2 · CONVERT 7 · SPLIT 1 · DELETE 1
- **반박 검토**: 위험 항목 21개 중 UPHOLD 4 · SOFTEN 12 · NEEDS_HUMAN 4 · DOWNGRADE_TO_KEEP 1

> 핵심 긴장: Planner는 "전역 컨텍스트 세금"을 공격적으로 줄이려 했지만, Adversarial Reviewer가 그중 다수를 **SOFTEN**했다. 이유는 단 하나 — **soft hook(스크립트 미강제 규율)은 오직 resident 텍스트로만 존재**한다. `docs/hooks_reference.md`는 `@`-import 되지 않으므로, AGENTS.md의 TOC를 포인터로 줄이면 soft 규율(과주장 방지, 가정 명시, mechanism-from-visual 금지)의 **유일한 흔적이 사라진다.** 따라서 "TOC를 줄여라"는 글자 중복 근거만으로는 안전하지 않다.

---

## 1. 전체 요약

하네스의 구조적 문제는 **3겹 동심원 중복**으로 요약된다 (Inventory Agent 검증, `diff -q` empty):

1. **CLAUDE.md → AGENTS.md → GEMINI.md**: CLAUDE.md(11B)는 순수 리다이렉트, AGENTS.md(~14KB/290줄)가 매 세션 resident 페이로드, GEMINI.md는 AGENTS.md와 **바이트 동일**. 같은 14KB 지침이 디스크에 2벌 저장되고 매 세션 pin된다.
2. **3중 저장 task 스킬**: 7개 능력(task-intake, dimensional-analysis, existing-research-onboarding, harness-evaluation, anomaly-debugging, meeting, sync-workflow)이 `skills/<n>/SKILL.md == .claude/commands/<n>.md == .agents/workflows/<n>.md`로 **각 3벌 바이트 동일**. 7개 문서가 21개 파일에 저장.
3. **에이전트 스텁의 1:1 스킬 미러**: `.claude/agents/*.md` 6개는 전부 11줄 위임 스텁("`skills/<같은이름>/SKILL.md`를 로드")이고, 동명 스킬이 실제 내용을 담는다.

**로드 비용 진실**: 매 세션 실제로 pin되는 것은 **AGENTS.md/GEMINI.md(~14KB) + settings.local.json hooks 뿐**이다. 25개 스킬·7개 커맨드·7개 워크플로우 미러·6개 에이전트 스텁·PHYSICS.md·docs/는 전부 on-demand. 즉 **컨텍스트 세금의 거의 전부가 AGENTS.md 한 파일에 집중**되어 있고, GEMINI.md 때문에 모든 절감이 2배로 적용된다 → **AGENTS.md를 먼저 줄이는 것이 최고 레버리지**.

**권한 측면**: settings.local.json에는 `permissions`/`allowed-tools`/`deny` 블록이 **전혀 없다**. 모든 게이팅이 Python hook(restrict-or-warn)으로 이뤄지고, 어떤 hook도 도구를 grant/auto-approve 하지 않는다. 유일한 "grant" 표면은 BYPASS 환경변수 4종인데, 품질/순서 게이트만 waive하고 **PI 결정 게이트는 절대 waive하지 못한다**(설계상 정확).

**가장 명확한 발견 2가지 (코드 검증됨)**:
- `workflow_hooks.py`는 `tool_name != 'Agent'`이면 즉시 0 반환(L281-282)인데, settings에서 Write|Edit / Bash|PowerShell 슬롯(L17·40·47)에 배선되어 **매 호출마다 즉시 no-op하는 인터프리터를 띄운다 = 죽은 배선**.
- skill 설명("spawned 되면 이 스킬을 로드하라" = auto-trigger)과 agent 스텁("do not auto-trigger") 간 **트리거 의미 모순**이 6쌍 전부에 존재.

---

## 2. 유지해야 할 항목 (KEEP — 18)

> 반박 검토에서 보호되었거나, 중복이 "스킬 내용"이 아니라 "저장 구조"에만 있는 항목들.

| 경로 | 유지 근거 | 위험도 | 신뢰도 |
|---|---|---|---|
| `CLAUDE.md` (→@AGENTS.md) | 11B 리다이렉트, 저장소 유일 @-import. 3번째 사본보다 저렴 | low | high |
| `GEMINI.md` | 세션당 1런타임만 로드 → 세션 세금 아님. 중복은 *AGENTS.md 먼저 줄일* 근거이지 삭제 근거 아님 | medium | high |
| `PHYSICS.md` | `@`-import 안 됨(검증) → 세션 비과세. on-demand 유지 | low | medium |
| `.agents/workflows/{7}` | 3번째 사본이지만 **Gemini/Antigravity 런타임용** (스킬 auto-expose 없음). 삭제 시 Gemini 동작 변경 | medium | medium |
| `.claude/agents/*` (6 스텁) | per-agent tool allowlist(예: code-reviewer는 Read/Grep/Glob, **no Bash**)가 author≠validator의 load-bearing 장치. CONVERT의 *fold 대상* | medium | medium |
| `.claude/settings.local.json` | hooks-only, allowlist 부재가 곧 무권한 부여. 전 hook이 restrict/warn-only. 구조상 보수적 | low | high |
| BYPASS 환경변수 4종 | 유일 grant 표면이나 품질/순서 게이트만 waive, PI 결정 게이트 절대 불가(검증) | low | high |
| 게이트 결속 스킬: `model-specification`, `baseline-strategy`, `baseline-validation`, `professor-interview`, `dimensional-analysis`, `anomaly-debugging`, `meeting`, `sync-workflow`, `harness-evaluation`, `existing-research-onboarding`, `research-retrospective` | 각자 `check_*` 게이트에 결속, 제품 내장 기능에 없는 고유 내용. 중복은 *3중 저장*이거나 *공유 boilerplate*이지 스킬 본질 아님 | low | high/med |

**특기 사항(반박 보호)**:
- `meeting` / `sync-workflow` / `task-intake`: `/code-review`·`/verify` 같은 내장 기능과 달리 **결정론적·게이트 강제 진입점**이다. `check_peer_review_invocation.py`는 peer-review 교수를 meeting 컨텍스트에서만 허용 → meeting은 단순 중복이 아님.

---

## 3. 줄여야 할 항목 (SHRINK — 11, 반박 검토 반영)

각 항목 형식: **경로 · 목적 · 문제 · 근거 · 조치 · 옮길 위치 · 위험 · 신뢰 · /harness-diet 자동화** + ⚖️반박 verdict.

### 3.1 `AGENTS.md :: ## Scientific Hook Index` (L62-81)
- **목적**: docs/hooks_reference.md로 가는 ~47앵커 TOC, 매 세션 resident
- **문제**: L64가 "resident 텍스트는 짧게 유지하라"는데 정작 이 섹션이 최장. 자기모순
- **근거**: 실제 내용(63섹션/346줄)은 reference에 있고 @-import 안 됨
- **조치**: SHRINK → 포인터 1줄 / **위치**: docs/hooks_reference.md / **위험** low / **신뢰** high / **diet 자동** ✅
- ⚖️ **SOFTEN (residual medium)**: 이 인덱스 항목 다수는 **스크립트 미강제 soft hook**(Ambiguity, Assumption/Units, Claim Strength, Reviewer Simulation, Negative Result, Scope Creep…). resident 텍스트가 이들의 **유일한 신호**다. 하드 게이트 TOC 앵커만 잘라내되, soft hook 목록은 한 줄 요약으로 resident에 남길 것.

### 3.2 `AGENTS.md :: ## Hard-Enforced Gates` (L47-60)
- **목적**: 10개 하드 게이트 bullet TOC
- **문제**: 동일 TOC-중복 패턴, 일부는 Professor-Led Lab(L26-27) 3번째 사본
- **조치**: SHRINK → 2-3줄 노트 / **위치**: docs/hooks_reference.md / **위험** low / **신뢰** high / **diet 자동** ✅
- ⚖️ **SOFTEN (medium)**: 이 bullet들은 Lead가 *쓰기 시도 전에* 어느 게이트가 하드 블록할지 알려줘 **잘못된 라우팅(직접 .py 쓰기 등)으로 인한 exit-2 thrash를 예방**한다. L51 결정-게이트 브레이크 + L52 cross-tier 라우팅은 파일에서 가장 안전 임계 문장 → 그대로 유지. CI/manifest bullet만 트림.

### 3.3 `AGENTS.md :: ## Harness Evaluation` (L83-85)
- **조치**: SHRINK → 1줄 포인터 / **위치**: harness-evaluation 스킬 / **위험** low / **신뢰** medium / **diet 자동** ✅
- ⚖️ **SOFTEN (low)**: 스킬 auto-activation은 사용자가 *요청할 때만* 발화. 그러나 이 resident 트리거는 "스킬 추가/AGENTS·README 변경/기존 repo 편입" 같은 **다른 작업의 부수효과** 케이스를 덮는다 — 이 경우 auto-activation은 안 됨. 제거 시 하네스 변경이 미평가로 ship될 수 있음. 순수 중복 아님 → 1줄은 남길 것.

### 3.4 `AGENTS.md :: Professor-Led Lab / Startup / Hard-Gates 내부 중복` (L20-60)
- **조치**: SHRINK 내부 반복 / **위치**: orchestration_protocol.md가 roster 소유 / **위험** medium / **신뢰** medium / **diet 자동** ❌
- ⚖️ **NEEDS_HUMAN (residual high)**: 결정-게이트 브레이크의 L27/L51 **이중 기재는 의도적 안전 중복**(긴 컨텍스트에서 단일 언급은 유실 가능). 어느 사본을 지울지는 **PI의 안전 판단**.

### 3.5 `scientific-verification-before-claim` + `claim-to-evidence` (병합)
- **문제**: claim-promotion 동일 순간을 두 스킬이 거의 동일한 red-flag 목록으로 감시(ladder만 7-rung vs 11-type 상이), 둘 다 매우 광범위 트리거
- **조치**: SHRINK → 단일 claim-promotion 스킬 / **위험** medium / **신뢰** medium / **diet 자동** ❌
- ⚖️ **NEEDS_HUMAN (medium)**: 이 둘은 **하드 claim-promotion 게이트**(`path_check_hooks.py:259`, docs/claims/*.md 쓰기 차단)를 뒷받침. 병합 시 **체커가 실제 파싱하는 ladder를 보존**해야 — 안 그러면 모든 claim 쓰기가 블록되거나 malformed lifecycle이 통과. 라이브 체커 대조 검증 필수.

### 3.6 `research-plan-review` + `researcher-review-loop` (병합)
- **조치**: SHRINK → 단일 researcher-review 스킬 / **위험** medium / **신뢰** medium / **diet 자동** ❌
- ⚖️ **UPHOLD (low)** — *가장 안전한 SHRINK 중 하나*: 이 산출물을 강제하는 체커가 **없음**(Planner 검증) → 하드 게이트 desync 불가. 단, human-in-the-loop 해석/산출 분리와 물리 고유 라벨(needs-baseline/needs-units/overclaims/too-broad), 결정 로깅 단계는 보존.

### 3.7 `numerical-validation`
- **조치**: SHRINK → 수렴/안정성/보존 체크리스트를 공유 doc로 factor / **위험** medium / **신뢰** medium / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)**: factor-and-reference는 좋은 DRY이나, 각 소비 스킬이 공유 doc를 **실제로 로드**할 때만 안전. 미수렴 격자·발산 적분기·보존 위반(=silent-wrong-number)을 잡는 핵심 방어 → 인라인 중복이 더 안전한 기본값일 수 있음.

### 3.8 `task-intake`
- **조치**: SHRINK — classification 표 + orient_note 템플릿 유지, AGENTS.md와 겹치는 gate-order/waiver recap 제거 / **위험** medium / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)**: task-intake는 **Orient 첫 행동**(AGENTS.md L41). waiver claim-ceiling(literature→interpretation, model→observation)이 *바로 이 결정 시점*에 앞에 있어야 다운스트림 주장 강도를 제한. Suggested-Next-Skill 중복만 트림, **waiver/claim-ceiling recap은 유지**.

### 3.9 `seed-design`
- **조치**: SHRINK — task-structure/sizing/Task-1 유지, spawn 메커니즘은 orchestration_protocol.md 참조 / **위험** medium / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)**: 내장 spawn-block 포맷은 `check_src_write_authorization.py`·`check_peer_review_invocation.py`가 검사하는 spawn 프롬프트로 직결 — **하드 게이트 machinery에 근접**. 참조 전환은 orchestration_protocol.md의 spawn block이 완전·확실 로드됨을 확인한 뒤에만. Task-Orchestration Mapping Rule만 안전 트림.

### 3.10 `workflow_hooks.py 죽은 배선` (settings L17·40·47)
- **조치**: SHRINK — Agent matcher(L8 pre, L33 post)만 남기고 Write|Edit·Bash|PowerShell 슬롯 제거 / **위험** low / **신뢰** high / **diet 자동** ⚠️(권한/hook 변경이라 PI 승인 — 본 단계 범위 밖)
- ⚖️ **UPHOLD (low)** — *세트 내 가장 깨끗한 latency win*: `main()`이 non-Agent에서 즉시 0 반환(L281-282) → 잃을 동작 0. Agent 슬롯만 건드리지 말 것.

### 3.11 `path_check_hooks.py Bash|PowerShell post 배선` (settings L48)
- **조치**: SHRINK — figure-provenance를 Write|Edit of outputs/figures/*로 좁히고 blanket Bash post 제거 / **위험** medium / **diet 자동** ❌
- ⚖️ **DOWNGRADE_TO_KEEP (residual medium)** — *반박이 뒤집음*: shell 생성 파일은 file_path가 없어(L266-268) 이 blanket 엔트리가 존재. 물리 워크플로우에서 **그림은 대개 `python plot.py` 등 Bash로 생성** → Write|Edit-only로 좁히면 지배적 그림 생성 경로가 provenance 검사에 **invisible**(Core Principle 7 위반). 대체 커버리지 없으면 좁히지 말 것.

---

## 4. 전역 지침 → Skill로 옮길 항목 (MOVE — 2)

### 4.1 `AGENTS.md :: ## Preferred Response Format` (L107-122)
- **문제**: 5섹션(Summary/Physical Impact/Validation/Caveats/Next Action) 템플릿을 *모든* 세션(사소한 Q&A 포함)에 무조건 pin
- **조치**: MOVE → deliverable 스킬(research-plan-review/claim-to-evidence/baseline-validation) 또는 조건부 포인터 / **위험** medium / **신뢰** medium / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)**: **Validation/Caveats는 장식이 아니라 "실제 실행한 것 vs 미해결 불확실성"을 매 응답에서 분리시키는 forcing function** — docs/claims를 안 건드리는 대화형 답변(과주장이 실제로 발생하는 곳)에서 claim-strength 규율의 resident 등가물. 옮기려면 **Validation+Caveats는 resident로 유지**하고 "사소한 턴은 skip" 절을 추가하는 방향이 맞음.

### 4.2 `AGENTS.md :: ## Local Instructions L6-7` (GEMINI/README sync 계약)
- **문제**: repo 유지보수/기여자 규칙이 매 연구 세션에 pin. 하네스 자체 편집 시에만 유효
- **조치**: MOVE → CONTRIBUTING.md / 하네스-유지보수 doc / **위험** medium / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)**: `check_contract_sync.py`로 강제되나, resident 문구는 체커가 못 하는 일을 함 — "**같은 체크포인트에서** 매칭 편집을 하라". "하네스 편집 작업일 때만 로드"는 bootstrap 문제(이미 AGENTS.md를 편집한 뒤에야 그 작업임을 앎). GEMINI-sync 줄은 유지, **README-sync 줄이 더 약함 → 이동 가능**.

---

## 5. Skill에서 reference.md / examples.md로 분리할 항목 (SPLIT — 1)

### 5.1 `literature-review-planning/SKILL.md` (181줄, 최장; 25개 중 분리된 스킬 0)
- **문제**: 내구성 8단계 루프 + 장문 reference(18항목 Detailed Review Standard, **한국어 컬럼 헤더(판정/비고, 확인 필요) — 재사용 스킬에 박힌 프로젝트 고유 drift**, lineage front-matter spec, 5스크립트 카탈로그) 혼재
- **조치**: SPLIT — SKILL.md는 루프+게이트/waiver 유지, 나머지는 reference.md로 / **위험** low / **신뢰** high / **diet 자동** ✅
- ⚖️ 반박 없음(저위험 기계적 분리).

---

## 6. 삭제 후보 (DELETE — 1)

### 6.1 `.claude/commands/{task-intake,dimensional-analysis,meeting,sync-workflow,harness-evaluation,anomaly-debugging,existing-research-onboarding}.md`
- **문제**: skills/<n>/SKILL.md와 **바이트 동일**(diff -q empty 검증). Claude가 스킬을 auto-expose → 커맨드층은 내용 0 추가하며 2번째 저장
- **조치**: DELETE / **위험** medium / **신뢰** high / **diet 자동** ❌
- ⚖️ **SOFTEN (medium)** — *세트 내 가장 중요한 반박*: 슬래시 커맨드 = **명시적·결정론적 진입점**, 스킬 auto-activation = **모델 판단·확률적**(miss 가능). 하필 이 7개가 감싸는 게 워크플로우 임계 의식 — `/meeting`(peer-review 교수를 합법 spawn하는 유일 게이트 경로), `/sync-workflow`(결정론적 상태 갱신), `/task-intake`(필수 Orient 첫 단계). 통삭제는 **결정론 → 확률**로의 회귀. **권고 수정: 완전 삭제 대신 스킬을 가리키는 thin command 스텁으로 축소.**

---

## 7. 사람이 직접 승인해야 하는 위험한 변경 (NEEDS_HUMAN / 안전 임계)

| 항목 | 조치 | 왜 PI 결정인가 |
|---|---|---|
| AGENTS.md 내부 중복(브레이크 이중 기재) §3.4 | SHRINK | 결정-게이트 브레이크 의도적 중복 — 어느 사본 삭제할지는 안전 판단 |
| claim 스킬 병합 §3.5 | SHRINK | 하드 claim-promotion 게이트가 파싱하는 ladder를 깨면 모든 claim 쓰기 블록/malformed 통과. 라이브 체커 대조 필요 |
| `peer-review-professor` CONVERT (§8) | CONVERT | `check_peer_review_invocation.py`가 **role명/스킬 경로 문자열**로 감지 → 경로 변경 시 meeting-only 게이트가 조용히 열림 |
| hook 단일 dispatcher 통합 §8(scripts) | CONVERT | 현재 fan-out은 **fault isolation** 보유(프로세스별 독립 exit-2). 단일 프로세스화 시 1개 버그가 **여러 하드 게이트 동시 무력화** 가능. 각 게이트 블록 보존 테스트 필수 — 안전 machinery 코드 변경 |
| figure-provenance 좁히기 §3.11 | (DOWNGRADE→KEEP) | shell 생성 그림 커버리지 상실 → 사실상 유지 권고 |
| Response Format 이동 §4.1 / contract 이동 §4.2 | MOVE | Validation/Caveats·GEMINI-sync는 resident 유지 조건부로만 |

> **공통 원칙**: hook/MCP/권한/allowed-tools 변경은 본 감사의 명시적 금지 범위였고, 위 항목 다수가 거기에 해당하므로 **/harness-diet 자동 처리 대상이 아니다.**

---

## 8. CONVERT 항목 (스킬+에이전트 스텁 병합 — 7)

> 6개 스킬+에이전트 쌍 + hook fan-out 1개. 공통 동기: 11줄 스텁("do not auto-trigger") ↔ 스킬("spawned 되면 로드") **트리거 모순 해소**. 방향: 스킬 본문을 에이전트 파일로 fold(스텁이 *대상*, 제거 대상 아님).

| 경로 | 위험 | 신뢰 | ⚖️ verdict | 보존 필수(load-bearing) |
|---|---|---|---|---|
| `code-reviewer` 스킬+스텁 | low | high | **UPHOLD** | tool allowlist **no-Bash**(author≠validator) + 물리 체크리스트 |
| `cache-log-auditor` 스킬+스텁 | low | high | **UPHOLD** | 보고서 템플릿 + 스크립트 호출 |
| `graduate-student` 스킬+스텁 | medium | high | **SOFTEN** | spawn-log-row 프로토콜(`check_src_write_authorization.py`가 의존) **byte-for-byte** 보존 안 하면 정당한 grad 쓰기 전부 블록 |
| `scientific-validator` 스킬+스텁 | medium | high | **SOFTEN** | 독립성/verdict ceiling, AGENTS.md L26/73 등 **교차참조 lockstep 갱신** |
| `workflow-manager` 스킬+스텁 | medium | medium | **SOFTEN** | thin caller 유지(통삭제 X) — 병렬 grad 배치 후 lineage 갱신 위임 경로 |
| `peer-review-professor` 스킬+스텁 | medium | medium | **NEEDS_HUMAN** | hook 감지 문자열(role/스킬 경로) lockstep 안 하면 게이트 조용히 열림 |
| `scripts/*.py` per-matcher fan-out | medium | medium | **NEEDS_HUMAN** | fault isolation 상실 위험 — 게이트별 블록 보존 테스트 필수 |

---

## 9. /harness-diet 처리 분류

### 9a. /harness-diet로 넘겨도 되는 low-risk 변경 (자동 가능)
순수 컨텍스트/저장 정리, 하드 게이트·권한·hook 미접촉, 반박 검토 통과:

1. **§5.1 SPLIT** `literature-review-planning/SKILL.md` → SKILL.md(루프+게이트) + reference.md(Detailed Review Standard/rubric/스크립트 카탈로그). *완전 자동 가능, 위험 low.*
2. **§3.1 SHRINK** AGENTS.md Scientific Hook Index → 포인터 + **soft-hook 1줄 요약 유지**(반박 조건 준수). *반자동.*
3. **§3.3 SHRINK** AGENTS.md Harness Evaluation → 1줄 포인터(부수효과 트리거 1줄 유지). *반자동.*
4. **§3.2 SHRINK** AGENTS.md Hard-Enforced Gates → CI/manifest bullet만 트림, **L51 브레이크/L52 cross-tier 유지**. *반자동, 보수적.*

> ⚠️ **§3.10(workflow_hooks 죽은 배선)은 명백한 win이지만 settings.json/hook 변경 = 본 감사 금지 범위 → 9a에서 제외**, PI 승인 후 별도 적용.

### 9b. /harness-diet 부적합 (사람 승인)
§3.4·3.5·3.7·3.8·3.9, §4.1·4.2, §6.1, §8 전부, §3.11 — 하드 게이트/spawn machinery/제품-결정론 트레이드오프 결속.

### 9c. /harness-diet 실행용 추천 프롬프트

```
/harness-diet

스코프: 아래 4개 low-risk 정리만 적용. 하드 게이트·hook·MCP·권한·allowed-tools·
        settings.json·결정 게이트 파일은 절대 건드리지 마. 적용 전 각 변경의 diff를
        보여주고 내 승인을 받아.

1. [SPLIT] skills/literature-review-planning/SKILL.md 를 분리:
   - SKILL.md = 8단계 루프 + 게이트/waiver 만 유지
   - reference.md = 18항목 Detailed Review Standard + Review Agent rubric
     (한국어 컬럼 헤더 포함) + 5-스크립트 카탈로그 + lineage front-matter spec

2. [SHRINK] AGENTS.md "## Scientific Hook Index" → docs/hooks_reference.md 포인터 1줄.
   단, 스크립트 미강제 soft hook 목록(Ambiguity, Assumption/Units, Claim Strength,
   Reviewer Simulation, Negative Result, Scope Creep, Anomaly)은 한 줄 요약으로 resident 유지.

3. [SHRINK] AGENTS.md "## Harness Evaluation" → 1줄 포인터. 단 "스킬 추가/AGENTS·README·
   PHYSICS 변경/기존 repo 편입 시 평가" 부수효과 트리거 문구는 유지.

4. [SHRINK] AGENTS.md "## Hard-Enforced Gates" → CI/Capability-Manifest/Spawn-Contract
   bullet만 reference로 트림. Human-Owned Decision Gate(브레이크)와 Cross-Tier Write
   라우팅 문장은 글자 그대로 유지.

제약: AGENTS.md를 바꾸면 GEMINI.md를 동일하게 맞추고
      python scripts/check_contract_sync.py 를 실행해 통과 확인.
      README.md/README.ko.md에 영향 있으면 같은 체크포인트에서 갱신.
별도 처리(자동 금지): workflow_hooks.py 죽은 배선 제거, 스킬+에이전트 CONVERT 6쌍,
      claim/researcher 스킬 병합, Response Format 이동 — 전부 내 수동 승인 후 진행.
```

---

*근거 데이터: 워크플로우 결과 JSON `/tmp/.../tasks/w6qmmo9xh.output` (inventory 61항목, perspective findings 49, classified 40, adversarial 21). 모든 "검증됨" 표기는 에이전트의 실제 파일 read/diff/라인 인용에 기반.*
