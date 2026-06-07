import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "check_claim_promotion_freshness.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_claim_promotion_freshness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_claim_promotion_freshness"] = module
    spec.loader.exec_module(module)
    return module


def make_project(tmp_path: Path, evidence: str = "outputs/data/direct_read.csv") -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".research-harness").write_text("test project\n", encoding="utf-8")
    target = project / evidence
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fresh evidence\n", encoding="utf-8")
    (project / "docs" / "claims").mkdir(parents=True)
    return project


CANDIDATE_CLAIM = """\
ceiling: mechanism

## Claim

outputs/data/direct_read.csv supports this mechanism.

## Finding Lifecycle

### Finding

Status: candidate

### Evidence Paths Read Directly

- outputs/data/direct_read.csv
"""


VALIDATED_WITHOUT_DIRECT_READ = """\
ceiling: mechanism

## Claim

outputs/data/direct_read.csv supports this mechanism.

## Finding Lifecycle

### Finding

Status: independently_checked

### Independent Check

Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

"""


VALIDATED_WITH_DIRECT_READ = """\
ceiling: mechanism

## Claim

outputs/data/direct_read.csv supports this mechanism.

## Finding Lifecycle

### Finding

Status: independently_checked

### Independent Check

Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

- outputs/data/direct_read.csv
"""


INTERPRETATION_WITHOUT_LIFECYCLE = """\
ceiling: interpretation

## Claim

outputs/data/direct_read.csv supports this interpretation.
"""


def test_freshness_rejects_candidate_mechanism_claim(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)

    result = checker.check_claim_freshness(
        project / "docs" / "claims" / "claim_alpha.md",
        CANDIDATE_CLAIM,
        project,
    )

    assert result.status == "fail"
    assert "candidate" in result.reason.lower()


def test_freshness_rejects_missing_direct_read_paths_for_mechanism(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)

    result = checker.check_claim_freshness(
        project / "docs" / "claims" / "claim_alpha.md",
        VALIDATED_WITHOUT_DIRECT_READ,
        project,
    )

    assert result.status == "fail"
    assert "evidence paths read directly" in result.reason.lower()


def test_freshness_rejects_unresolved_direct_read_paths_for_mechanism(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)
    claim = VALIDATED_WITH_DIRECT_READ.replace(
        "- outputs/data/direct_read.csv",
        "- outputs/data/missing.csv",
    )

    result = checker.check_claim_freshness(
        project / "docs" / "claims" / "claim_alpha.md",
        claim,
        project,
    )

    assert result.status == "fail"
    assert "unresolved" in result.reason.lower()


def test_freshness_accepts_validated_direct_read_mechanism_claim(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)

    result = checker.check_claim_freshness(
        project / "docs" / "claims" / "claim_alpha.md",
        VALIDATED_WITH_DIRECT_READ,
        project,
    )

    assert result.status == "pass"


def test_freshness_interpretation_claim_does_not_require_lifecycle(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)

    result = checker.check_claim_freshness(
        project / "docs" / "claims" / "claim_alpha.md",
        INTERPRETATION_WITHOUT_LIFECYCLE,
        project,
    )

    assert result.status == "pass"


def test_check_project_reports_lifecycle_failures(tmp_path):
    checker = load_checker()
    project = make_project(tmp_path)
    claim = project / "docs" / "claims" / "claim_alpha.md"
    claim.write_text(CANDIDATE_CLAIM, encoding="utf-8")

    code, messages = checker.check_project(project)

    assert code == 1
    assert any("candidate" in message.lower() for message in messages)
