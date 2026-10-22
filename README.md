# Programmable Network

WIC2005 coursework for student ID suffix **6042**, organised by lab.

| Location | Purpose |
|---|---|
| [lab-02/](lab-02/) | Three switches, six dual-stack hosts; topology, validation, webpage generator, evidence and guides |
| [lab-03/](lab-03/) | Three routers, three hosts; routing experiment and write-up |
| [docs/](docs/) | Generated Lab 2 GitHub Pages website |
| archive/ | Historical Week 1 and Week 2 logs and earlier duplicate-address example |
| start-lab-wsl.sh | Optional shared WSL container launcher |

## Start from VS Code PowerShell

Start Docker Desktop. Open the repository root in VS Code and run:

~~~powershell
docker version
docker run -it --rm --privileged -v "$($PWD.Path):/lab" -w /lab firdaussahran/netlab-mininet:1.0
~~~

Docker supplies the Linux container; PowerShell is a valid host terminal.
Use Linux commands after reaching the container shell.

## Lab 2

Inside the container:

~~~bash
cd /lab/lab-02
python3 build_topo.py topology.yaml
~~~

At mininet>, run pingall; six hosts should produce 30/30 received.
Type exit to return to the container shell. To regenerate the website:

~~~bash
python3 make_page.py topology.yaml
~~~

The generator writes to the repository's root docs/index.html.
Keep GitHub Pages configured for main and /docs.
The deliberate bad.yaml and JSON equivalent are useful lab inputs.
See [Lab 2 setup](lab-02/guides/START-HERE.md) and
[assignment report](lab-02/guides/ASSIGNMENT-REPORT.md).

## Lab 3

Inside the container:

~~~bash
cd /lab/lab-03
mkdir -p evidence
python3 routers.py --id 6042
~~~

This lab covers forwarding, static routes, longest-prefix matching, route
fallback, unreachable destinations, loops, and IPv6.

See [Lab 3 instructions](lab-03/README.md) and
[6042_Lab3_Writeup.md](lab-03/6042_Lab3_Writeup.md).
The write-up uses outputs pasted from the completed run. Raw terminal logs
have not been reconstructed; keep any original logs or screenshots separately.
Submit the reviewed write-up on Spectrum as instructed.

## Optional WSL workflow

From the repository root in WSL:

~~~bash
bash start-lab-wsl.sh
~~~

Then use the same container commands above.

## Records and changes

Current Lab 2 evidence stays in lab-02/evidence. Keep future Lab 3 evidence
in lab-03/evidence. Historical archive files are retained as useful records.
No files were deleted during organisation.

The existing generated website is preserved; it has not been regenerated or
published by this cleanup. Review git status and git diff before committing.
No commit, push, deployment, or Spectrum submission is performed here.

Course: [Week 2](https://firdaussahran.github.io/wic2005/weeks/week-02/#tab-lab)
and [Week 3](https://firdaussahran.github.io/wic2005/weeks/week-03/#tab-lab).