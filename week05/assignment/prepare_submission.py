#!/usr/bin/env python3
"""Export a reviewable standalone P4 repository without committing/publishing."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix="submission-review-6042-", dir=build))

    def ignored(directory, names):
        skip = {".git", "__pycache__", "build", "logs"} if Path(directory) == ROOT else {".git", "__pycache__"}
        # The compilation workflow is needed; publishing another lab image is not.
        if Path(directory) == ROOT / ".github/workflows":
            skip.add("image.yml")
        return set(names) & skip

    shutil.copytree(ROOT, target, dirs_exist_ok=True, ignore=ignored)
    (target / "README.md").write_text(
        "# Week 5 — Tunnel hop-limit assignment\n\n"
        "Student suffix: **6042**.\n\n"
        "See [assignment/REPORT.md](assignment/REPORT.md) for the design and analysis, "
        "and [assignment/evidence/](assignment/evidence/) for the actual experiment outputs.\n\n"
        "Start the supplied course environment with `python3 topo.py --id 6042`. "
        "Tunnel sends default to 8 visits; configure with `--hops N`.\n\n"
        "Run C4/C5 with `python3 assignment/run_assignment.py` in a dedicated privileged "
        "course container after preserving the existing evidence directories. "
        "The runner refuses to overwrite evidence.\n\n"
        "This is a local review export. It has no Git metadata and has not been published. "
        "The root `.github/workflows/compile.yml` and `.devcontainer/` are ready for a "
        "separate P4 repository. Leave the eventual assignment PR unmerged.\n",
        encoding="utf-8",
    )
    files = {str(p.relative_to(target)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(target.rglob("*")) if p.is_file()}
    (target / "SUBMISSION-MANIFEST.json").write_text(json.dumps(files, indent=2) + "\n")
    archive = shutil.make_archive(str(target), "zip", root_dir=target)
    print(f"Review folder: {target}")
    print(f"Review archive: {archive}")
    print(f"Exported files: {len(files)}")
    print("No Git commits, pushes, repository creation or submissions performed.")


if __name__ == "__main__":
    main()
