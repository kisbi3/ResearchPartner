import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "check_claim_promotion.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_claim_promotion", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_claim_promotion"] = module
    spec.loader.exec_module(module)
    return module


def make_project(
    tmp_path: Path,
    validation_rows: list[tuple[str, str, str, str, str]] | None = None,
    claim_body: str | None = None,
    evidence_paths: tuple[str, ...] = ("outputs/data/direct_read.csv",),
) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".research-harness").write_text("test project\n", encoding="utf-8")
    gates = project / "docs" / "gates"
    claims = project / "docs" / "claims"
    gates.mkdir(parents=True)
    claims.mkdir(parents=True)
    for rel_path in evidence_paths:
        target = project / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("evidence\n", encoding="utf-8")
    rows = validation_rows or []
    body = (
        "# Validation Log\n\n"
        "| Date | Check | Target | Status | Evidence |\n"
        "|---|---|---|---|---|\n"
    )
    for row in rows:
        body += "| " + " | ".join(row) + " |\n"
    (gates / "validation_log.md").write_text(body, encoding="utf-8")
    if claim_body is not None:
        (claims / "claim_alpha.md").write_text(claim_body, encoding="utf-8")
    return project


def validation_rows(*checks: str) -> list[tuple[str, str, str, str, str]]:
    return [
        ("2026-05-26", check, "claim_alpha", "pass", "outputs/data/direct_read.csv")
        for check in checks
    ]


CANDIDATE_MECHANISM_CLAIM = """\
---
lineage:
  claim_ceiling: mechanism
---
ceiling: mechanism

## Claim

The pattern reveals the mechanism.

## Finding Lifecycle

### Finding

Status: candidate
Claim affected: claim_alpha
Evidence paths:
- outputs/data/direct_read.csv

### Evidence Paths Read Directly

- outputs/data/direct_read.csv
"""


VALIDATED_WITHOUT_DIRECT_READ = """\
ceiling: mechanism

## Claim

The pattern reveals the mechanism.

## Finding Lifecycle

### Finding

Status: independently_checked
Claim affected: claim_alpha
Evidence paths:
- outputs/data/direct_read.csv

### Independent Check

Checker: scientific-validator
Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

"""


VALIDATED_WITH_DIRECT_READ = """\
ceiling: mechanism

## Claim

The pattern reveals the mechanism.

## Finding Lifecycle

### Finding

Status: independently_checked
Claim affected: claim_alpha
Evidence paths:
- outputs/data/direct_read.csv

### Independent Check

Checker: scientific-validator
Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

- outputs/data/direct_read.csv

### Decision

Decision: evidence_linked
Claim ceiling effect: mechanism allowed
"""


def test_candidate_finding_cannot_promote_mechanism(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "conservation"),
        CANDIDATE_MECHANISM_CLAIM,
    )

    assert checker.main(["--project", str(project), "--target", "mechanism"]) == 2


def test_validated_finding_without_direct_evidence_paths_fails(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "conservation"),
        VALIDATED_WITHOUT_DIRECT_READ,
    )

    assert checker.main(["--project", str(project), "--target", "mechanism"]) == 2


def test_validated_finding_with_unresolved_direct_evidence_path_fails(tmp_path):
    checker = load_checker()
    claim = VALIDATED_WITH_DIRECT_READ.replace(
        "outputs/data/direct_read.csv",
        "outputs/data/missing.csv",
    )
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "conservation"),
        claim,
        evidence_paths=(),
    )

    assert checker.main(["--project", str(project), "--target", "mechanism"]) == 2


def test_validated_evidence_linked_directly_read_finding_can_promote(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "conservation"),
        VALIDATED_WITH_DIRECT_READ,
    )

    assert checker.main(["--project", str(project), "--target", "mechanism"]) == 0


def test_interpretation_keeps_existing_count_gate_without_finding_lifecycle(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path, validation_rows("numerical_stability"))

    assert checker.main(["--project", str(project), "--target", "interpretation"]) == 0


def test_observation_keeps_existing_no_evidence_behavior(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)

    assert checker.main(["--project", str(project), "--target", "observation"]) == 0


def test_mechanism_still_requires_baseline_class(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("parameter_sweep", "numerical_stability"),
        VALIDATED_WITH_DIRECT_READ,
    )

    assert checker.main(["--project", str(project), "--target", "mechanism"]) == 2


def test_generalization_still_requires_two_check_categories(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "toy_model", "toy_model"),
        VALIDATED_WITH_DIRECT_READ.replace("ceiling: mechanism", "ceiling: generalization"),
    )

    assert checker.main(["--project", str(project), "--target", "generalization"]) == 2


def test_generalization_with_valid_finding_and_diversity_passes(tmp_path):
    checker = load_checker()
    project = make_project(
        tmp_path,
        validation_rows("toy_model", "conservation", "parameter_sweep"),
        VALIDATED_WITH_DIRECT_READ.replace("ceiling: mechanism", "ceiling: generalization"),
    )

    assert checker.main(["--project", str(project), "--target", "generalization"]) == 0
