# Week 05 — P4 tunnel practical

Student suffix: **6042**. Hosts: **10.42.0.1**, **10.42.0.2**, **10.42.0.3**.

[Official lab](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab) · [Course template](https://github.com/firdaussahran/p4-lab)

## Current status

The official starter files have been copied here. `tunnel.p4` implements the practical's parser, ingress and deparser changes. The temporary Step 6 fault is restored in this final program. The four stages and a repeatable experiment runner are provided.

**All four practical stages compiled and passed their experiment checks in the official course Docker image.** Real transcripts, host logs and switch logs are saved under `evidence/practical/`. See [RESULTS.md](RESULTS.md) for observations and evidence links. The first attempt encountered Windows line endings in `p4cli`; it is preserved under `evidence/practical-attempt01-crlf/`, and the corrected run passed.

The environment used was local Docker rather than Codespaces. The four wrap-up questions are answered in [LAB-ANSWERS.md](LAB-ANSWERS.md). The completed practical, answers and evidence are included in the local practical commit. No separate GitHub repository or Codespace has been created, and nothing has been pushed.

## Start here

1. Read [START-HERE.md](START-HERE.md) for local Docker setup, each practical step, commands and expected observations.
2. Use the staged programs to work through the exercise yourself, or run the recorded experiment sequence with `run_practical.py` inside the course container.
3. Read [RESULTS.md](RESULTS.md), `evidence/practical/summary.json` and the stage-specific raw transcripts and logs from the successful run.
4. Use [PREPARATION.md](PREPARATION.md) for the wider checklist, including the later assessed hop-limit assignment.

## Files

| Location | Purpose |
|---|---|
| `tunnel.p4` | Final practical implementation: tunnel-aware parser, tunnel-table forwarding and correct deparser |
| `stages/step03-starter.p4` | Original IPv4-only starter, for Steps 2–3 |
| `stages/step04-parser-deparser.p4` | Tunnel parsing and emission, still forwarding by IPv4 |
| `stages/step05-tunnel-forwarding.p4` | Completed tunnel forwarding |
| `stages/step06-broken-deparser.p4` | Deliberate missing tunnel emission, for diagnosis only |
| `topo.py` | Original two-switch/three-host Mininet topology |
| `send.py`, `receive.py` | Original packet sender and receiver; hop-limit assignment changes are not included |
| `p4cli`, `s1-commands.txt`, `s2-commands.txt` | Original runtime CLI helper and table entries |
| `run_practical.py` | Runs all four stages in separate working directories and saves actual evidence |
| `START-HERE.md` | Practical walkthrough and launch commands |
| `TEMPLATE-README.md` | Unmodified upstream README |
| `SOURCE.md` | Starter provenance and change scope |
| `.devcontainer/` | Original course Codespaces/dev-container configuration |
| `.github/workflows/` | Original template workflows; see the nested-folder note below |
| `assignment/` | Original, uncompleted report/evidence skeleton for the later assignment |

## Environment and repository layout

The supplied course image is `ghcr.io/firdaussahran/p4-lab:1.0`. It includes P4 compilation, BMv2, Mininet and Scapy. The privileged container creates the virtual network needed for the practical.

All files are kept inside `week05/` as requested. Since this folder is nested inside your coursework repository, GitHub does **not** automatically discover `week05/.github/workflows/` or `week05/.devcontainer/` as root-level configuration. For the course's exact Codespaces and submission workflow, create your own repository from the template and place this folder's contents at that repository's root. For the local Docker workflow, use the commands in START-HERE.md.

The original `week5/` preparation folder has been consolidated into `week05/`.
