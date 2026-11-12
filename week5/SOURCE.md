# Source and verification record

## Upstream starter

- Repository: https://github.com/firdaussahran/p4-lab
- Retrieved revision: `88245a03baf7dac20e20969d838b1e4e1dfecc09`
- Course image: `ghcr.io/firdaussahran/p4-lab:1.0`
- The topology, original host tools, CLI helper, table entries, dev-container configuration, compilation workflow and report skeleton came from the official starter. Upstream Git metadata was not copied.

## Preserved practical and C1 history

The practical added tunnel parsing, emission and tunnel-first forwarding. Its 31 recorded checks passed; see RESULTS.md, LAB-ANSWERS.md and evidence/practical/.

`tunnel_v1.p4` matches `stages/step05-tunnel-forwarding.p4`. Original host tools remain in `stages/send_v1.py` and `stages/receive_v1.py`, and practical/C1 runners explicitly select those definitions.

C1 demonstrated unbounded circulation, with counts 18→192 on s1 and 17→192 on s2. The baseline and C1 are separate commits on `hop-limit`. Initial shell-line-ending and runtime-CLI parser errors were corrected before the successful runs. Their failed-run logs were removed from the current folder during cleanup and remain available in Git history.

## Current assignment

- `tunnel.p4`: appended 8-bit budget; drop incoming 0/1, otherwise decrement before lookup.
- `send.py`, `receive.py`: matching five-byte format, configurable sender budget and remaining-value display.
- `assignment/REPORT.md`: C1–C5 design, results, evaluation and AI-use declaration.
- `assignment/MIXED-PREDICTION.md`: prediction recorded before implementation/testing.
- Test runners: reproducible C1, practical and C4/C5 experiments in fresh workspaces, preserving existing evidence.
- `assignment/README.md`, `assignment/PR-DESCRIPTION.md`: assignment guide and remaining publication instructions.

## Verification

The official course image compiled both P4 versions. All 26 C4/C5 assertions passed: ten delivery/argument checks, ten loop checks and six mixed checks. Normal delivery left 6 hops; the upgraded loop stopped after eight visits, and the mixed loop after 15. Mixed captured bytes showed remaining hops 7, IPv4 protocol 13 and invalid checksum, matching the prediction.

Three independent reviews found no implementation defects, verified the evidence/report, and repeated the experiments. The fresh live review passed 59 checks (57 runner assertions plus independent C1 and packet-capture verification). See assignment/REVIEW.md. This is functional BMv2 validation, not an ASIC performance measurement.

## Cleanup and GitHub state

Week 05 is submitted as the unmerged PR "Tunnel hop limit" from `hop-limit` into `main`.

Cleanup removed disposable `build/` copies and ZIPs, failed-attempt logs, an empty evidence placeholder, duplicate template/checklist documents, and the unused image-publishing workflow. Successful source/evidence, original packet tools, stage programs, compilation/dev-container configuration, report and review summary remain intact. The tracked deletions are recoverable from Git history; new build/export artifacts can be regenerated.

The compile workflow is at the repository root so GitHub runs it; it compiles in `week5/`.
