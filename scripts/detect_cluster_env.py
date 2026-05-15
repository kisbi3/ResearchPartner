#!/usr/bin/env python3
"""Detect the HPC cluster scheduler and record environment info.

Writes a cluster_env.md summary to the given run docs directory (or prints
to stdout when no --run is supplied).  Safe to run on a local workstation:
it reports 'none' when no scheduler is found.

Usage:
    python scripts/detect_cluster_env.py
    python scripts/detect_cluster_env.py --run ResearchPartner-runs/2026-05-16-myrun
    python scripts/detect_cluster_env.py --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    """Run a command quietly; return (returncode, stdout+stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""


def _which(name: str) -> bool:
    return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# Scheduler probes
# ---------------------------------------------------------------------------

def _probe_slurm() -> dict | None:
    if not _which("sbatch"):
        return None
    rc, ver = _run(["sbatch", "--version"])
    if rc != 0 and not ver:
        return None
    info: dict = {"scheduler": "slurm", "version": ver}

    # Partitions + resources
    rc2, sinfo = _run(["sinfo", "--noheader", "--format=%P %C %G %l %m"])
    if rc2 == 0 and sinfo:
        partitions = []
        for line in sinfo.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                partitions.append({
                    "name": parts[0].rstrip("*"),
                    "cpus_A/I/O/T": parts[1],
                    "gres": parts[2],
                    "timelimit": parts[3],
                    "memory_MB": parts[4],
                })
        info["partitions"] = partitions

    # Default account / QOS
    rc3, acct = _run(["sacctmgr", "show", "user", os.environ.get("USER", ""), "format=Account,DefaultAccount", "--noheader", "-P"])
    if rc3 == 0 and acct:
        info["default_account"] = acct.strip()

    return info


def _probe_pbs() -> dict | None:
    """Detect PBS/Torque."""
    if not _which("qsub"):
        return None
    rc, ver = _run(["qsub", "--version"])
    # PBS version strings vary; SGE also has qsub — distinguish by pbsnodes
    if not _which("pbsnodes") and not _which("qnodes"):
        return None  # Likely SGE/OGE, not PBS
    info: dict = {"scheduler": "pbs", "version": ver}

    rc2, queues = _run(["qstat", "-Q"])
    if rc2 == 0 and queues:
        info["queues_raw"] = queues[:2000]

    return info


def _probe_sge() -> dict | None:
    """Detect Sun/Univa/Open Grid Engine."""
    if not _which("qsub") or not _which("qstat"):
        return None
    rc, out = _run(["qstat", "-g", "c"])
    if rc != 0:
        return None
    info: dict = {"scheduler": "sge"}
    rc2, ver = _run(["qsub", "-help"])
    info["version_hint"] = ver.splitlines()[0] if ver else "unknown"
    if out:
        info["queues_raw"] = out[:2000]
    return info


def _probe_lsf() -> dict | None:
    if not _which("bsub"):
        return None
    rc, ver = _run(["bsub", "-V"])
    info: dict = {"scheduler": "lsf", "version": ver}

    rc2, queues = _run(["bqueues"])
    if rc2 == 0 and queues:
        info["queues_raw"] = queues[:2000]

    return info


def _probe_none() -> dict:
    return {"scheduler": "none", "note": "No recognized HPC scheduler found. Use run_in_background + Monitor for local long-running jobs."}


# ---------------------------------------------------------------------------
# Environment extras
# ---------------------------------------------------------------------------

def _module_system() -> str:
    if _which("module"):
        return "environment-modules"
    if _which("lmod"):
        return "lmod"
    # 'module' is often a shell function, not a binary — check common paths
    for path in ["/usr/share/Modules/init/bash", "/etc/profile.d/modules.sh"]:
        if Path(path).exists():
            return "environment-modules (shell function)"
    return "none"


def _gpu_info() -> str:
    rc, out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if rc == 0 and out:
        return out[:500]
    return "none"


def _env_hints() -> dict:
    keys = [
        "SLURM_SUBMIT_HOST", "SLURM_CLUSTER_NAME",
        "PBS_O_HOST", "PBS_SERVER",
        "SGE_ROOT", "SGE_CLUSTER_NAME",
        "LSB_JOBID", "LSF_SERVERDIR",
        "HOSTNAME", "USER",
    ]
    return {k: os.environ[k] for k in keys if k in os.environ}


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------

def detect() -> dict:
    env = (
        _probe_slurm()
        or _probe_pbs()
        or _probe_sge()
        or _probe_lsf()
        or _probe_none()
    )
    env["module_system"] = _module_system()
    env["gpu_info"] = _gpu_info()
    env["env_hints"] = _env_hints()
    return env


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def to_markdown(info: dict) -> str:
    scheduler = info.get("scheduler", "unknown")
    lines = [
        "# Cluster Environment",
        "",
        f"**Scheduler**: `{scheduler}`",
    ]

    if scheduler == "none":
        lines += ["", info.get("note", ""), ""]
    else:
        if "version" in info:
            lines.append(f"**Version**: {info['version']}")
        if "default_account" in info:
            lines.append(f"**Default account/QOS**: {info['default_account']}")
        lines.append("")

    # Partitions / queues
    if "partitions" in info:
        lines += ["## SLURM Partitions", ""]
        lines.append("| Partition | CPUs (A/I/O/T) | GRES | Timelimit | Mem (MB) |")
        lines.append("|---|---|---|---|---|")
        for p in info["partitions"]:
            lines.append(
                f"| {p['name']} | {p['cpus_A/I/O/T']} | {p['gres']} | {p['timelimit']} | {p['memory_MB']} |"
            )
        lines.append("")
    elif "queues_raw" in info:
        lines += ["## Queues / Raw Output", "", "```", info["queues_raw"], "```", ""]

    # GPU
    gpu = info.get("gpu_info", "none")
    lines.append(f"**GPU (nvidia-smi)**: {'`' + gpu + '`' if gpu != 'none' else 'none'}")
    lines.append("")

    # Module system
    lines.append(f"**Module system**: {info.get('module_system', 'unknown')}")
    lines.append("")

    # Env hints
    hints = info.get("env_hints", {})
    if hints:
        lines += ["## Environment Variables", ""]
        for k, v in hints.items():
            lines.append(f"- `{k}` = `{v}`")
        lines.append("")

    lines += [
        "## Submission Guidelines",
        "",
        _submission_guidelines(info),
        "",
    ]

    return "\n".join(lines)


def _submission_guidelines(info: dict) -> str:
    s = info.get("scheduler", "none")
    if s == "slurm":
        return (
            "- Submit with `sbatch job.sh`; monitor with `squeue -u $USER`.\n"
            "- Parameter sweeps: use `#SBATCH --array=0-N` job arrays.\n"
            "- GPU jobs: add `#SBATCH --gres=gpu:1` and load CUDA modules.\n"
            "- Check time limits per partition before setting `--time`.\n"
            "- Use `ScheduleWakeup` to pause the Claude session and resume after job completion."
        )
    elif s == "pbs":
        return (
            "- Submit with `qsub job.sh`; monitor with `qstat -u $USER`.\n"
            "- Parameter sweeps: use `#PBS -J 0-N` job arrays.\n"
            "- GPU jobs: add `#PBS -l ngpus=1`.\n"
            "- Use `ScheduleWakeup` to pause the Claude session and resume after job completion."
        )
    elif s == "sge":
        return (
            "- Submit with `qsub job.sh`; monitor with `qstat -u $USER`.\n"
            "- Parameter sweeps: use `#$ -t 1-N` task arrays.\n"
            "- GPU jobs: add `-l gpu=1` resource request.\n"
            "- Use `ScheduleWakeup` to pause the Claude session and resume after job completion."
        )
    elif s == "lsf":
        return (
            "- Submit with `bsub < job.sh`; monitor with `bjobs -u $USER`.\n"
            "- Parameter sweeps: use `#BSUB -J name[0-N]` job arrays.\n"
            "- GPU jobs: add `#BSUB -gpu 'num=1'`.\n"
            "- Use `ScheduleWakeup` to pause the Claude session and resume after job completion."
        )
    else:
        return (
            "- No cluster scheduler detected. Use `run_in_background: true` in Bash + Monitor.\n"
            "- For jobs >5 min use `ScheduleWakeup` to pause and resume."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, help="Run directory; writes docs/cluster_env.md there.")
    p.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    info = detect()

    if args.json:
        print(json.dumps(info, indent=2))
        return 0

    md = to_markdown(info)

    if args.run:
        out_path = Path(args.run) / "docs" / "cluster_env.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"Written: {out_path}")
    else:
        print(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
