# Submission preparation and remaining publication steps

## Completed locally

- C1 baseline preservation and loop-before evidence are already committed from the earlier session.
- C2 design, C3 implementation, C4 protected delivery/loop tests and C5 mixed-version analysis are complete in [REPORT.md](REPORT.md).
- All four required evidence files exist: [loop-before.txt](evidence/loop-before.txt), [delivery.txt](evidence/delivery.txt), [loop-after.txt](evidence/loop-after.txt), [mixed.txt](evidence/mixed.txt).
- The updated P4 program compiled in the official image. All 26 C4/C5 assertions passed.
- The report includes the AI-use declaration and distinguishes actual tests from proposals and code-based conclusions.
- [PR-DESCRIPTION.md](PR-DESCRIPTION.md) supplies the required title **Tunnel hop limit** and prepared PR body.
- [REVIEW.md](REVIEW.md) summarises the three independent reviews and fresh live rerun: 59 checks passed, none failed.
- `prepare_submission.py` creates a standalone review folder and ZIP under `../build/`, with a SHA-256 manifest. Root `.github/workflows/compile.yml` and `.devcontainer/` are included for a separate repository.

## Why C6 publication is pending

The latest instruction is **do not commit anything first**. GitHub pushes and PRs show committed snapshots; they cannot include these uncommitted implementation/report changes. No new commit, staging, push, repository creation or PR was performed during C2–C5 work. Existing branch `hop-limit` still points at the earlier C1 commit `8567723`.

The current `origin` is `DaoPhang/programmable-network`, the combined coursework repository. The course expects a PR inside your own P4 template repository, where the P4 files and workflow live at the root. That separate repository has not been created. A green local compilation is not a green GitHub Actions check, and no PR URL or Spectrum submission exists yet.

## Final steps for your own GitHub publication

1. Create your own repository from https://github.com/firdaussahran/p4-lab, keeping it private until deciding lecturer access if desired.
2. Establish the completed four-byte practical baseline on its `main`, including preserved `tunnel_v1.p4`. Carry over the meaningful earlier baseline/C1 history where practical so the assignment PR shows the hop-limit change against the finished lab. Do not place the completed assignment directly onto its `main`.
3. Create `hop-limit` from that baseline and commit the reviewed updated source, report and evidence. Keep the original baseline intact.
4. Push `hop-limit` and open the prepared PR **within your own repository**, targeting its `main`. Use the exact required title **Tunnel hop limit** and the body in PR-DESCRIPTION.md.
5. Confirm **Compile tunnel.p4** is green. If it fails, inspect the workflow output and correct the problem before submission.
6. Make the repository public or grant the lecturer collaborator access. The lecturer's GitHub login has not been supplied here.
7. Submit the real PR URL through your authenticated Spectrum course assignment page. An authenticated Spectrum session/submission destination is not available to this CLI session.
8. **Leave the PR unmerged**. Deadline: **Friday 13 November 2026, before the Week 6 class**.

No Codespace was created, so there is no Codespace to delete. Temporary local test containers were removed.

## Reproduce tests locally

In PowerShell, starting at the coursework repository root:

```powershell
Set-Location .\week05
$week05Path = (Get-Location).Path
docker run --rm --privileged --mount "type=bind,source=$week05Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 python3 assignment/run_assignment.py
```

The test runner refuses to overwrite `delivery.txt`, `loop-after.txt`, `mixed.txt` or their raw directories. Preserve existing results under separately named backups before a repeat. It uses a fresh topology workspace for each scenario and cleans up Mininet after each.

## Produce a fresh review export

From `week05` on Windows:

```powershell
python -I assignment/prepare_submission.py
```

The generated folder is a local review artifact without Git metadata, and is not a replacement for the baseline/assignment branch history. The ZIP includes the report, sources, preserved baseline, evidence and a checksum manifest. Review the exported README for standalone operation.
