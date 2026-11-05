# Week 05 assignment — tunnel hop limit

Student suffix: **6042**  
Working branch: **`hop-limit`**

[Course instructions](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab) · [Full report](REPORT.md) · [Submission steps](SUBMISSION.md)

## Overview and status

This assignment adds a hop limit to the practical's P4 tunnel program, demonstrates that it stops a forwarding loop, and evaluates deployment with an older switch program. The topology is h1 → s1 → s2, with h2 and h3 connected to s2. Host addresses are `10.42.0.1`, `10.42.0.2` and `10.42.0.3`.

**C1–C5 are complete locally.** The updated program compiled in the official course image, and all **26 C4/C5 assertions passed**. C6 materials are prepared, but publication and submission remain pending. The latest implementation, report and evidence changes are uncommitted and unstaged as requested.

## C1 — Demonstrate the original loop

The completed practical is preserved in [tunnel_v1.p4](../tunnel_v1.p4), which matches the saved Step 5 program. Baseline commit `b5fc667` and C1 commit `8567723` preserve the earlier work.

The experiment identified s2's tunnel destination-3 entry as handle 2 and changed its output from port 3 to port 1. Since s1 already sends destination 3 towards s2, this created s1 → s2 → s1. One packet was sent from h1 with destination identifier 3, then switch packet-reception counts were measured twice.

| Switch | First count | After five-second wait | Increase |
|---|---:|---:|---:|
| s1 | 18 | 192 | 174 |
| s2 | 17 | 192 | 175 |

These counts represent repeated switch-processing visits by one injected packet. The topology was stopped after measurement. [loop-before.txt](evidence/loop-before.txt) records the commands and outputs, with [structured counts](evidence/loop-before-raw/counts.json) and raw logs alongside it.

REPORT.md also explains why the supplied ordinary IPv4 TTL decrement is insufficient: the program has no expiration check, so an unsigned 8-bit TTL can wrap from 0 to 255. That conclusion is based on code inspection; a separate ordinary-IPv4 loop was not run.

## C2 — Design the limit

The design was recorded before implementation. The new tunnel format is:

```text
proto_id: 16 bits | dst_id: 16 bits | hops: 8 bits
```

The header grows from four to five bytes. The sender defaults to **8** and accepts `--hops` values **0–255**. On a valid tunnel packet, ingress drops incoming 0 or 1; otherwise it subtracts one before applying the tunnel table. Exhausted values are never subtracted, preventing wraparound.

A positive initial value N permits at most N visits to upgraded switches on an all-upgraded loop: at most N−1 forwards, followed by discard on visit N. Initial 0 drops on the first visit. Normal traversal of two switches with initial 8 arrives with **6 remaining**. Successful traversal of K switches requires N > K.

## C3 — Implement the format and processing

| File | Change |
|---|---|
| [tunnel.p4](../tunnel.p4) | Appended 8-bit field; ingress exhaustion check and decrement |
| [send.py](../send.py) | Matching Scapy field, configurable initial budget and argument validation |
| [receive.py](../receive.py) | Matching field and display of the remaining budget |
| [tunnel_v1.p4](../tunnel_v1.p4) | Unchanged original implementation for baseline/mixed testing |

The existing parser extraction and deparser emission include the new field automatically. Table keys and entries are unchanged. Ordinary IPv4 retains the practical's behaviour.

## C4 — Verify delivery and loop termination

[delivery.txt](evidence/delivery.txt) records h2 and h3 receiving packets with **hops=6**, ordinary UDP delivery, and **2/2 ping replies at TTL 62**. Boundary tests confirm that 0, 1 and 2 do not reach the two-switch destination, 3 arrives with 1, and 255 arrives with 253. Invalid CLI limits and `--hops` without `--tunnel` are rejected before transmission.

[loop-after.txt](evidence/loop-after.txt) repeats the original destination-3 loop. Initial 8 produced **s1=4, s2=4**, with no increase after another five seconds: eight visits, seven forwards, then discard. Additional budgets 0, 1, 2 and 3 matched the specified visit counts and remained stable.

## C5 — Evaluate mixed deployment

The [original prediction](MIXED-PREDICTION.md) was written before implementation/testing. The experiment ran updated s1 with old s2 using `--s2-program tunnel_v1.p4`.

A frame reached h2 with **7 remaining**, but old s2 started its IPv4 parser one byte early. Its checksum update changed the real IPv4 protocol from **17 (UDP) to 13** and left an invalid checksum. Consequently, the normal UDP receiver did not report the message. The raw capture and decoded bytes are saved with [mixed.txt](evidence/mixed.txt).

The mixed loop stopped after **8 s1 visits and 7 s2 visits**, or 15 total, matching the prediction. Only s1 decremented the limit. This does not protect cycles containing only old switches.

REPORT.md compares two rollout approaches, the required Week 3 `check_paths()` behaviour and its limitations, and hardware/header costs. The rollout approaches are proposals, not implemented features. BMv2 functional results do not establish ASIC throughput or resource usage.

## C6 — Prepare and submit

The report and AI-use declaration are complete, and all four required evidence files exist. [PR-DESCRIPTION.md](PR-DESCRIPTION.md) contains the proposed PR title/body. [prepare_submission.py](prepare_submission.py) exports a standalone review folder/ZIP, including root compilation and dev-container configuration.

The remaining steps are to review and authorise commits, establish the separate P4 template repository and baseline, push its assignment branch, open a PR into its own `main`, confirm **Compile tunnel.p4** is green, provide lecturer access, and submit the real PR URL on Spectrum. **Leave the PR unmerged.** Deadline: **13 November 2026, before the Week 6 class**.

No new commits, push, separate repository, PR, GitHub Actions result or Spectrum submission is claimed. See [SUBMISSION.md](SUBMISSION.md) for details.

## Evidence and reproduction

| Required transcript | Supporting files |
|---|---|
| [loop-before.txt](evidence/loop-before.txt) | `evidence/loop-before-raw/`: counts, switch/host logs and cleanup |
| [delivery.txt](evidence/delivery.txt) | [Delivery assertions](evidence/delivery-raw/checks.json) and raw logs |
| [loop-after.txt](evidence/loop-after.txt) | [Loop assertions](evidence/loop-after-raw/checks.json) and raw logs |
| [mixed.txt](evidence/mixed.txt) | [Mixed assertions/decoded bytes](evidence/mixed-raw/checks.json), capture and raw logs |

From PowerShell at the coursework repository root, run C4/C5 in the official course container:

```powershell
Set-Location .\week05
$week05Path = (Get-Location).Path
docker run --rm --privileged --mount "type=bind,source=$week05Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 python3 assignment/run_assignment.py
```

For C1 replay, use `python3 assignment/run_loop_before.py` instead. It selects the preserved baseline and original host tools in `../stages/`, independent of the current assignment format.

Both runners refuse to overwrite existing evidence. Preserve prior transcripts and raw directories under separate backup names before repeating. Each run uses fresh workspaces and a dedicated container, and runs Mininet cleanup. Transcript `mininet>` lines show equivalent commands executed automatically through the topology's CLI callback.

Initial failed attempts are retained separately: the practical exposed Windows shell line endings, and C1's first runner expected a different displayed field name in the runtime CLI. Both were corrected before the successful runs. Temporary experiment containers were removed after execution.
