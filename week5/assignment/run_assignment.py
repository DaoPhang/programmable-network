#!/usr/bin/env python3
"""Record C4/C5 in fresh workspaces inside the dedicated course container.

From week05: python3 assignment/run_assignment.py
Existing evidence is never overwritten. No Git operations are performed.
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
EVIDENCE = ROOT / "assignment/evidence"


def worker(mode):
    topology = runpy.run_path("topo.py", run_name="assignment_topology")
    checks = {}
    measurements = {}

    def experiment(net):
        def host(name, command):
            print(f"mininet> {name} {command}", flush=True)
            text = net[name].cmd(command)
            print(text, end="", flush=True)
            return text

        def cli(switch, command):
            print(f"mininet> sh sh ./p4cli {switch} {command}", flush=True)
            result = subprocess.run(["sh", "./p4cli", switch, command], capture_output=True, text=True, timeout=15)
            print(result.stdout + result.stderr, end="", flush=True)
            if result.returncode or re.search(r"Error|Invalid|Syntax error", result.stdout + result.stderr):
                raise RuntimeError("Runtime table command failed")
            return result.stdout

        def count():
            counts = {}
            for switch in ("s1", "s2"):
                print(f'mininet> sh grep -c "Processing packet received" logs/{switch}.txt', flush=True)
                result = subprocess.run(["grep", "-c", "Processing packet received", f"logs/{switch}.txt"], capture_output=True, text=True)
                if result.returncode not in (0, 1):
                    raise RuntimeError(result.stderr)
                counts[switch] = int(result.stdout.strip())
                print(result.stdout, end="", flush=True)
            return counts

        def read_hosts():
            result = {}
            for name in ("h2", "h3"):
                text = Path(f"logs/{name}.txt").read_text()
                print(f"mininet> sh cat logs/{name}.txt\n{text}", flush=True)
                result[name] = text
            return result

        def configure_loop():
            dump = cli("s2", "table_dump MyIngress.myTunnel_exact")
            entries = re.findall(r"Dumping entry (0x[0-9a-fA-F]+|[0-9]+)(.*?)(?=Dumping entry|$)", dump, re.S)
            handles = [int(handle, 16 if handle.startswith("0x") else 10) for handle, block in entries
                       if re.search(r"(?:hdr\.)?myTunnel\.dst_id\s*:\s*EXACT\s+0*3\b", block)]
            if len(handles) != 1:
                raise RuntimeError("Cannot identify destination 3 entry")
            cli("s2", f"table_modify MyIngress.myTunnel_exact MyIngress.myTunnel_forward {handles[0]} 1")
            cli("s2", "table_dump MyIngress.myTunnel_exact")

        def loop_case(hops, mixed=False):
            before = count()
            host("h1", f'python3 send.py 10.42.0.3 "loop hops {hops}" --tunnel 3 --hops {hops}')
            time.sleep(1)
            first = count()
            print("mininet> sh sleep 5", flush=True)
            time.sleep(5)
            second = count()
            delta = {s: second[s] - before[s] for s in before}
            if mixed:
                expected = {"s1": max(1, hops), "s2": max(0, hops - 1)}
            else:
                visits = max(1, hops)
                expected = {"s1": (visits + 1) // 2, "s2": visits // 2}
            checks[f"hops_{hops}_exact_visits"] = delta == expected
            checks[f"hops_{hops}_counts_stable"] = first == second
            measurements[f"hops_{hops}"] = {"before": before, "first": first, "after_five_seconds": second,
                                                "visits": delta, "expected": expected}

        time.sleep(2)
        if mode == "delivery":
            # Omitted --hops exercises the sender's default; explicit values cover boundaries.
            host("h1", 'python3 send.py 10.42.0.2 "delivery h2 default" --tunnel 2')
            host("h1", 'python3 send.py 10.42.0.3 "delivery h3 eight" --tunnel 3 --hops 8')
            for hops in (0, 1, 2, 3, 255):
                host("h1", f'python3 send.py 10.42.0.3 "boundary {hops}" --tunnel 3 --hops {hops}')
            host("h1", 'python3 send.py 10.42.0.3 "plain IPv4 delivery"')
            ping = host("h1", "ping -c 2 10.42.0.3")
            time.sleep(1)
            logs = read_hosts()
            checks["h2_default_arrives_with_6"] = "dst_id=2, hops=6" in logs["h2"] and "delivery h2 default" in logs["h2"]
            checks["h3_eight_arrives_with_6"] = "dst_id=3, hops=6" in logs["h3"] and "delivery h3 eight" in logs["h3"]
            checks["exhausted_values_not_delivered"] = all(f"'boundary {n}'" not in logs["h3"] for n in (0, 1, 2))
            checks["three_arrives_with_1"] = "hops=1" in logs["h3"] and "'boundary 3'" in logs["h3"]
            checks["max_arrives_with_253"] = "hops=253" in logs["h3"] and "'boundary 255'" in logs["h3"]
            checks["plain_udp_works"] = "Received (plain IPv4)" in logs["h3"] and "plain IPv4 delivery" in logs["h3"]
            checks["plain_ping_works"] = "2 packets transmitted, 2 received" in ping and "ttl=62" in ping
            for suffix in ("--tunnel 3 --hops -1", "--tunnel 3 --hops 256", "--hops 8"):
                text = host("h1", f'python3 send.py 10.42.0.3 invalid {suffix}; printf "EXIT=%s\\n" "$?"')
                checks[f"reject_{suffix}"] = "EXIT=2" in text and "error:" in text
        elif mode == "loop-after":
            configure_loop()
            loop_case(8)
            # Exhaustion and odd-budget boundaries are checked in the actual data plane too.
            for hops in (0, 1, 2, 3):
                loop_case(hops)
            read_hosts()
        elif mode == "mixed":
            prediction = (ROOT / "assignment/MIXED-PREDICTION.md").read_text()
            print("=== Prediction recorded before this run ===\n" + prediction, flush=True)
            host("h2", "timeout 8 tcpdump -ni h2-eth0 -c 1 -XX 'ether proto 0x1212' > logs/h2cap.txt 2>&1 &")
            host("h2", "timeout 8 tcpdump -ni h2-eth0 -c 1 -w logs/mixed.pcap 'ether proto 0x1212' > logs/pcap-status.txt 2>&1 &")
            time.sleep(1)
            host("h1", 'python3 send.py 10.42.0.3 "mixed delivery" --tunnel 2 --hops 8')
            print("mininet> sh sleep 8", flush=True)
            time.sleep(8)
            cap = Path("logs/h2cap.txt").read_text()
            print("mininet> sh cat logs/h2cap.txt\n" + cap, flush=True)
            from scapy.all import rdpcap
            from scapy.utils import checksum
            frames = rdpcap("logs/mixed.pcap")
            if len(frames) != 1:
                raise RuntimeError("Expected one captured mixed-version frame")
            packet = bytes(frames[0])
            ip = packet[19:39]  # Ethernet 14 + new MyTunnel 5.
            decoded = {"frame_hex": packet.hex(), "proto_id": int.from_bytes(packet[14:16], "big"),
                       "dst_id": int.from_bytes(packet[16:18], "big"), "hops": packet[18],
                       "ipv4_version": ip[0] >> 4, "ipv4_protocol": ip[9],
                       "ipv4_checksum": ip[10:12].hex(), "ipv4_checksum_valid": checksum(ip) == 0}
            print("Captured packet decoded at NEW header offsets:\n" + json.dumps(decoded, indent=2), flush=True)
            measurements["mixed_delivery"] = decoded
            logs = read_hosts()
            checks["mixed_frame_reaches_h2_with_7"] = decoded["hops"] == 7 and decoded["dst_id"] == 2
            checks["mixed_ipv4_protocol_corrupted"] = decoded["ipv4_protocol"] != 17
            checks["mixed_ipv4_checksum_invalid"] = not decoded["ipv4_checksum_valid"]
            checks["mixed_udp_not_received"] = "mixed delivery" not in logs["h2"]
            configure_loop()
            loop_case(8, mixed=True)
        else:
            raise ValueError(mode)
        print("=== Assertions ===\n" + json.dumps(checks, indent=2), flush=True)
        Path("checks.json").write_text(json.dumps({"checks": checks, "measurements": measurements}, indent=2) + "\n")
        if not all(checks.values()):
            raise RuntimeError("One or more packet experiment assertions failed")
        print("mininet> exit", flush=True)

    topology["main"].__globals__["CLI"] = experiment
    sys.argv = ["topo.py", "--id", "6042"]
    if mode == "mixed":
        sys.argv += ["--s2-program", "tunnel_v1.p4"]
    topology["main"]()


def main():
    if sys.platform != "linux" or os.geteuid() != 0:
        sys.exit("Run in the dedicated privileged course container as root.")
    (ROOT / "build").mkdir(exist_ok=True)
    for mode in ("delivery", "loop-after", "mixed"):
        transcript = EVIDENCE / f"{mode}.txt"
        raw = EVIDENCE / f"{mode}-raw"
        if transcript.exists() or raw.exists():
            sys.exit(f"Preserve existing {mode} evidence before running again.")
        work = Path(tempfile.mkdtemp(prefix=f"{mode}-", dir=ROOT / "build"))
        for name in ("topo.py", "tunnel.p4", "tunnel_v1.p4", "send.py", "receive.py", "p4cli", "s1-commands.txt", "s2-commands.txt"):
            shutil.copy2(ROOT / name, work / name)
        raw.mkdir(parents=True)
        print(f"Running {mode} in {work}", flush=True)
        try:
            result = subprocess.run([sys.executable, "-u", str(Path(__file__).resolve()), "--worker", mode],
                                    cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=150)
            transcript.write_text(result.stdout)
            print(result.stdout, end="", flush=True)
            if (work / "checks.json").exists():
                shutil.copy2(work / "checks.json", raw / "checks.json")
            if result.returncode:
                sys.exit(f"{mode} failed; inspect saved transcript")
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or b""
            if isinstance(captured, bytes):
                captured = captured.decode(errors="replace")
            transcript.write_text(captured + "\nTIMED OUT\n")
            raise
        finally:
            cleanup = subprocess.run(["mn", "-c"], capture_output=True, text=True, timeout=30)
            (raw / "cleanup.txt").write_text(cleanup.stdout + cleanup.stderr)
            if (work / "logs").exists():
                shutil.copytree(work / "logs", raw / "logs")
    print("C4 and C5 experiments all passed.", flush=True)


if __name__ == "__main__":
    if "--worker" in sys.argv:
        worker(sys.argv[-1])
    else:
        main()
