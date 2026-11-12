#!/usr/bin/env python3
"""Run practical Steps 2–6 in the supplied privileged P4 lab container.

Saves genuine transcripts and switch/host logs under evidence/practical/.
Each stage has its own working directory; the final tunnel.p4 is never replaced.
Run from week5: python3 run_practical.py
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence" / "practical"
FILES = ("topo.py", "send.py", "receive.py", "p4cli", "s1-commands.txt", "s2-commands.txt")


def send(number):
    return f'h1 python3 send.py 10.42.0.3 "test {number}" --tunnel 2'


READ_HOSTS = ["sh sleep 2", "sh cat logs/h2.txt logs/h3.txt"]
STAGES = [
    ("step03-starter", [
        "h1 ping -c 3 10.42.0.2",
        "h1 ping -c 3 10.42.0.3",
        "sh sh ./p4cli s2 table_dump MyIngress.ipv4_lpm",
        "sh sh ./p4cli s2 table_delete MyIngress.ipv4_lpm 2",
        "h1 ping -c 2 -W 1 10.42.0.3",
        'sh sh ./p4cli s2 "table_add MyIngress.ipv4_lpm MyIngress.ipv4_forward 10.42.0.3/32 => 3"',
        "h1 ping -c 2 10.42.0.3",
        send(1), *READ_HOSTS,
    ]),
    ("step04-parser-deparser", [send(2), *READ_HOSTS]),
    ("step05-tunnel-forwarding", [send(3), *READ_HOSTS, "h1 ping -c 2 10.42.0.3"]),
    ("step06-broken-deparser", [send(4), *READ_HOSTS]),
]


def validate(label, transcript, logs):
    h2 = logs.get("h2.txt", "")
    h3 = logs.get("h3.txt", "")
    if label == "step03-starter":
        return {
            "ipv4_initial_pings": transcript.count("3 packets transmitted, 3 received") == 2,
            "deleted_entry_blocks_h3": "2 packets transmitted, 0 received" in transcript,
            "restored_entry_delivers_h3": "2 packets transmitted, 2 received" in transcript,
            "starter_tunnel_not_received": "Received (" not in h2 + h3,
            "ttl_62": "ttl=62" in transcript,
        }
    if label == "step04-parser-deparser":
        return {
            "ipv4_destination_h3_receives": "TTL 62: 'test 2'" in h3,
            "tunnel_header_retained": "tunnelled, dst_id=2" in h3,
            "h2_does_not_receive": "Received (" not in h2,
        }
    if label == "step05-tunnel-forwarding":
        return {
            "tunnel_destination_h2_receives": "TTL 64: 'test 3'" in h2,
            "h3_does_not_receive_tunnel": "Received (" not in h3,
            "ipv4_still_works": "2 packets transmitted, 2 received" in transcript,
            "six_entries_each_switch": transcript.count("6 table entries added") == 2,
        }
    s2 = logs.get("s2.txt", "").lower()
    return {
        "broken_packet_not_received": "Received (" not in h2 + h3,
        "s2_misreads_ipv4_proto": "4500" in s2,
        "s2_misreads_length_as_destination": "0022" in s2 or "0x22" in s2,
    }


def main():
    if sys.platform != "linux" or os.geteuid() != 0:
        sys.exit("Run this inside the privileged Linux P4 lab container as root.")
    for tool in ("p4c-bm2-ss", "simple_switch", "simple_switch_CLI", "mn"):
        if not shutil.which(tool):
            sys.exit(f"Missing course environment tool: {tool}")
    if EVIDENCE.exists() and any(EVIDENCE.iterdir()):
        sys.exit("Evidence already exists. Preserve it or move it before running again.")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = {}
    for label, commands in STAGES:
        print(f"Running {label}...", flush=True)
        work = ROOT / "build" / "practical" / label
        work.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            source = ROOT / "stages" / filename.replace(".py", "_v1.py") if filename in ("send.py", "receive.py") else ROOT / filename
            shutil.copy2(source, work / filename)
        shutil.copy2(ROOT / "stages" / f"{label}.p4", work / "tunnel.p4")
        out = EVIDENCE / label
        out.mkdir()
        # Allow the Scapy receivers to attach before the first packet is sent.
        script = "\n".join(["sh sleep 2", *commands, "exit", ""])
        (out / "commands.txt").write_text(script)
        try:
            result = subprocess.run(
                [sys.executable, "-u", "topo.py", "--id", "6042"],
                input=script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=work, timeout=150,
            )
            transcript = result.stdout
            (out / "session.txt").write_text(transcript)
            logs = {}
            if (work / "logs").exists():
                shutil.copytree(work / "logs", out / "logs")
                logs = {p.name: p.read_text(errors="replace") for p in (work / "logs").glob("*.txt")}
            checks = validate(label, transcript, logs)
            checks["process_exited_successfully"] = result.returncode == 0
            checks["both_switch_logs_saved"] = all(logs.get(name) for name in ("s1.txt", "s2.txt"))
            checks["both_receivers_started"] = all("Listening on" in logs.get(name, "") for name in ("h2.txt", "h3.txt"))
            # Docker may emit a Mininet resource-limit warning even when forwarding works.
            checks["no_runtime_cli_errors"] = not any(
                ("Error" in line or "Invalid" in line or "Syntax error" in line)
                and not line.startswith("*** Error setting resource limits.")
                for line in transcript.splitlines()
            )
            summary[label] = checks
            print(json.dumps(checks, indent=2), flush=True)
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or b""
            if isinstance(captured, bytes):
                captured = captured.decode(errors="replace")
            (out / "session.txt").write_text(captured + "\nRUN TIMED OUT\n")
            summary[label] = {"completed_without_timeout": False}
        finally:
            # This runner is intended for a dedicated lab container.
            cleanup = subprocess.run(["mn", "-c"], capture_output=True, text=True)
            (out / "cleanup.txt").write_text(cleanup.stdout + cleanup.stderr)
            (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        if not all(summary[label].values()):
            sys.exit(f"A check failed at {label}; inspect {out} before continuing.")
    print("All four practical stages passed. Final tunnel.p4 retains tunnel emission.")


if __name__ == "__main__":
    main()
