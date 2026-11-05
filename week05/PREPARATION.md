# Week 5 — P4 programmable data plane and tunnel hop limit

Status: the practical experiments have now passed in the official course image using local Docker; see RESULTS.md and evidence/practical/. A separate template repository/Codespace has not been created, and the assessed assignment has not been completed. The unchecked boxes below remain a reusable course checklist rather than a record of the automated run.

- Student ID suffix: **6042** (use only these four digits).
- IPv4 addresses: h1 `10.42.0.1`, h2 `10.42.0.2`, h3 `10.42.0.3`.
- [Official lab and assignment instructions](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab)
- [P4 lab template](https://github.com/firdaussahran/p4-lab)
- Assignment deadline: **Friday 13 November 2026, before the Week 6 class**.
- Submission: **pull-request URL on Spectrum**. Leave the pull request unmerged.

## What you are learning

A P4 program defines how a switch parses headers, processes packets and rebuilds outgoing packets. You will first add a custom tunnel header to a starter program, then select forwarding using its destination identifier. Finally, you will add a hop limit so tunnel packets cannot circulate indefinitely.

The topology is h1 → s1 → s2, with h2 and h3 attached to s2. s1 port 1 connects to h1 and port 2 to s2. s2 port 1 connects to s1, port 2 to h2 and port 3 to h3. Tunnel destination identifiers are 1, 2 and 3 for h1, h2 and h3 respectively.

## 1. Set up the course environment

- [ ] Create your own GitHub repository using **Use this template** on the P4 lab template, for example named `p4-lab`.
- [ ] Open a **2-core GitHub Codespace** on that repository's `main` branch. The course supplies the P4/BMv2 environment there.
- [ ] Locate `tunnel.p4`, `topo.py`, `send.py`, `receive.py`, `p4cli`, and `assignment/`.
- [ ] Start the lab from the Codespaces terminal:

```bash
python3 topo.py --id 6042
```

This compiles the program and opens a `mininet>` prompt. Enter host commands at that prompt; prefix ordinary shell commands there with `sh`. Use `exit` to return to the Codespaces terminal. Restart the topology after changing P4 source.

This local `week05/` folder now contains the starter files, completed practical P4 source, staged programs and a local Docker walkthrough in START-HERE.md. Runtime verification passed; see RESULTS.md. For the course's exact Codespaces and submission workflow, use a repository created from the template, with its source and configuration at the repository root.

## 2. Complete the practical lab, in order

### Steps 0–2: Setup and ordinary IPv4

- [ ] Finish template/Codespaces setup and launch with `--id 6042`.
- [ ] Read startup output. The unused `myTunnel_exact` table warning is expected at this stage.
- [ ] At `mininet>`, run:

```text
h1 ping -c 3 10.42.0.2
h1 ping -c 3 10.42.0.3
```

- [ ] Confirm both work; expected reply TTL is 62.
- [ ] Inspect `logs/s1.txt`: parser states, table keys, hits/misses and actions.

### Step 3: Change forwarding entries while the network runs

- [ ] Use `p4cli` to dump s2's `MyIngress.ipv4_lpm` table and inspect handles.
- [ ] Delete h3's entry (the course uses handle 2); verify h1-to-h3 ping fails.
- [ ] Restore `10.42.0.3/32` using `MyIngress.ipv4_forward` and output port 3; verify ping works again.
- [ ] Keep the entire table-add expression quoted: its `=>` must not become shell redirection.
- [ ] Use `send.py` on h1 to send to IPv4 destination `10.42.0.3` with tunnel destination **2**, using the course's test-1 payload.
- [ ] Check `logs/h2.txt` and `logs/h3.txt`: neither should receive it yet.
- [ ] Inspect s1's trace for EtherType `0x1212`; explain why the starter parser does not recognise it.
- [ ] Exit Mininet.

Use the exact `p4cli` and `send.py` command syntax and payloads on the official page. The later malformed-packet example depends on the payload length.

### Step 4: Parse and emit the tunnel header

- [ ] In `tunnel.p4`, recognise `TYPE_MYTUNNEL` in the parser's initial selection.
- [ ] Add `parse_myTunnel`: extract the tunnel header and parse IPv4 when `proto_id` is `TYPE_IPV4`; otherwise accept.
- [ ] Emit `hdr.myTunnel` between Ethernet and IPv4 in the deparser.
- [ ] Restart; repeat the conflicting-destination test with the course's test-2 payload.
- [ ] Confirm delivery to **h3**, with the tunnel header retained and TTL **62**. Ingress still uses IPv4 forwarding.
- [ ] Note that the unused tunnel-table warning remains; exit Mininet.

### Step 5: Forward using the tunnel destination

- [ ] Change ingress to apply `myTunnel_exact` when the tunnel header is valid; otherwise apply `ipv4_lpm` for valid IPv4; otherwise drop.
- [ ] Restart and confirm the unused-table warning disappears and table entries are installed.
- [ ] Repeat the conflicting-destination test with the course's test-3 payload.
- [ ] Confirm delivery to **h2**, with IPv4 TTL **64**.
- [ ] Check ordinary IPv4 using `h1 ping -c 2 10.42.0.3`; exit Mininet.

### Step 6: Diagnose a deparser fault

- [ ] Temporarily comment out tunnel-header emission; restart and send the course's test-4 packet.
- [ ] Confirm neither host receives it despite successful compilation.
- [ ] Compare s1 and s2 traces. Explain how s2 interprets IPv4 bytes as tunnel fields when Ethernet still advertises `0x1212`.
- [ ] With the course's exact payload, expected misread values are `proto_id = 0x4500` and `dst_id = 0x0022` (34). Different payload lengths can change the latter.
- [ ] **Restore tunnel-header emission** and exit Mininet.

### Practical wrap-up

- [x] Answer the four lab questions in [LAB-ANSWERS.md](LAB-ANSWERS.md): two more runtime changes versus two program changes; Step 4's destination and retained header; TTL 64 versus 62; compiler warnings versus faults requiring packet tests.
- [x] Include the completed `tunnel.p4`, answers and evidence in the local coursework repository's practical commit. This preserves the assignment baseline locally.
- [ ] Transfer the completed baseline to your separate P4 template repository when setting up that repository.

## 3. Complete the assessed hop-limit assignment

### Preparation

- [x] After completing practical Steps 4 and 5 and restoring the Step 6 edit, copy `tunnel.p4` to **`tunnel_v1.p4`**.
- [x] Create and switch to branch **`hop-limit`**.
- [x] Stage and commit `tunnel_v1.p4` as the preserved original tunnel implementation (baseline commit `b5fc667`).
- [ ] Make meaningful development commits throughout the assignment.

### C1 — Record the loop before protection

- [x] Start the topology with `--id 6042`.
- [x] Dump s2's tunnel table, identify the handle for destination **3**, then modify that entry to output port **1**, back towards s1.
- [x] Send a tunnel packet from h1 to `10.42.0.3` with tunnel destination **3**.
- [x] Count packet-reception records in both switch logs, wait five seconds, then count again to demonstrate continued circulation.
- [x] Save actual commands and outputs to **`assignment/evidence/loop-before.txt`**.
- [x] Stop the topology after the experiment, ending the loop.
- [x] Inspect `ipv4_forward` and explain in `assignment/REPORT.md` why decrementing IPv4 TTL without an expiration check is insufficient.

See [assignment/README.md](assignment/README.md): s1 counts increased 18 → 192 and s2 counts 17 → 192 in the successful fresh run.

### C2 — Specify your design

- [x] Record field width/position, initial value, decrement/drop rules and visit semantics in **`assignment/REPORT.md`** before implementation.
- [x] Choose an appended 8-bit field, default 8, drop incoming 0/1 and otherwise decrement before lookup.

### C3 — Implement the design

- [x] Update **`tunnel.p4`**, **`send.py`** and **`receive.py`** consistently; provide `--hops` and display the remaining limit.
- [x] Compile and test in the official course image. Preserve `tunnel_v1.p4` and original host tools.

### C4 — Verify delivery and loop termination

- [x] Verify delivery to h2/h3 with remaining hops and ordinary IPv4; save **`assignment/evidence/delivery.txt`**.
- [x] Repeat the loop in a fresh network and save **`assignment/evidence/loop-after.txt`**.
- [x] Verify default 8 gives eight total visits and stable counts, plus boundary cases 0/1/2/3.

### C5 — Test mixed versions and discuss deployment

- [x] Save **`assignment/MIXED-PREDICTION.md`** before implementation/testing.
- [x] Run new s1 and old s2 using `--s2-program tunnel_v1.p4`; test delivery, capture bytes and repeat the loop.
- [x] Save **`assignment/evidence/mixed.txt`**, raw logs and decoded measurements.
- [x] Explain checksum/protocol corruption and the 15-visit mixed loop in REPORT.md.
- [x] Compare two safe upgrade approaches, Week 3's required `check_paths()` and hardware costs.

### C6 — Submit

- [x] Finish `assignment/REPORT.md`, including design, observations, analysis and an **AI-use declaration** identifying tools and contributions. AI use is permitted at Level 3 (Open); you must understand and defend the work.
- [x] Check that all four evidence files contain real experimental outputs with your `10.42.0.x` addresses.
- [x] Prepare PR title/body and a standalone review export; see [assignment/SUBMISSION.md](assignment/SUBMISSION.md).
- [ ] Review and authorise commits before publication; the latest C2–C5 changes remain uncommitted as requested.
- [ ] Push branch `hop-limit` and open a PR **inside your own P4 repository**, from `hop-limit` into `main`.
- [ ] Confirm the **Compile tunnel.p4** check passes. The template supplies `.github/workflows/compile.yml`.
- [ ] Make the repository public or give the lecturer collaborator access.
- [ ] Submit the **PR URL on Spectrum** before the deadline; **leave the PR unmerged**.
- [ ] Commit and push all work, then delete the Codespace to release storage quota.

## Required files in the P4 submission repository

```text
tunnel.p4
tunnel_v1.p4
send.py
receive.py
assignment/
  REPORT.md
  evidence/
    loop-before.txt
    delivery.txt
    loop-after.txt
    mixed.txt
```

All listed source/report/evidence files are now present locally. C1–C5 are complete; publication, the GitHub compilation check and Spectrum submission remain pending. Experimental outputs are preserved as recorded.

## Mark allocation

| Criterion | Weight |
|---|---:|
| Loop evidence and IPv4 TTL analysis | 20% |
| Header and pipeline design justification | 20% |
| Implementation, delivery and loop termination | 20% |
| Mixed versions, deployment, control/data-plane comparison and hardware costs | 25% |
| PR quality, development commits and clear report | 15% |

## Troubleshooting

- After an interface-related crash, run `mn -c` in the Codespaces terminal, then relaunch the topology.
- For compiler errors, fix the reported P4 line and restart.
- VS Code may flag `core.p4`/`v1model.p4` incorrectly; use the actual compiler output to judge compilation.
- Inspect switch logs when packets disappear; successful compilation alone does not establish correct forwarding.
- Codespaces may stop after 30 idle minutes. Restarting preserves edits; deleting a Codespace requires committed/pushed work if you want to retain it remotely.
