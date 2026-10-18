# WIC2005 — Week 1 & Week 2 lab quick guide (Kali Linux)

Verified against the live course pages and Week 2 starter topology/script on **16 October 2026**. Commands were checked against source material, not executed in a Kali/Mininet environment.

Sources: [Week 1 lab](https://firdaussahran.github.io/wic2005/weeks/week-01/#tab-lab), [Week 2 lab and assignment](https://firdaussahran.github.io/wic2005/weeks/week-02/#tab-lab), [official Kali Docker setup](https://www.kali.org/docs/containers/installing-docker-on-kali/).

## 0. Prepare Kali once

Prerequisites: internet access, Docker Engine running, a text editor; Week 2 also needs Git and a GitHub/institutional Git account. The assignment specifically uses GitHub Pages. Mininet, Python and the lab libraries are already in the course container; do not install them separately on Kali for this workflow.

**Kali additions** (installation commands, rather than commands printed in the lab):

```bash
sudo apt update
sudo apt install -y docker.io git curl
sudo systemctl enable docker --now
sudo docker run hello-world
git --version
mkdir -p ~/netlab
cd ~/netlab
```

Use an installed editor such as Mousepad or VS Code. Below, Docker commands have `sudo` added for Kali permissions. Alternatively, the course/Kali instructions allow `sudo usermod -aG docker $USER`, then logging out and back in, after which omit `sudo`.

**Know your terminals:**

- **Kali:** download/edit files, start Docker and run Git. Start Docker while inside `~/netlab`.
- **Container shell:** run `mn`, Python scripts and conversions. The shared directory is `/lab`.
- **`mininet>`:** enter host/network commands. Do not type the prompt itself.

Files in `/lab` persist in your Kali `netlab` directory; other container changes disappear on exit because of `--rm`.

Pre-class preparation on the pages: Week 1 enrol in Linux Essentials, Python Essentials 2 and DevNet Associate using your university student email, and read Feamster, Rexford & Zegura, *The Road to SDN*. Week 2 preparation is NetAcad **Software Development and Design**.

## 1. Week 1 — Ethernet without a controller

**Submission: nothing to hand in; explore.**

1. **Kali:** start the container (same command as the page, with `sudo`):

```bash
sudo docker run -it --rm --privileged -v "${PWD}:/lab" -w /lab firdaussahran/netlab-mininet:1.0
```

2. **Container shell:** create one Linux bridge and three hosts:

```bash
mn --topo single,3 --mac --switch lxbr --controller none
```

3. **`mininet>`:** inspect devices and links. Identify the `s1`–`h2` connection in `net`:

```text
nodes
net
dump
```

4. Inspect the tables **before traffic**, then after a ping:

```text
h1 ip neigh
sh brctl showmacs s1
h1 ping -c 3 h2
h1 ip neigh
sh brctl showmacs s1
pingall
```

Initially h1's neighbour table is empty and the bridge lists its own ports. After ping, h1 knows `10.0.0.2` → `00:00:00:00:00:02`; the bridge learns h1/h2's source MACs. h3 stays unknown until it transmits.

5. Break and restore h3's connection; observe failures and recovery:

```text
link s1 h3 down
pingall
link s1 h3 up
pingall
```

6. Start a web server on h2 and fetch it from h1:

```text
h2 python3 -m http.server 80 &
h1 curl h2
exit
```

You are back in the container shell. Enter `exit` again to return to Kali.

Think about: how does the bridge learn forwarding ports? Where are the control and management planes? What could go wrong repeating a manual change across 40 switches?

## 2. Week 2 — Build a network from data and track it in Git

### 1) Download and personalise the starter files

**Kali, inside `~/netlab`:** the following `curl` commands are convenience additions using the exact download links from the page.

```bash
curl -fLO https://firdaussahran.github.io/wic2005/labs/week-02/build_topo.py
curl -fLO https://firdaussahran.github.io/wic2005/labs/week-02/topology.yaml
```

Open and read both. In `topology.yaml`, replace **NNNN first**, then **NN**:

- `NNNN`: last four student-ID digits, kept as a quoted string in `student_id_last4`.
- `NN`: last two digits as a number without a leading zero.
- Your blocks: `10.NN.0.0/16` and `fd00:NNNN::/32`.
- Example only: ending `4207` means `student_id_last4: "4207"`, h1 IPv4 `10.7.0.1/24`, IPv6 `fd00:4207::1/64`.

Use your own digits in **all** commands below. Never put your full student ID in the files. YAML uses spaces, not tabs.

### 2) Build and test

Start the same Docker command from section 1. **Container shell:**

```bash
python3 build_topo.py topology.yaml
```

**`mininet>`:**

```text
net
pingall
h1 ping -6 -c 1 fd00:NNNN::2
h1 ip neigh
exit
```

`pingall` tests IPv4 only. The IPv6 ping demonstrates Neighbour Discovery; the table should contain IPv4 and IPv6 neighbours. Stay in the container shell after `exit`.

Keep **two terminals** open from here: container for Mininet; a second Kali terminal in `~/netlab` for Git and editing.

### 3) Start Git (Kali terminal)

```bash
git init
git add build_topo.py topology.yaml
git commit -m "Week 2: starting topology"
```

If Git requests an identity, configure it and retry the commit. The page uses a name/email example; for the assignment, use an appropriate pseudonym and GitHub no-reply email to respect its no-name rule:

```bash
git config user.name "YOUR_PSEUDONYM"
git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"
```

These local configuration commands are an adaptation of the page's global identity setup.

### 4) Grow the network

Edit `topology.yaml`: add `s2` under `switches`, h4 under `hosts` with `ip: 10.NN.0.4/24` and `ipv6: fd00:NNNN::4/64`, and links `[h4, s2]` and `[s1, s2]`.

**Container shell:** rebuild with `python3 build_topo.py topology.yaml`; at `mininet>` run `pingall` (expect **12/12 replies**), then `exit`.

**Kali:**

```bash
git diff
git commit -am "Add s2 and h4"
```

### 5) Convert YAML to JSON (container shell)

```bash
python3 -c "import yaml, json; print(json.dumps(yaml.safe_load(open('topology.yaml')), indent=2))" > topology.json
python3 build_topo.py topology.json
```

Run `pingall`, then `exit`. Compare both files: the model is identical; JSON loses the YAML comments.

### 6) Demonstrate duplicates, then implement validation

In **topology.yaml**, temporarily give h4 h2's addresses: `10.NN.0.2/24` and `fd00:NNNN::2/64`. Build the YAML again and run `pingall`. The page describes only **one failure out of 12**; treat this as its example, since duplicate-address results can vary with timing.

At `mininet>`:

```text
h2 ip -6 addr show dev h2-eth0
h4 ip -6 addr show dev h4-eth0
exit
```

Look for IPv6 `dadfailed` on one host. IPv4 can silently use duplicate addresses.

Now fill in **`check(spec)` in `build_topo.py`** (the starter leaves it as a TODO). Check both `ip` and optional `ipv6` for every host, remove the `/prefix`, and track address → host in a dictionary. Append a problem when another host uses the same address. The supplied `check_mine()` already checks personal address blocks; leave it in place.

Rebuild the bad YAML: it must stop **before Mininet starts**, with `PROBLEM` messages for both duplicate addresses. Restore h4 to `.4` / `::4`, confirm it builds, exit Mininet, then **Kali**:

```bash
git commit -am "Check for duplicate IP addresses"
```

### 7) Push (Kali)

Create an **empty** remote repository; use GitHub if continuing to the assignment. Replace the URL placeholder, including its angle brackets:

```bash
git branch -M main
git remote add origin <your repository URL>
git push -u origin main
```

For HTTPS authentication use a personal access token when prompted, or use an SSH remote/key. Your GitHub account password does not work for Git pushes.

## 3. Week 2 assignment — Your network, published

**Due before the Week 3 class, Friday 23 October 2026. Submit your GitHub Pages link on Spectrum.** This counts toward the lab portfolio. Continue in the same `netlab` folder/repository.

### A1–A2: Get files and design your own topology

**Kali** (download convenience commands):

```bash
curl -fLO https://firdaussahran.github.io/wic2005/labs/week-02/make_page.py
curl -fLO https://firdaussahran.github.io/wic2005/labs/week-02/page.yaml
```

Design **at least 3 switches and 6 hosts**, every host with IPv4 and IPv6 in your own blocks, with connectivity between all hosts. A simple connected switch tree is a practical choice. Build in the container, run `pingall` and obtain **0% dropped**, then exit and commit your design.

### A3: Validate addresses and links

Extend `check()` to reject links whose endpoints are absent from the declared switches/hosts, as well as duplicate IPv4/IPv6 addresses.

Copy `topology.yaml` to `bad.yaml` (e.g. `cp topology.yaml bad.yaml` in the container). In **bad.yaml only**, duplicate a host address and add a link to a nonexistent switch. Capture the rejection in the **container shell**:

```bash
mkdir -p evidence
python3 build_topo.py bad.yaml > evidence/check.txt 2>&1
```

Confirm the file contains a `PROBLEM` line for each mistake. Commit the validator, bad example and evidence from Kali.

### A4: Collect running-network evidence

Build the **good** `topology.yaml` again. At **`mininet>`**, replace the address placeholders and adapt host/switch/interface names if you changed them:

```text
pingall
h1 ping -6 -c 1 fd00:NNNN::2
h1 ip neigh > evidence/neigh.txt
sh brctl showmacs s1 > evidence/macs.txt
h2 ip -6 addr add fd00:NNNN::1/64 dev h2-eth0
h2 ip addr add 10.NN.0.1/24 dev h2-eth0
sh sleep 3
h2 ip -6 addr show dev h2-eth0 > evidence/dad.txt
h2 ip -4 addr show dev h2-eth0 >> evidence/dad.txt
exit
```

Copy the earlier `pingall` terminal output into **`evidence/pingall.txt`** yourself. The deliberate duplicates above demonstrate IPv6 DAD versus IPv4 acceptance; they change the running network, not your good YAML. Commit `evidence/`.

### A5: Complete and generate the page

**Container shell:**

```bash
python3 make_page.py topology.yaml
```

Open `docs/index.html` in your Kali browser. Complete these TODO functions in `make_page.py`:

- `links_section()`: list every network link.
- `mermaid_diagram()`: generate Mermaid from links, one line per link; follow its docstring and start with `graph LR`.

In `page.yaml`, set `repository:` to your repository address and write your own answers, including the lab wrap-up questions: model versus serialisation; validation versus `pingall` and what IPv6 detected; why `git diff` beats copied version folders. Answer all prompts in the supplied file using your actual network/evidence.

Regenerate after changes to topology, answers or generator code. Check the page online so Mermaid can load. Commit **`docs/` and all other assignment files**. For example, these added staging commands include new files that `git commit -am` would miss:

```bash
git add build_topo.py topology.yaml topology.json bad.yaml make_page.py page.yaml evidence/ docs/
git commit -m "Complete network page and evidence"
git push
```

Run Git in Kali, not inside the container. Make **at least five meaningful commits** over the assignment's progress, rather than saving everything for one final commit.

### A6: Publish and submit

On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → main → /docs → Save**. After a minute or two, open:

```text
https://<your-username>.github.io/<your-repository>/
```

Verify the network, links, diagram, answers and evidence display; submit this URL on Spectrum. The course says free accounts need a public repository; eligible GitHub Education benefits can permit a private repository, but the published page remains public. **No name or full student ID anywhere in the repository; only the last four digits.** Use your own topology and wording.

Marking: network **20%**; duplicate/bad-link validation **20%**; generated links/diagram/page **20%**; evidence **15%**; explanations **15%**; progressing Git history (≥5 commits) **10%**.

## Quick fixes

- Docker daemon unavailable: on Kali, `sudo systemctl start docker`; use `sudo docker ...` for permission errors.
- First image download takes time (page estimates about 265 MB). For download issues, page diagnostic: `sudo docker run alpine ping -c 3 8.8.8.8`.
- Mininet hangs adding hosts: restart the container with the full `--privileged` command.
- Leftover Mininet devices: run `mn -c` in the container shell, then rebuild.
- Script missing: start Docker from `~/netlab`; `ls` inside `/lab` must show your files.
- YAML/KeyError: compare starter indentation and keys; use spaces, not tabs.
- Address `PROBLEM`: replace every placeholder; `10.07.0.1` is invalid, use `10.7.0.1`.
- Page generator `PROBLEM`: fix topology validation first. Missing-evidence warnings: collect all five files and regenerate.
- Pages 404: wait two minutes, then verify `main`, `/docs`, and committed/pushed `docs/index.html`.
- Container-created files may be root-owned on Kali. If editing is denied, a Kali-specific fix from inside `~/netlab` is `sudo chown -R "$(id -u):$(id -g)" evidence docs topology.json` (include only paths that exist).
- Docker Hub unavailable: the page links [netlab-mininet.Dockerfile](https://firdaussahran.github.io/wic2005/labs/week-01/netlab-mininet.Dockerfile). Download it into an empty folder and run `sudo docker build -t firdaussahran/netlab-mininet:1.0 -f netlab-mininet.Dockerfile .`; it still needs internet for Ubuntu packages.

**Verification note:** the lab command sequences, filenames, image tag, task requirements and deadline above were checked against the fetched course HTML. The starter files confirm `check()` is intentionally unfinished and `check_mine()` is supplied. Kali installation, `sudo`, download/staging commands, identity privacy adaptation and file-ownership advice are explicitly added conveniences. Timing-dependent ping/DAD output is an observation to inspect, not a guaranteed exact result.
