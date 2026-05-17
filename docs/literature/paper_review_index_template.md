# Paper Review Index Template

Use this run-local index to keep the literature set navigable. Add every requested, received, reviewed, deferred, or rejected paper so the literature gate remains auditable.

| Paper ID | Title | Authors / Year | PDF | Review Note | Status | Role in Project | Reproduction Candidate | Novelty Impact |
|---|---|---|---|---|---|---|---|---|
| P1 |  |  | [PDF](pdfs/example.pdf)<br>`literature/pdfs/example.pdf` | [Review](reviews/P1-title.md)<br>`literature/reviews/P1-title.md` | requested / received / reading / reviewed / deferred | foundation / closest prior work / benchmark / method / review | yes / no / maybe | supports / weakens / contradicts / unverified |

## Review Status Legend

- `requested`: Lead Agent asked the researcher for the PDF.
- `received`: PDF is present but not reviewed.
- `reading`: review is in progress.
- `reviewed`: detailed section-by-section paper review exists.
- `deferred`: paper is relevant but not needed for the current iteration.
- `rejected`: paper was inspected and judged out of scope, with a reason.

## Reuse Notes

- Link every review note back to the PDF and the replanning memo.
- Use clickable relative Markdown links plus run-relative code paths so future agents can navigate quickly and still recover exact run-local paths.
- Keep title, authors, year, and role stable so future runs can reuse this index.
- Do not mark novelty as supported from metadata alone.
