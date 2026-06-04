#!/usr/bin/env python3
"""
Install researcher-facing skills as slash commands for Claude Code,
Codex CLI, and Antigravity CLI.

Re-run whenever a SKILL.md is updated.

Project-local install (default):
  .claude/commands/<name>.md           (Claude Code)
  .agents/workflows/<name>.md          (Antigravity CLI XML Workflow)
  .agents/skills/<name>/SKILL.md       (Antigravity CLI UI Skill)
  .codex/skills/<name>/SKILL.md        (Codex CLI — directory junction)

Global install (--global):
  ~/.claude/commands/<name>.md
  ~/.gemini/antigravity/global_workflows/<name>.md
  ~/.gemini/antigravity-cli/skills/<name>/SKILL.md
  ~/.codex/skills/<name>/SKILL.md
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILLS = [
    "task-intake",
    "meeting",
    "sync-workflow",
    "existing-research-onboarding",
    "harness-evaluation",
    "anomaly-debugging",
    "dimensional-analysis",
]

LOCAL_TARGETS = {
    "claude":              lambda root: root / ".claude" / "commands",
    "antigravity_wf":      lambda root: root / ".agents" / "workflows",
    "antigravity_skill":   lambda root: root / ".agents" / "skills",
    "codex":               lambda root: root / ".codex" / "skills",
}

GLOBAL_TARGETS = {
    "claude":              lambda _: Path.home() / ".claude" / "commands",
    "antigravity_wf":      lambda _: Path.home() / ".gemini" / "antigravity" / "global_workflows",
    "antigravity_skill":   lambda _: Path.home() / ".gemini" / "antigravity-cli" / "skills",
    "codex":               lambda _: Path.home() / ".codex" / "skills",
}


def find_harness_root() -> Path:
    p = Path(__file__).resolve().parent.parent
    if (p / "skills").is_dir():
        return p
    raise RuntimeError(f"skills/ directory not found under {p}")


def _remove_junction_or_symlink(path: Path) -> None:
    if sys.platform == "win32":
        subprocess.run(["cmd", "/c", "rmdir", str(path)], check=True, capture_output=True)
    else:
        path.unlink()


def make_junction(src: Path, dst: Path) -> None:
    """Create a directory junction (Windows) or symlink (Unix)."""
    if dst.exists() or dst.is_symlink():
        _remove_junction_or_symlink(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dst), str(src)],
            check=True, capture_output=True,
        )
    else:
        os.symlink(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def install(root: Path, targets: dict) -> None:
    skills_dir = root / "skills"
    ok, skipped = [], []

    for name in SKILLS:
        skill_dir = skills_dir / name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            print(f"  SKIP  {name}  (SKILL.md not found)")
            skipped.append(name)
            continue

        # Claude Code command
        copy_file(skill_md, targets["claude"](root) / f"{name}.md")
        
        # Antigravity XML Workflow
        copy_file(skill_md, targets["antigravity_wf"](root) / f"{name}.md")

        # Antigravity UI Skill
        try:
            make_junction(skill_dir, targets["antigravity_skill"](root) / name)
        except Exception as e:
            copy_file(skill_md, targets["antigravity_skill"](root) / name / "SKILL.md")
            print(f"  WARN  {name}  antigravity skill junction failed ({e}), used copy instead")

        # Codex UI Skill
        try:
            make_junction(skill_dir, targets["codex"](root) / name)
        except Exception as e:
            copy_file(skill_md, targets["codex"](root) / name / "SKILL.md")
            print(f"  WARN  {name}  codex junction failed ({e}), used copy instead")

        print(f"  OK    {name}")
        ok.append(name)

    print(f"\n{len(ok)} skill(s) installed, {len(skipped)} skipped.")
    print(f"  Claude Code      : {targets['claude'](root)}")
    print(f"  Antigravity WF   : {targets['antigravity_wf'](root)}")
    print(f"  Antigravity Skill: {targets['antigravity_skill'](root)}")
    print(f"  Codex CLI        : {targets['codex'](root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--global", dest="global_install", action="store_true",
                        help="Install to user home directories (available in all projects)")
    args = parser.parse_args()

    root = find_harness_root()
    targets = GLOBAL_TARGETS if args.global_install else LOCAL_TARGETS
    scope = "global" if args.global_install else "project-local"
    print(f"Installing {len(SKILLS)} skills ({scope}) ...\n")
    install(root, targets)


if __name__ == "__main__":
    main()
