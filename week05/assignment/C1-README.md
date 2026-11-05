# Assignment preparation and C1 — completed

Student suffix: **6042**. Branch: **`hop-limit`**.

## Completed tasks 1–3

1. Preserved the finished practical as `../tunnel_v1.p4`, byte-for-byte identical to `../tunnel.p4` and the tested Step 5 program.
2. Created `hop-limit` from `week05-practical` and committed the baseline as **`b5fc667`**, `Preserve completed tunnel lab before hop-limit changes`.
3. Ran the before-protection tunnel-loop experiment and saved the actual outputs to [evidence/loop-before.txt](evidence/loop-before.txt). The loop was stopped by topology shutdown.

| Switch | First count | After five-second wait | Increase |
|---|---:|---:|---:|
| s1 | 18 | 192 | 174 |
| s2 | 17 | 192 | 175 |

Counts represent packet-processing visits. Only one packet was injected. The measured interval including the second reads was 5.018 seconds. Read [REPORT.md](REPORT.md) section 1 for the loop explanation and the separate code-based IPv4 TTL analysis.

The working program and host tools are still unchanged practical versions. No hop-limit design or implementation has been added yet.

## What the experiment did

- Compiled and ran the preserved baseline using the original two-switch topology and `--id 6042`.
- Used a new working directory under ignored `../build/`, so previous logs did not affect the counts.
- Dumped both tunnel tables, identified s2's destination-3 handle as 2 and modified its output to port 1.
- Verified that modification with a second s2 dump.
- Sent one packet from h1 to `10.42.0.3` with `--tunnel 3` and payload `loop before`.
- Counted packet receptions, waited five seconds, counted again and verified both increases.
- Let the original topology stop its switches/links, ran Mininet cleanup, and removed the temporary container.

The runner drives the topology through a scripted CLI callback. Transcript lines beginning `mininet>` display the equivalent commands; they were executed automatically rather than typed interactively.

## Evidence files

- [loop-before.txt](evidence/loop-before.txt): the successful run's transcript.
- [loop-before-raw/counts.json](evidence/loop-before-raw/counts.json): count values and timing.
- `evidence/loop-before-raw/logs/`: actual host/switch outputs.
- [loop-before-raw/cleanup.txt](evidence/loop-before-raw/cleanup.txt): Mininet cleanup output.
- `evidence/loop-before-attempt01-parser/`: preserved initial attempt, which stopped before packet transmission because the runtime CLI omits the `hdr.` prefix from its displayed match-field names. The runner was corrected before the successful run.

## Repeat the experiment

From PowerShell at the coursework repository root:

```powershell
Set-Location .\week05
$week05Path = (Get-Location).Path
docker run --rm --privileged --mount "type=bind,source=$week05Path,target=/lab" -w /lab ghcr.io/firdaussahran/p4-lab:1.0 python3 assignment/run_loop_before.py
```

The runner refuses to overwrite existing `assignment/evidence/loop-before.txt` or `loop-before-raw/`. Preserve those under separately named backups before repeating. It also verifies that `tunnel.p4` still matches `tunnel_v1.p4`; this runner is specifically for the pre-change experiment.

Run it only in a dedicated lab container: it uses `mn -c` for cleanup. The original completed practical source is not edited, and runtime forwarding changes exist only within that experiment's switches.

## Next task

C2 is to specify the hop-limit design in REPORT.md before changing P4 or host packet formats. Later sections and the other three required evidence files remain unfinished. No push, PR or Spectrum submission has been performed.
