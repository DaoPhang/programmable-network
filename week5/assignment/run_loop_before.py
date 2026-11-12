#!/usr/bin/env python3
"""Record C1 using the preserved practical in a dedicated course container.

From week5: python3 assignment/run_loop_before.py
Each run uses a fresh build directory; existing evidence is never overwritten.
"""
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "assignment" / "evidence"


def worker():
    topology = runpy.run_path("topo.py", run_name="loop_topology")

    def experiment(net):
        def cli(switch, command):
            print(f"mininet> sh sh ./p4cli {switch} {command}", flush=True)
            result = subprocess.run(
                ["sh", "./p4cli", switch, command],
                capture_output=True, text=True, timeout=15,
            )
            print(result.stdout, end="", flush=True)
            if result.stderr:
                print(result.stderr, end="", flush=True)
            if result.returncode or re.search(r"Error|Invalid|Syntax error", result.stdout + result.stderr):
                raise RuntimeError("Runtime CLI command failed")
            return result.stdout

        cli("s1", "table_dump MyIngress.myTunnel_exact")
        dump = cli("s2", "table_dump MyIngress.myTunnel_exact")
        # BMv2 prints entry handles in hexadecimal, followed by match/action lines.
        entries = re.findall(
            r"Dumping entry (0x[0-9a-fA-F]+|[0-9]+)(.*?)(?=Dumping entry|$)",
            dump, re.S,
        )
        handles = [int(handle, 16 if handle.startswith("0x") else 10)
                   for handle, block in entries
                   if re.search(r"(?:hdr\.)?myTunnel\.dst_id\s*:\s*EXACT\s+0*3\b", block)]
        if len(handles) != 1:
            raise RuntimeError(f"Expected exactly one entry for tunnel destination 3: {handles}")
        handle = handles[0]
        print(f"Identified destination 3 entry handle: {handle}", flush=True)
        cli("s2", f"table_modify MyIngress.myTunnel_exact MyIngress.myTunnel_forward {handle} 1")
        cli("s2", "table_dump MyIngress.myTunnel_exact")
        time.sleep(2)  # Let the original receiver processes attach before transmission.
        command = 'python3 send.py 10.42.0.3 "loop before" --tunnel 3'
        print(f"mininet> h1 {command}", flush=True)
        sent = net["h1"].cmd(command)
        print(sent, end="", flush=True)
        if "Sent from h1-eth0." not in sent:
            raise RuntimeError("Sender did not confirm packet transmission")
        time.sleep(0.5)

        def counts(label):
            print(f"=== {label} ===", flush=True)
            values = {}
            for switch in ("s1", "s2"):
                args = ["grep", "-c", "Processing packet received", f"logs/{switch}.txt"]
                print(f'mininet> sh grep -c "Processing packet received" logs/{switch}.txt', flush=True)
                result = subprocess.run(args, capture_output=True, text=True, timeout=10)
                print(result.stdout, end="", flush=True)
                if result.returncode not in (0, 1):
                    raise RuntimeError(result.stderr)
                values[switch] = int(result.stdout.strip())
            return values

        before = counts("First count after the single send")
        start = time.monotonic()
        print("mininet> sh sleep 5", flush=True)
        time.sleep(5)
        after = counts("Second count after five seconds")
        elapsed = time.monotonic() - start
        for switch in ("s1", "s2"):
            if after[switch] <= before[switch] or before[switch] <= 0:
                raise RuntimeError(f"{switch} counts did not show continued circulation")
        summary = {
            "student_suffix": "6042", "tunnel_destination": 3,
            "s2_entry_handle": handle, "s2_modified_output_port": 1,
            "first_counts": before, "second_counts": after,
            "count_interval_seconds": round(elapsed, 3),
            "both_counts_increased": True,
            "source": "tunnel_v1.p4 (preserved completed practical)",
        }
        Path("counts.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("Counts increased on both switches without another send.", flush=True)
        print("mininet> exit", flush=True)
        # Returning from CLI lets the original topology shut down both switches.

    topology["main"].__globals__["CLI"] = experiment
    sys.argv = ["topo.py", "--id", "6042"]
    topology["main"]()


def main():
    if sys.platform != "linux" or os.geteuid() != 0:
        sys.exit("Run inside the privileged course Linux container as root.")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    transcript = EVIDENCE / "loop-before.txt"
    raw = EVIDENCE / "loop-before-raw"
    if transcript.exists() or raw.exists():
        sys.exit("C1 evidence already exists; preserve it before repeating.")
    if (ROOT / "tunnel_v1.p4").read_bytes() != (ROOT / "stages/step05-tunnel-forwarding.p4").read_bytes():
        sys.exit("The preserved practical baseline has changed.")
    (ROOT / "build").mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="loop-before-", dir=ROOT / "build"))
    for filename in ("topo.py", "send.py", "receive.py", "p4cli", "s1-commands.txt", "s2-commands.txt"):
        source = ROOT / "stages" / filename.replace(".py", "_v1.py") if filename in ("send.py", "receive.py") else ROOT / filename
        shutil.copy2(source, work / filename)
    shutil.copy2(ROOT / "tunnel_v1.p4", work / "tunnel.p4")
    raw.mkdir()
    print(f"Running C1 in fresh directory {work}", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "-u", str(Path(__file__).resolve()), "--worker"],
            cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=90,
        )
        transcript.write_text(result.stdout)
        print(result.stdout, end="", flush=True)
        if result.returncode:
            sys.exit(f"C1 failed; inspect {transcript}")
        shutil.copy2(work / "counts.json", raw / "counts.json")
    except subprocess.TimeoutExpired as exc:
        captured = exc.stdout or b""
        if isinstance(captured, bytes):
            captured = captured.decode(errors="replace")
        transcript.write_text(captured + "\nRUN TIMED OUT\n")
        sys.exit("C1 timed out; partial transcript saved.")
    finally:
        cleanup = subprocess.run(["mn", "-c"], capture_output=True, text=True, timeout=30)
        (raw / "cleanup.txt").write_text(cleanup.stdout + cleanup.stderr)
        if (work / "logs").exists():
            shutil.copytree(work / "logs", raw / "logs")
    print(f"Saved C1 transcript: {transcript}", flush=True)


if __name__ == "__main__":
    if "--worker" in sys.argv:
        worker()
    else:
        main()
