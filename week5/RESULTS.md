# Practical results — student suffix 6042

The practical experiments ran in the official `ghcr.io/firdaussahran/p4-lab:1.0` image on local Docker Desktop, with two BMv2 switches and three Mininet hosts. All four staged P4 programs compiled, and all **31 recorded checks** passed. Raw outputs are preserved; this document summarises those outputs.

The Codespaces/template-repository setup was replaced by the equivalent local course container for execution. No personal GitHub repository or Codespace was created.

## Observations

| Practical stage | Actual result | Evidence |
|---|---|---|
| Ordinary IPv4 | h1→h2 and h1→h3 each received 3/3 replies; TTL was 62. | [Starter transcript](evidence/practical/step03-starter/session.txt) |
| Runtime table edit | Deleting s2 IPv4 entry handle 2 caused 2/2 packets to be lost. Restoring h3's /32 entry to output port 3 restored 2/2 replies. | [Starter transcript](evidence/practical/step03-starter/session.txt) |
| Tunnel before parser changes | Neither receiver reported the test-1 packet. s1 did not recognise EtherType `0x1212`; ingress dropped the packet. | [s1 log](evidence/practical/step03-starter/logs/s1.txt) |
| Tunnel parsing and emission | h3 received `test 2`, retaining `dst_id=2`, with TTL 62. h2 did not receive it. The compiler still removed the unused tunnel table. | [h3 output](evidence/practical/step04-parser-deparser/logs/h3.txt), [transcript](evidence/practical/step04-parser-deparser/session.txt) |
| Tunnel-table forwarding | h2 received `test 3` with TTL 64, although the IPv4 destination remained `10.42.0.3`. h3 did not receive that packet. Six table entries were installed on each switch; ordinary h1→h3 ping received 2/2 replies at TTL 62. | [h2 output](evidence/practical/step05-tunnel-forwarding/logs/h2.txt), [transcript](evidence/practical/step05-tunnel-forwarding/session.txt) |
| Missing tunnel emission | Neither receiver reported `test 4`. s1 forwarded using destination 2, but s2 parsed `proto_id=0x4500` and destination `0x0022`, then ran `MyIngress.drop`. | [s1 log](evidence/practical/step06-broken-deparser/logs/s1.txt), [s2 log](evidence/practical/step06-broken-deparser/logs/s2.txt) |
| Preserved practical source | `tunnel_v1.p4` matches the successfully compiled/tested Step 5 source, including correct tunnel emission. `tunnel.p4` now contains the later hop-limit assignment. | [Practical baseline](tunnel_v1.p4), [Step 5 source](stages/step05-tunnel-forwarding.p4) |

## Why the results change

Adding parsing makes the tunnel header and encapsulated IPv4 available to ingress. At Step 4, ingress still applies the IPv4 table, so the packet goes to h3 and IPv4 TTL decreases on both switches. The deparser keeps the valid tunnel header in the output.

At Step 5, ingress selects the tunnel table first. Destination identifier 2 sends the packet to h2. The tunnel action only sets the output port, leaving the enclosed IPv4 TTL at 64. Untunnelled ping still uses the IPv4 action and arrives with TTL 62.

At Step 6, s1 consumes the real tunnel header during parsing but fails to reinsert it. Ethernet still advertises the tunnel format, so s2 reads IPv4's first four bytes as a tunnel header. The six-byte payload `test 4` gives IPv4 total length 34, which becomes tunnel destination 34 (`0x0022`). That key misses the table and triggers the default drop action. The compiler accepts this program because its syntax and types are valid; packet correctness still requires testing.

## Test record and troubleshooting

- [Successful automated summary](evidence/practical/summary.json): all checks are true.
- Each stage directory contains the commands, full session, raw switch/receiver logs and Mininet cleanup output.
- The first attempt failed because the Windows checkout gave `p4cli` CRLF endings. After normalising the helper to LF and adding `.gitattributes`, the full rerun passed. The failed-attempt transcript/summary was removed during cleanup and remains available in Git history; all successful evidence is retained.
- Mininet printed a container resource-limit warning. It did not prevent the recorded packet tests from passing.
- Some receiver logs contain a Scapy `Network is down` warning during teardown, after the topology's interfaces are removed. The saved delivery lines precede teardown.
- The temporary containers were removed after execution. Disposable build intermediates and repeated review/export copies were removed during cleanup; successful evidence logs remain in the repository.

## Scope still remaining

The practical code and experiments are complete locally. The four wrap-up questions are answered in [LAB-ANSWERS.md](LAB-ANSWERS.md), included with the practical baseline and evidence in the earlier local commit. Assignment C1–C5 are now complete too; see [assignment/REPORT.md](assignment/REPORT.md). The work is submitted as the unmerged PR "Tunnel hop limit"; see [assignment/README.md](assignment/README.md#c6-prepare-and-submit).
