export const meta = {
  name: 'harness-legacy-scan',
  description: 'Read-only audit of an AI coding/research harness: find stale rules, duplication, global-context tax, over-broad skills, product overlap, risky permissions. Report only — never modifies, deletes, or touches files/hooks/MCP/permissions. Optional args: { root: "<abs path>" } (defaults to this repo).',
  whenToUse: 'Run when you want to audit the harness itself for legacy cruft before a /harness-diet pass. Produces a classified findings report (KEEP/SHRINK/MOVE/SPLIT/CONVERT/DELETE) with an adversarial counter-review. Read-only.',
  phases: [
    { title: 'Inventory' },
    { title: 'Perspectives' },
    { title: 'Plan' },
    { title: 'Adversarial' },
  ],
}

// Project root: caller may pass { root } via Workflow args; otherwise this repo.
const ROOT = (args && args.root) || '/home/complexitylab/ResearchPartner'

const CONTEXT = `
You are auditing an AI coding/research harness rooted at ${ROOT}. THIS IS STRICTLY READ-ONLY.
ABSOLUTE CONSTRAINTS: Do NOT modify, create, or delete any file. Do NOT edit hooks, MCP config, or permissions/allowed-tools. Use only Read/Grep/Glob/Bash-for-reading (ls, cat, diff, wc, find — never write/redirect). Report findings only.

AUDIT SCOPE (discover what actually exists; not all may be present):
- Root instruction files: CLAUDE.md, AGENTS.md, GEMINI.md, PHYSICS.md (and any *.md that is @-imported or auto-loaded every session).
- skills/** and/or .claude/skills/** (each skill's SKILL.md, plus any reference.md / examples.md).
- .claude/commands/**, .claude/agents/**, .agents/workflows/** (and any runtime mirrors).
- .claude/settings.json and .claude/settings.local.json (hooks, permissions, allowed-tools, env).
- .cursor/rules/** if present.
- MCP config files if present (search for *mcp* and "mcpServers" keys).
- Hook implementation scripts referenced by settings (commonly scripts/*.py).

AUDIT PHILOSOPHY (apply this lens):
- A good harness prevents recurring REAL mistakes; it must not exist to preserve old habits.
- The harness should appear only when needed, not be globally pinned (every byte in an always-loaded file is a per-session context tax).
- Goal: find and CLASSIFY candidates to shrink/remove, NOT add rules.

KEY DISTINCTIONS to verify with your own reads (do not assume):
- What loads EVERY session (CLAUDE.md and its @-imports, settings hooks) vs what loads on demand (skills, commands, agents, docs).
- Duplication: redirect/identity chains (CLAUDE->AGENTS->GEMINI), triple-stored skills (skills/ == .claude/commands/ == .agents/workflows/), agent stubs that only point at a same-named skill. Use 'diff -q' / 'wc -l' to prove byte-identity, never eyeball it.
- Hooks: which fire deterministic blocks (exit 2) vs warn-only (exit 0); which are wired but no-op (dead wiring); which over-trigger (e.g. fire on every Bash). Read the hook scripts' main()/early-exit logic.
- Permissions: whether settings declares allowed-tools/deny at all; whether any env var or hook GRANTS rather than restricts.
- Product overlap: rules/skills/commands now covered by built-in product features (Claude Code /code-review, /review, /security-review, /init, /verify, /run, subagents/Agent tool, hooks framework, settings permissions, memory, plan mode; Cursor/Codex equivalents).
`

const FINDING_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          path: { type: 'string', description: 'file or config path / section' },
          purpose: { type: 'string', description: 'current purpose, 1 sentence' },
          problem: { type: 'string', description: 'the staleness/duplication/overbreadth problem found' },
          evidence: { type: 'string', description: 'concrete evidence: quote, line, size, diff result, overlap' },
          recommendation: { type: 'string', enum: ['KEEP', 'SHRINK', 'MOVE', 'SPLIT', 'CONVERT', 'DELETE'] },
          target_location: { type: 'string', description: 'where to move/split to, or "-" if N/A' },
          risk: { type: 'string', enum: ['low', 'medium', 'high'], description: 'risk of making the change' },
          confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
          harness_diet_auto: { type: 'boolean', description: 'can /harness-diet safely automate this?' },
        },
        required: ['path', 'purpose', 'problem', 'evidence', 'recommendation', 'target_location', 'risk', 'confidence', 'harness_diet_auto'],
      },
    },
  },
  required: ['findings'],
}

// ---- Phase 1: Inventory ----
phase('Inventory')
const INV_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          path: { type: 'string' },
          kind: { type: 'string', description: 'global-context | skill | agent | command | workflow-mirror | settings | hook-script | mcp | cursor-rule | domain-doc | other' },
          size: { type: 'string', description: 'lines or bytes' },
          purpose: { type: 'string' },
          load_trigger: { type: 'string', description: 'when it loads: every-session | on-skill-invoke | on-command | on-hook | never' },
        },
        required: ['path', 'kind', 'size', 'purpose', 'load_trigger'],
      },
    },
    notes: { type: 'string', description: 'duplication/mirroring observations across the set (prove byte-identity with diff -q)' },
  },
  required: ['items', 'notes'],
}
const inventory = await agent(
  `${CONTEXT}\n\nTASK (Inventory Agent): Catalogue every harness-related file/config in scope under ${ROOT}. Discover them yourself with find/ls/Glob — do not assume a layout. For each, record path, kind, size, purpose, and load_trigger (every-session vs on-demand). Prove every duplication claim with 'diff -q' or matching 'wc -l'. Pay special attention to: (a) what is pinned every session vs loaded on demand, (b) redirect/identity chains and triple-stored skills, (c) skills that mirror .claude/agents 1:1. Return the structured inventory.`,
  { label: 'inventory', phase: 'Inventory', schema: INV_SCHEMA }
)

const invText = JSON.stringify(inventory, null, 2)
const SHARED = `${CONTEXT}\n\nINVENTORY (from Inventory Agent — verify, do not blindly trust):\n${invText}\n`

// ---- Phase 2: Perspective finders (barrier: planner needs all four) ----
phase('Perspectives')
const PERSPECTIVES = [
  {
    key: 'global-context-tax',
    prompt: `TASK (Global Context Tax Agent): Analyze the ALWAYS-RESIDENT instructions (CLAUDE.md, AGENTS.md, GEMINI.md, and anything @-imported every session; check whether PHYSICS.md is @-imported). Every byte here costs context in EVERY session. Find: (1) rules pinned globally that only matter in narrow situations (should be a skill, loaded on demand); (2) redirect/duplication chains and whether keeping mirrored files byte-identical earns its cost; (3) long hook indices / gate catalogs embedded in the resident file that merely duplicate a reference doc; (4) prose restating product defaults; (5) verbose blocks that could SHRINK or MOVE to a doc/skill. Read the resident files fully. Quote specific sections + line ranges as evidence. NOTE: a catalog entry whose underlying rule is a SOFT (script-unenforced) behavioral hook may be the only resident trace of that rule — flag those for SHRINK-with-residual-summary, not blind removal.`,
  },
  {
    key: 'skill-quality',
    prompt: `TASK (Skill Quality Agent): Review every skill (skills/** and/or .claude/skills/**). For each notable one assess: (1) is it still needed / does it map to a real recurring mistake; (2) is its description too broad (would it trigger on unrelated tasks); (3) is SKILL.md too long (candidate to SPLIT into reference.md/examples.md — note whether any are currently split); (4) does it overlap another skill OR a same-named .claude/agents agent (find such pairs and check for trigger-semantics contradictions, e.g. "load when spawned" vs "do not auto-trigger"). Read several SKILL.md files (the largest and any agent-duplicated ones). Report per-skill findings with line counts as evidence.`,
  },
  {
    key: 'product-overlap',
    prompt: `TASK (Product Overlap Agent): Find harness rules/skills/commands that now duplicate BUILT-IN product features of Claude Code / Codex / Cursor (e.g. /code-review, /review, /security-review, /init, /verify, /run, subagents/Agent tool, hooks framework, settings permissions, memory, plan mode). For each candidate state the product feature it overlaps and whether the harness copy adds REAL value (e.g. physics-specific checks, gate enforcement, tool-allowlist restrictions, deterministic invocation) or is redundant. Distinguish "deterministic slash-command entry point" (real value) from "model-judged skill auto-trigger". Read the relevant SKILL.md/command/agent files.`,
  },
  {
    key: 'safety-permission',
    prompt: `TASK (Safety and Permission Agent): Analyze settings.json / settings.local.json and the hook scripts they call. Assess: (1) does settings declare allowed-tools/deny at all, and does its absence imply over-broad default access or constant prompts; (2) are any hook matchers over-broad (Write|Edit on everything, Bash on everything) causing friction or over-trigger; (3) is any hook wired but dead (no-ops by construction — read main()/early-exit); (4) does any hook or env var GRANT rather than restrict (find the only "grant" surfaces and confirm they cannot waive human-owned decision gates). DO NOT propose editing hooks/permissions as auto-changes — classify only, and mark such items harness_diet_auto=false. Read settings and the referenced scripts.`,
  },
]

const perspectiveResults = await parallel(
  PERSPECTIVES.map((p) => () =>
    agent(`${SHARED}\n\n${p.prompt}`, { label: p.key, phase: 'Perspectives', schema: FINDING_SCHEMA })
      .then((r) => ({ key: p.key, findings: (r && r.findings) || [] }))
  )
)

const allFindings = perspectiveResults.filter(Boolean).flatMap((r) =>
  r.findings.map((f) => ({ ...f, source: r.key }))
)
const findingsText = JSON.stringify(allFindings, null, 2)

// ---- Phase 3: Refactor Planner (barrier: needs all findings to dedupe) ----
phase('Plan')
const PLAN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    classified: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          path: { type: 'string' },
          recommendation: { type: 'string', enum: ['KEEP', 'SHRINK', 'MOVE', 'SPLIT', 'CONVERT', 'DELETE'] },
          rationale: { type: 'string' },
          target_location: { type: 'string' },
          risk: { type: 'string', enum: ['low', 'medium', 'high'] },
          confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
          harness_diet_auto: { type: 'boolean' },
        },
        required: ['path', 'recommendation', 'rationale', 'target_location', 'risk', 'confidence', 'harness_diet_auto'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['classified', 'summary'],
}
const plan = await agent(
  `${CONTEXT}\n\nALL PERSPECTIVE FINDINGS:\n${findingsText}\n\nTASK (Refactor Planner): Consolidate and DEDUPLICATE the findings into one classification per distinct item, each labeled KEEP / SHRINK / MOVE / SPLIT / CONVERT / DELETE. Merge findings about the same path. Resolve conflicts (if two agents disagree, pick the safer call and note it). Verify load-bearing or conflicting claims directly (re-read the file / re-run diff) before classifying. Be conservative: prefer SHRINK/MOVE/SPLIT over DELETE unless redundancy is proven. Mark harness_diet_auto=true ONLY for mechanical low-risk changes (move a block to a doc, split a long SKILL.md). NEVER mark hook/permission/MCP changes as auto. Return the consolidated classification + a short summary.`,
  { label: 'refactor-planner', phase: 'Plan', schema: PLAN_SCHEMA }
)

// ---- Phase 4: Adversarial Reviewer ----
phase('Adversarial')
const riskyItems = (plan.classified || []).filter(
  (c) => c.recommendation !== 'KEEP'
)
const ADV_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    challenges: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          path: { type: 'string' },
          proposed: { type: 'string', description: 'the planner recommendation being challenged' },
          counterargument: { type: 'string', description: 'why removing/shrinking could be dangerous or wrong; cite the failure it prevents' },
          verdict: { type: 'string', enum: ['UPHOLD', 'DOWNGRADE_TO_KEEP', 'NEEDS_HUMAN', 'SOFTEN'], description: 'UPHOLD=safe to proceed; DOWNGRADE_TO_KEEP=do not change; NEEDS_HUMAN=PI must decide; SOFTEN=do a gentler version' },
          residual_risk: { type: 'string', enum: ['low', 'medium', 'high'] },
        },
        required: ['path', 'proposed', 'counterargument', 'verdict', 'residual_risk'],
      },
    },
  },
  required: ['challenges'],
}
const adversarial = await agent(
  `${CONTEXT}\n\nPLANNER RECOMMENDATIONS TO CHALLENGE (everything except KEEP):\n${JSON.stringify(riskyItems, null, 2)}\n\nTASK (Adversarial Reviewer): For EACH item, argue the opposite — what real mistake or safety property would be LOST if we removed/shrank/moved it. Remember this is a SCIENTIFIC harness: gates, claim-strength controls, reproducibility, figure provenance, and the human-owned decision brake exist to prevent specific failures. Two patterns to watch: (a) SOFT hooks have no script enforcement, so resident text may be their ONLY trace — shrinking it deletes the rule; (b) hooks that detect by role-name/skill-path strings break silently if a CONVERT renames the path. Flag anything load-bearing for a hard-enforced gate as DOWNGRADE_TO_KEEP or NEEDS_HUMAN. Verify with reads where needed. Give a verdict and residual risk per item.`,
  { label: 'adversarial-reviewer', phase: 'Adversarial', schema: ADV_SCHEMA }
)

return {
  root: ROOT,
  inventory,
  perspectiveResults,
  allFindings,
  plan,
  adversarial,
}
