import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_baseline_strategy.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_baseline_strategy", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_baseline_strategy"] = module
    spec.loader.exec_module(module)
    return module


def make_run(tmp_path: Path, strategy_body: str | None) -> Path:
    run = tmp_path / "run"
    docs = run / "docs"
    docs.mkdir(parents=True)
    if strategy_body is not None:
        (docs / "baseline_strategy.md").write_text(strategy_body, encoding="utf-8")
    return run


VARIATION_BODY = """\
# Baseline Strategy

## Decision

variation

## Rationale

This model extends Smith 2019 by adding a next-nearest-neighbour coupling.

## Variation Path

### Parent Model

Smith et al. 2019, Phys. Rev. B 100, 014412

### Key Result to Reproduce

Magnetization vs. temperature curve, Fig. 3a

### Reproduce Pass Criterion

Magnetization at T/J = 0.5 matches within 5% of the value reported in Smith 2019 Fig. 3a.
"""

NEW_MODEL_BODY = """\
# Baseline Strategy

## Decision

new model

## Rationale

This model has no direct published parent; it introduces a novel frustrated geometry.

## New Model Path

### Analytical Checkpoint 1

Mean-field theory prediction for the paramagnetic phase.

**Expected result:**

Magnetization m = tanh(z*J*m/kT) with coordination number z = 6.

**Pass criterion:**

Code reproduces mean-field magnetization within 2% at T/J < 0.1.
"""


def test_missing_file_fails(tmp_path):
    checker = load_checker()
    run = make_run(tmp_path, None)
    code, messages = checker.check_run(run)
    assert code == 1
    assert "missing" in messages[0].lower()


def test_no_decision_fails(tmp_path):
    checker = load_checker()
    body = "# Baseline Strategy\n\n## Decision\n\n<!-- FILL IN -->\n"
    run = make_run(tmp_path, body)
    code, messages = checker.check_run(run)
    assert code == 1
    assert "decision" in messages[0].lower()


def test_variation_with_pass_criterion_passes(tmp_path):
    checker = load_checker()
    run = make_run(tmp_path, VARIATION_BODY)
    code, messages = checker.check_run(run)
    assert code == 0
    assert "variation" in messages[0].lower()


def test_variation_missing_pass_criterion_fails(tmp_path):
    checker = load_checker()
    body = """\
# Baseline Strategy

## Decision

variation

## Variation Path

### Parent Model

Smith 2019

### Key Result to Reproduce

Fig. 3a

### Reproduce Pass Criterion

<!-- FILL IN -->
"""
    run = make_run(tmp_path, body)
    code, messages = checker.check_run(run)
    assert code == 1
    assert "pass criterion" in messages[0].lower()


def test_new_model_with_checkpoint_passes(tmp_path):
    checker = load_checker()
    run = make_run(tmp_path, NEW_MODEL_BODY)
    code, messages = checker.check_run(run)
    assert code == 0
    assert "new model" in messages[0].lower()


def test_new_model_missing_pass_criterion_fails(tmp_path):
    checker = load_checker()
    body = """\
# Baseline Strategy

## Decision

new model

## New Model Path

### Analytical Checkpoint 1

Mean-field theory.

**Expected result:**

m = tanh(...)

**Pass criterion:**

"""
    run = make_run(tmp_path, body)
    code, messages = checker.check_run(run)
    assert code == 1
    assert "pass criterion" in messages[0].lower()


def test_main_cli_pass(tmp_path):
    checker = load_checker()
    run = make_run(tmp_path, VARIATION_BODY)
    assert checker.main(["--run", str(run)]) == 0


def test_main_cli_fail(tmp_path):
    checker = load_checker()
    run = make_run(tmp_path, None)
    assert checker.main(["--run", str(run)]) == 1
