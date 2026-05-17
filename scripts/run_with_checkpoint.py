#!/usr/bin/env python3
"""Checkpoint manager for long-running computations.

Provides CheckpointManager: a lightweight save/load/clear utility that any
src/ script can import to gain resume-from-interruption capability.

Usage in a src/ script
----------------------

    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from run_with_checkpoint import CheckpointManager
    from _layout import cache_dir

    RUN_DIR = Path("path/to/run")
    ckpt = CheckpointManager(cache_dir(RUN_DIR), Path(__file__).stem)

    state = ckpt.load()             # returns dict or None
    start_step = state["step"] if state else 0
    results    = state["results"] if state else []

    for step in range(start_step, N_STEPS):
        results.append(compute(step))
        ckpt.maybe_save({"step": step + 1, "results": results})

    ckpt.clear()                    # remove checkpoint on clean exit
    np.save(output_path, results)
    print(f"output = {output_path}")

Checkpoint file location
------------------------
``cache_dir(run) / f"checkpoint_{stem}.pkl"``

Use ``_layout.cache_dir()`` for the path so the location stays in sync
with the rest of the harness.

Atomic writes
-------------
Saves go to a ``.tmp`` sibling first, then ``Path.replace()`` so a kill
mid-save never corrupts the last good checkpoint.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

_DEFAULT_INTERVAL = 50


class CheckpointManager:
    """Atomic periodic save/load/clear for a single in-progress computation.

    Parameters
    ----------
    cache_dir:
        Directory where the checkpoint file is stored.  Use
        ``scripts._layout.cache_dir(run_dir)`` to keep the path in sync
        with the harness layout.
    stem:
        Script stem (typically ``Path(__file__).stem``).  The checkpoint
        file is named ``checkpoint_{stem}.pkl``.
    interval:
        Number of ``maybe_save()`` calls between writes.  Default 50.
        Set to 1 to save every call.
    """

    def __init__(self, cache_dir: Path, stem: str, interval: int = _DEFAULT_INTERVAL) -> None:
        self.path = cache_dir / f"checkpoint_{stem}.pkl"
        self.interval = interval
        self._count = 0  # calls to maybe_save since last checkpoint write

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> dict | None:
        """Return the saved state dict, or None if no checkpoint exists.

        The returned dict may contain any keys the caller saved, plus a
        harness-internal ``_ckpt_step`` key recording the loop count at
        the time of the last save.
        """
        if not self.path.exists():
            return None
        try:
            state = pickle.loads(self.path.read_bytes())
        except Exception as exc:
            print(
                f"[checkpoint] WARNING: could not load {self.path}: {exc}",
                file=sys.stderr,
            )
            return None
        step = state.get("_ckpt_step", "?")
        print(f"[checkpoint] Resuming from {self.path} (step {step})")
        self._count = int(step) if str(step).isdigit() else 0
        return state

    def maybe_save(self, state: dict) -> None:
        """Save state every ``self.interval`` calls.

        Call this at the end of each loop iteration.  The save is skipped
        unless ``self._count`` is a multiple of ``self.interval``.
        """
        self._count += 1
        if self._count % self.interval == 0:
            self._write(state)

    def save(self, state: dict) -> None:
        """Unconditionally save state now, bypassing the interval counter."""
        self._count += 1
        self._write(state)

    def clear(self) -> None:
        """Remove the checkpoint file after a clean, completed run."""
        if self.path.exists():
            self.path.unlink()
            print(f"[checkpoint] Cleared {self.path}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _write(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**state, "_ckpt_step": self._count}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_bytes(pickle.dumps(payload))
        tmp.replace(self.path)
        print(f"[checkpoint] Saved step {self._count} → {self.path}")


if __name__ == "__main__":
    print(
        "run_with_checkpoint.py is a library module, not a standalone script.\n"
        "Import CheckpointManager from your src/ scripts."
    )
