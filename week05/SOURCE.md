# Source and verification record

## Upstream starter

- Repository: https://github.com/firdaussahran/p4-lab
- Retrieved revision: `88245a03baf7dac20e20969d838b1e4e1dfecc09`
- Course image: `ghcr.io/firdaussahran/p4-lab:1.0`
- The topology, original host tools, CLI helper, table files, dev-container configuration, workflows and report skeleton came from that starter. TEMPLATE-README.md preserves its README. Upstream Git metadata was not copied.

## Practical and C1 history

The practical added tunnel parsing, emission and tunnel-first ingress forwarding. Its 31 recorded checks passed in the official image; see RESULTS.md and evidence/practical/. LAB-ANSWERS.md answers its four questions. Windows shell line endings were corrected and the first failed attempt was retained.

`tunnel_v1.p4` and `stages/step05-tunnel-forwarding.p4` preserve the same completed practical. Original host tools are retained in `stages/send_v1.py` and `stages/receive_v1.py` from the earlier committed files. Practical/C1 replay runners explicitly select those definitions.

C1 demonstrated unbounded circulation, with counts 18→192 on s1 and 17→192 on s2. The baseline and C1 history exist as `b5fc667` and `8567723`. An initial runtime-CLI field-name parser mismatch was corrected and its failed attempt preserved.

## Current assignment implementation

- `tunnel.p4` adds an 8-bit appended hop budget and drops incoming 0/1 before decrement/table lookup.
- `send.py` and `receive.py` agree on the five-byte header; the sender configures/validates the initial budget and the receiver prints the remaining value.
- `assignment/REPORT.md` records C2 design before implementation and finishes C1–C5 analysis and the AI-use declaration.
- `assignment/MIXED-PREDICTION.md` preserves the prediction written before implementation and mixed traffic.
- `assignment/run_assignment.py` records actual C4/C5 results in fresh workspaces without replacing evidence.
- `assignment/PR-DESCRIPTION.md`, `SUBMISSION.md` and `prepare_submission.py` prepare the publication materials and standalone review export.

## Verification actually completed

- Updated and original P4 compile in the official course image.
- **26 C4/C5 assertions passed:** 10 delivery/argument checks, 10 protected-loop checks, 6 mixed-version checks.
- h2 and h3 received default-budget traffic with 6 remaining; ordinary IPv4 UDP/ping succeeded.
- The upgraded default loop stopped after eight visits; boundary limits 0/1/2/3 matched the defined semantics and did not wrap.
- Mixed s1 new/s2 old stopped after 15 visits. Captured bytes showed preserved hops 7, corrupted IPv4 protocol 13 and invalid checksum, matching the prior prediction.
- All four required transcripts, structured results and raw logs are under assignment/evidence/.
- Python syntax and local documentation links are checked separately. Raw experiment outputs retain their original whitespace.

These are functional BMv2 results; no ASIC timing/resource or throughput measurements are claimed. The Week 3 comparison refers to the required completed `check_paths()` described by the course, not a function present in this local week3 code.

## Publication state

C2–C5 changes remain uncommitted and unstaged at the user's request. No new commits, pushes, repository creation, PR, GitHub Actions run or Spectrum submission was made during this work. Existing C1 commits remain intact on `hop-limit`.

The current remote is the combined coursework repository. Nested week05 configuration is not automatically active at that repository's root. The standalone local export supplies root compilation/dev-container configuration for a separate P4 repository and excludes the optional image-publishing workflow. See assignment/SUBMISSION.md for the remaining C6 steps.
