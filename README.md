# Programmable Network

WIC2005 network labs: three switches and six dual-stack hosts described as data.

## Run the lab

From an Ubuntu/WSL terminal in this repository, with Docker Desktop running:

```bash
bash start-lab-wsl.sh
```

Inside the container:

```bash
python3 build_topo.py topology.yaml
```

At the Mininet prompt, run `pingall`. For six hosts, expect `30/30 received`.

## Project layout

| Location | Purpose |
|---|---|
| `topology.yaml`, `topology.json` | Current network in two formats |
| `build_topo.py` | Validate and build the network |
| `bad.yaml` | Invalid topology for validation evidence |
| `make_page.py`, `page.yaml` | Webpage generator and explanations |
| `start-lab-wsl.sh` | Portable container launcher |
| `evidence/` | Current assignment evidence |
| `docs/` | Generated GitHub Pages website |
| `guides/` | Setup instructions, assignment report and reference guide |
| `archive/lab-logs/` | Historical runs of earlier networks |
| `archive/examples/` | Earlier duplicate-address example |

See [setup instructions](guides/START-HERE.md) and the [assignment report](guides/ASSIGNMENT-REPORT.md). Run commands from the repository root, including those shown in the guides. Historical logs do not replace current evidence.

Regenerate the webpage inside the container after changing topology, explanations or evidence:

```bash
python3 make_page.py topology.yaml
```

GitHub Pages uses the `main` branch's `/docs` folder. Review the written answers and rendered page before submitting.

Course sources: [Week 1](https://firdaussahran.github.io/wic2005/weeks/week-01/#tab-lab) and [Week 2](https://firdaussahran.github.io/wic2005/weeks/week-02/#tab-lab).
