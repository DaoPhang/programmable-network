# Practical lab walkthrough — Steps 1–7 of your requested list

These instructions use your student suffix **6042** and **10.42.0.x** addresses. All four stages have now been run successfully in the official course Docker image. Below, **expected** describes what to look for when repeating the exercise; RESULTS.md records the actual observations and links to the saved evidence.

The active `tunnel.p4`, `send.py` and `receive.py` now contain the later hop-limit assignment. To replay this original practical safely, use `run_practical.py`, which selects the preserved original packet tools and runs in separate directories. The manual stage-copy commands below are for a separate practical workspace: use `stages/send_v1.py` as its `send.py` and `stages/receive_v1.py` as its `receive.py`. Do not replace the assignment sources to replay the practical.

## 1. Choose the environment

### Course workflow: template repository and Codespaces

Create your own repository from https://github.com/firdaussahran/p4-lab and open a two-core Codespace. Copy the relevant local files there if continuing this implementation. Keep its files at the repository root so its `.devcontainer/` and `.github/workflows/` work normally.

A personal template repository and Codespace have not been created by this preparation.

### Local workflow: Docker Desktop on Windows

The same course image can run locally. Start Docker Desktop and make sure it is using Linux containers. Open PowerShell at your coursework repository root:

```powershell
Set-Location .\week5
$week5Path = (Get-Location).Path
docker run -it --rm --privileged --mount "type=bind,source=$week5Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 bash
```

The remaining manual commands run **inside this container**, which starts at `/lab`. This directory is your local `week5` folder mounted into Linux. Files saved here remain on Windows after the container exits.

Before running a stage, back up any `logs/` output you want to keep: topology restarts reuse the log paths.

## 2. Start the IPv4-only program and inspect forwarding

At the **container shell**, select the starter and start the topology:

```bash
cp stages/step03-starter.p4 tunnel.p4
python3 topo.py --id 6042
```

At **`mininet>`**:

```text
h1 ping -c 3 10.42.0.2
h1 ping -c 3 10.42.0.3
sh less logs/s1.txt
```

Press `q` to leave `less` and return to Mininet.

Expected: both pings succeed and replies have TTL 62. Both switches run IPv4 forwarding, each decreasing TTL once. Startup warns that the tunnel table is unused, so its entries are skipped.

In the log, identify Ethernet and IPv4 extraction, the IPv4 destination key, the table hit and `ipv4_forward` action.

## 3. Change forwarding entries at runtime

At **`mininet>`**:

```text
sh sh ./p4cli s2 table_dump MyIngress.ipv4_lpm
```

Check the dump first. In the supplied entry order, h3's entry has handle **2**. If your dump differs, substitute its actual handle below.

```text
sh sh ./p4cli s2 table_delete MyIngress.ipv4_lpm 2
h1 ping -c 2 -W 1 10.42.0.3
sh sh ./p4cli s2 "table_add MyIngress.ipv4_lpm MyIngress.ipv4_forward 10.42.0.3/32 => 3"
h1 ping -c 2 10.42.0.3
```

Expected: deletion breaks h3 connectivity; restoring its /32 entry to s2 port 3 restores connectivity. These edits do not recompile P4.

The doubled `sh` is intentional: the first is Mininet's shell escape; the second runs `p4cli` using the shell even when Windows-mounted files lack Unix executable permission.

Now send a packet whose IPv4 destination is **h3** but whose tunnel destination is **2 (h2)**:

```text
sh sleep 2
h1 python3 send.py 10.42.0.3 "test 1" --tunnel 2
sh sleep 2
sh cat logs/h2.txt logs/h3.txt
sh less logs/s1.txt
```

Expected: neither host receives the packet. The starter parser does not recognise EtherType `0x1212`, leaving IPv4 invalid; ingress drops the packet. The two-second pauses allow receivers to attach and log asynchronous traffic.

After inspecting the logs, press `q` and type `exit` to return to the container shell.

## 4. Add tunnel parsing and emission

The completed Step 4 program has three changes:

- Ethernet type `TYPE_MYTUNNEL` transitions to `parse_myTunnel`.
- That parser state extracts `hdr.myTunnel`, then parses IPv4 when `proto_id` is `TYPE_IPV4`.
- The deparser emits Ethernet, then MyTunnel, then IPv4.

At the **container shell**:

```bash
cp stages/step04-parser-deparser.p4 tunnel.p4
python3 topo.py --id 6042
```

At **`mininet>`**:

```text
sh sleep 2
h1 python3 send.py 10.42.0.3 "test 2" --tunnel 2
sh sleep 2
sh cat logs/h2.txt logs/h3.txt
exit
```

Expected: **h3** receives a tunnelled packet with `dst_id=2` and **TTL 62**. Parsing and emission now support the tunnel, but ingress still chooses the IPv4 table. The tunnel table is still unused.

## 5. Activate tunnel-destination forwarding

The final ingress selection is:

```p4
if (hdr.myTunnel.isValid()) {
    myTunnel_exact.apply();
} else if (hdr.ipv4.isValid()) {
    ipv4_lpm.apply();
} else {
    drop();
}
```

At the **container shell**:

```bash
cp stages/step05-tunnel-forwarding.p4 tunnel.p4
python3 topo.py --id 6042
```

At **`mininet>`**:

```text
sh sleep 2
h1 python3 send.py 10.42.0.3 "test 3" --tunnel 2
sh sleep 2
sh cat logs/h2.txt logs/h3.txt
h1 ping -c 2 10.42.0.3
exit
```

Expected: **h2** receives the packet with **TTL 64**, although the enclosed IPv4 destination remains `10.42.0.3`. Both switches use the tunnel action, which does not change IPv4 TTL. Normal IPv4 ping still works. The unused tunnel-table warning disappears, and six entries load per switch.

## 6. Introduce and diagnose the deparser fault

At the **container shell**:

```bash
cp stages/step06-broken-deparser.p4 tunnel.p4
python3 topo.py --id 6042
```

At **`mininet>`**:

```text
sh sleep 2
h1 python3 send.py 10.42.0.3 "test 4" --tunnel 2
sh sleep 2
sh cat logs/h2.txt logs/h3.txt
sh less logs/s1.txt
sh less logs/s2.txt
exit
```

Use `q` to leave each log viewer before entering the next command.

Expected: compilation succeeds, but neither host receives the UDP test. s1 parses and forwards using tunnel destination 2, then emits a packet missing the tunnel bytes while retaining Ethernet type `0x1212`. s2 therefore treats the first four IPv4 bytes as the tunnel header:

| Tunnel field read by s2 | Expected value | Actual byte source |
|---|---|---|
| `proto_id` | `0x4500` | IPv4 version/header length and service byte |
| `dst_id` | `0x0022` (34) | IPv4 total length: 20-byte IP + 8-byte UDP + 6-byte `test 4` payload |

Destination 34 has no tunnel entry, so s2 drops it. This illustrates why compilation must be followed by packet tests and log inspection.

## 7. Restore the final program

At the **container shell**:

```bash
cp stages/step05-tunnel-forwarding.p4 tunnel.p4
```

The final program must contain `packet.emit(hdr.myTunnel);`. You can rerun Step 5 to verify restoration, then exit the container with `exit`.

## Automated recording of the same experiments

The runner uses an independent working directory for each stage and leaves your final `tunnel.p4` unchanged. It runs the same pings, runtime entry changes and test packets, and saves raw switch/host logs. Run it inside a dedicated course container; it calls `mn -c` to clean up between stages.

From **PowerShell**, with the working directory at `week5`:

```powershell
$week5Path = (Get-Location).Path
docker run --rm --privileged --mount "type=bind,source=$week5Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 python3 run_practical.py
```

Or, from the **container shell**, use:

```bash
python3 run_practical.py
```

Results are written to:

```text
evidence/practical/
  summary.json
  step03-starter/
    commands.txt
    session.txt
    cleanup.txt
    logs/
  step04-parser-deparser/
    ...
  step05-tunnel-forwarding/
    ...
  step06-broken-deparser/
    ...
```

The runner stops on a failed check and refuses to overwrite existing evidence. Read its summary alongside the raw logs before deciding a stage passed. If repeating, move the previous `evidence/practical` directory to a separately named backup first.

## Windows troubleshooting observed during setup

- The first run encountered `p4cli: 5: Syntax error: word unexpected (expecting "in")`. Git had checked out that shell script with CRLF endings. The helper was normalised to LF, and `.gitattributes` now keeps Linux shell/P4/Python files in LF format.
- Mininet can print `Error setting resource limits. Mininet's performance may be affected.` inside Docker. The runner records that warning and checks actual packet delivery; it does not treat that warning alone as a runtime table error.
- The initial failed experiment's logs were removed during cleanup; they remain available in Git history. The successful practical evidence is retained.

## What remains after this practical

The four wrap-up lab questions are answered in [LAB-ANSWERS.md](LAB-ANSWERS.md). The hop-limit assignment C1–C5 are complete; see [assignment/README.md](assignment/README.md) and [assignment/REPORT.md](assignment/REPORT.md). The report is complete; the PR steps are in [assignment/README.md](assignment/README.md#c6-prepare-and-submit).
