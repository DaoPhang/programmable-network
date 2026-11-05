# Programmable Network

WIC2005 coursework for student ID suffix **6042**, organised by week. This repository contains lab programs, write-ups and saved experimental evidence.

| Location | Contents and status |
|---|---|
| [week2/](week2/) | Three-switch, six-host dual-stack topology, input validation, webpage generator, evidence and assignment report |
| [week3/](week3/) | Three-router routing experiments and completed write-up; observations preserved as excerpts rather than a raw session log |
| [week4/](week4/README.md) | OpenFlow forwarding, firewall rules, controller failure and standalone fallback; wrap-up answers and a partial session log |
| [week05/](week05/README.md) | Completed P4 tunnel practical and hop-limit assignment C1–C5, preserved baseline, report, test runners and successful evidence |
| [docs/](docs/) | Generated Week 2 website; GitHub Pages source is `main` → `/docs` |
| [archive/](archive/) | Historical Week 1/2 logs and duplicate-address example |
| [start-lab-wsl.sh](start-lab-wsl.sh) | Optional WSL launcher for the Weeks 2–4 Mininet image |

## Run Weeks 2–4

Start Docker Desktop with Linux containers enabled. From the repository root in VS Code PowerShell:

```powershell
docker version
docker run -it --rm --privileged -v "$($PWD.Path):/lab" -w /lab firdaussahran/netlab-mininet:1.0
```

Docker provides the Linux environment. Run the following Linux commands inside the container, and enter host or switch commands at the `mininet>` prompt after a topology starts. Type `exit` to stop Mininet and return to the container shell.

### Week 2 — topology, validation and website

```bash
cd /lab/week2
python3 build_topo.py topology.yaml
```

At `mininet>`, run `pingall`; six hosts should produce **30/30 received**. After leaving Mininet, regenerate the website with:

```bash
python3 make_page.py topology.yaml
```

The generator writes the repository's `docs/index.html`. The deliberate `bad.yaml` and JSON topology input support the validation exercises. See the [setup guide](week2/guides/START-HERE.md) and [assignment report](week2/guides/ASSIGNMENT-REPORT.md). Some older guides retain the former `lab-02` name; use `week2/` for the current folder.

### Week 3 — routing and longest-prefix matching

```bash
cd /lab/week3
python3 routers.py --id 6042
```

Follow the [Week 3 instructions](week3/README.md) for forwarding and static route configuration. The [completed write-up](week3/6042_Lab3_Writeup.md) covers route selection, fallback, unreachable destinations, routing loops and IPv6. Its observations use excerpts from the completed run; a raw terminal log was not supplied.

### Week 4 — control plane separation and OpenFlow

```bash
mn --topo single,3 --mac --switch ovs,datapath=user --controller none --ipbase 10.42.0.0/24
```

The [Week 4 README](week4/README.md) records hub and manual forwarding, firewall priority, reactive controller flows, controller failure and standalone fallback, with all three wrap-up answers. The [saved session log](week4/evidence/session.log) covers Steps 0–4 and part of Step 5. Later Step 5 and Step 6 observations came from shared terminal output and are identified in the write-up.

## Run Week 5 — P4 tunnel and hop limit

Week 5 uses the official **P4 image**, which contains BMv2 and the P4 compiler. From the repository root in PowerShell:

```powershell
Set-Location .\week05
$week05Path = (Get-Location).Path
docker run -it --rm --privileged --mount "type=bind,source=$week05Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 bash
```

Inside this container:

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

The active `tunnel.p4`, `send.py` and `receive.py` implement the five-byte tunnel header with an 8-bit hop limit. The unchanged `tunnel_v1.p4` and original packet tools in `stages/` preserve the practical baseline.

Completed validation in the official course image:

- **31 practical assertions passed**, covering IPv4, runtime table edits, tunnel parsing/forwarding and the deliberate deparser fault.
- **26 assignment assertions passed**, covering delivery, argument and hop boundaries, protected loops and mixed-version deployment.
- Normal two-switch delivery with initial hops 8 arrived with **6 remaining**. The all-upgraded loop stopped after **8 switch visits**.
- Mixed deployment stopped the tested loop after **15 visits**, but the old switch corrupted the inner IPv4 packet. The report explains why the new format requires a deployment strategy.
- Independent reviewers repeated the experiments and recorded **59 passing checks**, including two additional evidence checks; see the [review summary](week05/assignment/REVIEW.md).

Start with the [Week 5 overview](week05/README.md), [practical answers](week05/LAB-ANSWERS.md), [assignment guide](week05/assignment/README.md) and [full report](week05/assignment/REPORT.md). The assignment guide links all four required evidence transcripts and provides reproduction instructions. Runners refuse to overwrite existing evidence; preserve it before repeating experiments.

The source, report and evidence are published in this combined coursework repository. **Course submission remains outstanding:** a separate P4 template repository, an unmerged PR titled **Tunnel hop limit**, a green **Compile tunnel.p4** check, lecturer access and the PR URL submitted on Spectrum. The deadline is **Friday 13 November 2026, before the Week 6 class**. See the [C6 instructions](week05/assignment/README.md#c6--prepare-and-submit).

Week 5's `.github/` and `.devcontainer/` are nested inside `week05/`; GitHub does not use them as root configuration for this combined repository. The assignment guide explains the standalone export for the separate P4 repository.

## Optional WSL workflow

From the repository root in WSL:

```bash
bash start-lab-wsl.sh
```

Then use the Weeks 2–4 container commands above. For Week 5, use its P4 image and mount `week05/` at `/lab` as shown above.

## Evidence and course links

Week 2 evidence is in [week2/evidence/](week2/evidence/), Week 3 observations are in its write-up, and Week 4's saved log has the coverage limits described above. Week 5 retains successful practical evidence in [week05/evidence/practical/](week05/evidence/practical/) and assignment evidence in [week05/assignment/evidence/](week05/assignment/evidence/). Historical logs remain in `archive/`; generated build copies and failed Week 5 attempts were removed during cleanup.

Course labs: [Week 2](https://firdaussahran.github.io/wic2005/weeks/week-02/#tab-lab) · [Week 3](https://firdaussahran.github.io/wic2005/weeks/week-03/#tab-lab) · [Week 4](https://firdaussahran.github.io/wic2005/weeks/week-04/#tab-lab) · [Week 5](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab).
