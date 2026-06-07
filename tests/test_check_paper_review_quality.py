import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / ".harness" / "scripts" / "check_paper_review_quality.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_paper_review_quality", CHECK_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_paper_review_quality"] = module
    spec.loader.exec_module(module)
    return module


def test_quality_check_passes_review_with_required_evidence_links(tmp_path):
    checker = load_checker()
    review_path = tmp_path / "review.md"
    review_path.write_text(
        """# Example Paper

## Review Metadata

- PDF path: [PDF](../pdfs/example.pdf)
- Run-relative PDF path: `literature/pdfs/example.pdf`
- Paper Review Index: [literature/index.md](../index.md)
- Replanning Memo: [docs/replanning_memo.md](../../docs/replanning_memo.md)

## Context Summary

<!-- context-summary:start -->
- One-line claim: Example benchmark study.
- Method: standard benchmark protocol.
- Key result: reproducible trend.
- Novelty status: unverified.
- Reproduction target: Figure 1.
- Limitations: 확인 필요.
- Why we care: comparison baseline.
- Citation key: example2026.
<!-- context-summary:end -->

## Source Text Extraction

- Extracted text path: [Extracted text](../extracted_text/P1-example.txt)
- Run-relative extracted text path: `literature/extracted_text/P1-example.txt`
- Extraction caveat: PDF text extraction is a reading aid, not evidence by itself. Verify claims against the PDF.

## Machine-Assisted Draft From Extracted Text

> 확인 필요: provisional reading aid. It does not establish novelty or validate claims.

## 0. Executive Summary

This paper asks a clear benchmark question.

## 1. Research Context and Motivation

The core problem is reproducibility.

## 2. Key Concepts and Definitions

| Concept | Definition |
|---|---|
| Benchmark | A comparison target |

## 3. Methodology

The model, parameters, units, and assumptions are recorded.

## Figure/Table-by-Figure/Table Review

| Figure/Table | What It Shows |
|---|---|
| Fig. 1 | A benchmark |

## Results Logic

The result sequence is stated.

## Discussion and Interpretation

Author claims and reviewer interpretation are separated.

## Reproduction Extraction

- Candidate reproduction target: Figure 1
- Pass/fail criterion: reproduce qualitative trend only after quantitative check

## Novelty and Claim Impact

| Our Planned Claim | Paper Evidence | Impact | Status | Needed Action |
|---|---|---|---|---|
| New benchmark | direct PDF | weakens | unverified | verify |

## Final Takeaway

Use cautiously.

## Quality Checklist

- [x] The review is detailed enough to understand the paper's flow without reopening the PDF.
- [x] Important concepts are defined at first use.
- [x] Method details include assumptions, parameters, units, and reproduction-critical settings.
- [x] Each important figure/table is reviewed separately.
- [x] Author claims and reviewer interpretation are separated.
- [x] Novelty impact is based on direct PDF evidence or explicitly marked unverified.
- [x] Reproduction target and pass/fail criterion are explicit.
""",
        encoding="utf-8",
    )

    result = checker.check_review_quality(review_path)

    assert result.status == "pass"
    assert result.missing == []
    assert result.warnings == []


def test_quality_check_flags_missing_links_and_unchecked_items(tmp_path):
    checker = load_checker()
    review_path = tmp_path / "thin-review.md"
    review_path.write_text(
        """# Thin Review

## Review Metadata

- PDF path:

## 0. Executive Summary

Short.

## Quality Checklist

- [ ] The review is detailed enough to understand the paper's flow without reopening the PDF.
""",
        encoding="utf-8",
    )

    result = checker.check_review_quality(review_path)

    assert result.status == "fail"
    assert "Source Text Extraction" in result.missing
    assert "Reproduction Extraction" in result.missing
    assert "Novelty and Claim Impact" in result.missing
    assert "Paper Review Index link" in result.missing
    assert "unchecked checklist item" in result.warnings

