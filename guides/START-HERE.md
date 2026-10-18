# Start here

This repository contains the WIC2005 Week 1 and Week 2 Mininet lab work for student suffix `6042`. The current topology describes three switches and six dual-stack hosts.

## Run in Ubuntu / WSL 2

Start Docker Desktop. Enable your Ubuntu distribution under **Settings > Resources > WSL Integration**. Open an Ubuntu terminal in this repository, then run:

```bash
bash start-lab-wsl.sh
```

The launcher uses the directory containing the script, so no personal machine path is required. It prefers the Linux `docker` command and falls back to `docker.exe` if that client is available on WSL's PATH. The course container requires privileged mode to create its virtual network.

Inside the container:

```bash
python3 build_topo.py topology.yaml
```

At the `mininet>` prompt:

```text
net
pingall
h1 ping -6 -c 3 fd00:6042::6
exit
```

For six hosts, successful IPv4 connectivity reports `0% dropped (30/30 received)`. The separate IPv6 command checks IPv6 reachability. Type `exit` again at the container shell to return to Ubuntu. No Docker Compose file is required.

## Assignment files

- `topology.yaml`: network specification; `topology.json`: its JSON equivalent.
- `build_topo.py`: validation and network creation.
- `bad.yaml`: deliberately invalid input for validation tests, when present.
- `make_page.py` and `page.yaml`: webpage generator and written explanations.
- `evidence/`: current assignment test output, when collected.
- `docs/index.html`: generated page for GitHub Pages, when built.

Run `python3 make_page.py topology.yaml` inside the container after editing page content or evidence. Review the generated page before publishing it.

## Historical logs

The `archive/lab-logs/week1-run.txt` and `archive/lab-logs/week2-*.txt` files are earlier experiment records. Some describe smaller networks. Keep them as history; use the files in `evidence/` to assess the final topology. Historical logs do not replace current assignment evidence.

The Kali lab guide is optional reference material. With Docker Desktop and WSL integration, skip its Kali-specific Docker installation steps.

## Git and publication

Use PowerShell in this repository for Git, or Git installed in Ubuntu. Inspect `git status` and `git diff` before committing. The remote repository is https://github.com/DaoPhang/programmable-network.

Push reviewed commits, then configure GitHub Pages to deploy the `main` branch's `/docs` folder. Confirm that the published page renders correctly and submit its URL as instructed by the course. Generating a local page does not publish it or submit the assignment.

Only the suffix `6042` is needed in the coursework. Keep full student IDs, credentials, local secrets and personal machine paths out of public files.
