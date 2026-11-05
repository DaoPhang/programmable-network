# Submission status and remaining steps

## Current GitHub state

The source, report and experiment evidence were committed by the user as **`e2e5040` — `Week05`** and pushed to `DaoPhang/programmable-network` on `main`. The coursework files are inside `week05/`.

C1–C5 are complete and tested. The separate course submission repository/PR, green GitHub compilation check, lecturer access and Spectrum submission remain outstanding. Pushing the combined coursework folder alone does not complete these requirements.

## Ready files

- [README.md](README.md): complete C1–C6 guide.
- [REPORT.md](REPORT.md): design, implementation, observations, evaluation and AI-use declaration.
- Required evidence: [loop-before.txt](evidence/loop-before.txt), [delivery.txt](evidence/delivery.txt), [loop-after.txt](evidence/loop-after.txt), [mixed.txt](evidence/mixed.txt).
- [REVIEW.md](REVIEW.md): independent reviews and fresh live rerun, with 59 checks passed and none failed.
- [PR-DESCRIPTION.md](PR-DESCRIPTION.md): exact required title **Tunnel hop limit** and prepared body.
- [prepare_submission.py](prepare_submission.py): create a standalone review export with root compilation/dev-container configuration and a SHA-256 manifest when needed.

Successful raw logs, assertion JSONs, test runners and the original `tunnel_v1.p4` remain available. Generated build/review copies, duplicate guides, failed-attempt logs and the unused image-publishing workflow were removed during cleanup. Earlier tracked files remain recoverable from Git history.

## Finish the course submission

1. Create your own repository from https://github.com/firdaussahran/p4-lab. Files such as `tunnel.p4`, `topo.py`, `.github/` and `.devcontainer/` must be at that repository's root, rather than nested inside `week05/`.
2. Establish the completed four-byte practical baseline on its `main`, including `tunnel_v1.p4`. Carry over the earlier baseline/C1 history where practical. Do not put the finished assignment directly onto the submission repository's `main`.
3. Create `hop-limit` from that baseline and commit/transfer the reviewed updated source, report and evidence. Keep the preserved baseline unchanged.
4. Push `hop-limit` and open a PR inside that repository, targeting its own `main`. Use title **Tunnel hop limit** and the body in PR-DESCRIPTION.md.
5. Confirm **Compile tunnel.p4** is green. Local compilation passed, but no GitHub Actions result is claimed here. If it fails, inspect the workflow output and fix the problem before submission.
6. Make the submission repository public or grant the lecturer collaborator access.
7. Submit the actual PR URL on your authenticated Spectrum course assignment page.
8. **Leave the PR unmerged.** Deadline: **Friday 13 November 2026, before the Week 6 class**.

No Codespace was created, so none needs deleting. The experiments used the official course Docker image locally, and temporary test containers were removed.

## Reproduce tests

From PowerShell at the coursework repository root:

```powershell
Set-Location .\week05
$week05Path = (Get-Location).Path
docker run --rm --privileged --mount "type=bind,source=$week05Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 python3 assignment/run_assignment.py
```

The runner refuses to overwrite existing delivery, loop-after and mixed transcripts/raw directories. Preserve existing evidence under separately named backups before repeating. Each scenario uses a fresh workspace and Mininet cleanup.

## Generate a standalone export

From `week05`:

```powershell
python -I assignment/prepare_submission.py
```

This generates a fresh folder/ZIP under ignored `build/`. Previous generated copies were removed to keep the workspace small. The export contains the required files at the correct repository root, but does not contain Git metadata or replace the required baseline/assignment branch history.
