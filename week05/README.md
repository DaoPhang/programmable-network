# Week 05 — P4 tunnel practical and hop-limit assignment

Student suffix: **6042**. Hosts: **10.42.0.1**, **10.42.0.2**, **10.42.0.3**.

[Official lab](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab) · [Course template](https://github.com/firdaussahran/p4-lab)

## Current status

The practical and assignment C1–C5 are complete locally. The practical passed 31 checks; the hop-limit delivery, loop-boundary and mixed-version experiments passed **26 further assertions** in the official course Docker image.

`tunnel.p4` is the **hop-limit implementation**. `tunnel_v1.p4` preserves the completed practical without a limit. The user published the source, report and evidence to the combined coursework repository in commit `e2e5040` (`Week05`). The separate P4 submission repository/PR, green GitHub compilation check and Spectrum submission remain outstanding.

Start with [assignment/README.md](assignment/README.md) for the complete C1–C6 guide, [assignment/REPORT.md](assignment/REPORT.md) for the design and analysis, and [assignment/SUBMISSION.md](assignment/SUBMISSION.md) for publication status and the remaining submission steps.

## Observed assignment results

| Experiment | Result |
|---|---|
| h2/h3 tunnel delivery, initial 8 | Both received with 6 remaining and IPv4 TTL 64 |
| Ordinary IPv4 | Plain UDP worked; ping received 2/2 replies with TTL 62 |
| All-upgraded loop | Initial 8 stopped after 8 visits: s1=4, s2=4; stable after five seconds |
| Boundary loops | Initial 0/1 dropped at s1; 2 stopped after 2 visits; 3 after 3 |
| Mixed s1 new/s2 old | Frame reached h2 with 7 remaining, but old s2 corrupted the IPv4 protocol/checksum |
| Mixed loop, initial 8 | Stopped after 15 visits: s1=8, s2=7 |

Evidence: [delivery.txt](assignment/evidence/delivery.txt), [loop-after.txt](assignment/evidence/loop-after.txt), [mixed.txt](assignment/evidence/mixed.txt), and the earlier [loop-before.txt](assignment/evidence/loop-before.txt). Each experiment also retains raw logs and structured checks.

## Run the updated program

Inside the supplied privileged course container, from this folder:

```bash
python3 topo.py --id 6042
```

At `mininet>`:

```text
h1 python3 send.py 10.42.0.2 "hello h2" --tunnel 2 --hops 8
h1 python3 send.py 10.42.0.3 "hello h3" --tunnel 3 --hops 8
sh cat logs/h2.txt logs/h3.txt
h1 ping -c 2 10.42.0.3
exit
```

`--hops` defaults to 8 and accepts 0–255. An incoming budget of 0 or 1 drops before forwarding. A positive N allows at most N ingress visits on an all-upgraded path, with the Nth visit dropping; traversing K switches successfully requires N > K.

To reproduce C4/C5, use `python3 assignment/run_assignment.py` in a dedicated course container after preserving the existing evidence. The runner refuses to overwrite results. The Docker launch pattern is documented in [assignment/SUBMISSION.md](assignment/SUBMISSION.md).

## File guide

| Location | Purpose |
|---|---|
| `tunnel.p4`, `send.py`, `receive.py` | Updated five-byte tunnel format and hop enforcement |
| `tunnel_v1.p4` | Unchanged four-byte practical baseline |
| `stages/` | Practical P4 versions plus original sender/receiver for replay |
| `topo.py`, `p4cli`, switch command files | Original topology and table setup |
| `assignment/REPORT.md` | Completed C1–C5 design, observations and evaluation; AI-use declaration |
| `assignment/MIXED-PREDICTION.md` | Original prediction written before implementation/testing |
| `assignment/run_assignment.py` | Actual C4/C5 experiments and assertions |
| `assignment/run_loop_before.py` | C1 replay using preserved P4 and original host tools |
| `assignment/PR-DESCRIPTION.md` | Prepared PR title/body |
| `assignment/prepare_submission.py` | Export a standalone review folder/ZIP without Git publication |
| `LAB-ANSWERS.md`, `RESULTS.md` | Practical answers and original practical observations |
| `run_practical.py` | Practical replay with preserved original host tools |
| `START-HERE.md` | Practical walkthrough; assignment guidance is in `assignment/README.md` |
| `SOURCE.md` | Starter provenance and verification history |

## Repository layout

Everything remains inside `week05/`. GitHub does not discover its nested `.github/workflows/` or `.devcontainer/` as root configuration of the parent coursework repository. The standalone export puts these at the root of a review folder intended for your separate P4 template repository. Only the needed compilation workflow is retained; the template's optional image-publishing workflow has been removed.

The current Git remote is the combined coursework repository. A separate P4 repository and its assignment PR remain to be configured for the course submission. Local P4 compilation passed, but no GitHub Actions result is claimed. Disposable build/review copies, failed-attempt logs and duplicate guides were removed; successful evidence and reproducible test runners are retained. Generate a fresh standalone export with `python -I assignment/prepare_submission.py` when needed.
