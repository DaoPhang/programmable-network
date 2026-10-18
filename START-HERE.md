# Your lab status — student suffix 6042

Completed on 18 October 2026:
- Docker Desktop started; course image downloaded; hello-world passed.
- Ubuntu installed in WSL 2; Windows folder access verified.
- Week 1: initial tables, ping, link failure/recovery and HTTP fetch executed. See week1-run.txt.
- Week 2: initial IPv4/IPv6 passed; two-switch/four-host expansion passed 12/12; JSON passed 12/12.
- Duplicate experiment: 11/12 replies and IPv6 dadfailed observed. See week2-duplicates-run.txt.
- check() now rejects duplicate IPv4/IPv6 and unknown link endpoints. Duplicates verified rejected.
- Local Git history records the starting topology, growth and validation. Commits use placeholder identity student-6042 / student-6042@users.invalid; replace it with your preferred pseudonym/no-reply email before publishing.

## Open the lab from Ubuntu

```bash
cd '/mnt/c/Users/dtpha/Documents/Programmable Network'
bash start-lab-wsl.sh
```

This opens the container. Inside:

```bash
python3 build_topo.py topology.yaml
```

At mininet>, run pingall. Type exit once to leave Mininet, then again to leave the container.

The launcher uses Windows docker.exe, verified from Ubuntu, so it works with the current setup. For the normal Linux docker command, enable Ubuntu under Docker Desktop > Settings > Resources > WSL Integration and Apply. No second Docker Engine installation is needed.

Ubuntu was verified using its root account for automation. When you open Ubuntu normally, complete any first-launch username/password setup it requests.

## Still needed for the marked assignment

The four-host topology is the completed lab, not the final assignment design. The assignment requires at least three switches and six hosts, your own explanations in page.yaml, completion of links_section()/mermaid_diagram() in make_page.py, bad-link evidence, running-network evidence, and generated docs/index.html. Aim for at least five meaningful commits.

A remote was not added and nothing was uploaded. Your GitHub repository URL is needed for the push/Pages steps. Do not commit real names, full student IDs, passwords or tokens. The marked assignment is due before class on 23 October 2026; submit the Pages URL on Spectrum.

The Kali guide is reference material; skip its Docker installation steps for this Docker Desktop/WSL setup. Runtime logs here record the actual checks on your machine. Resource-limit and bridge-nf warnings appeared, but the connectivity tests passed.
