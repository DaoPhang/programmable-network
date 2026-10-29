# Lab 4 — Control Plane Separation and OpenFlow

Student ID suffix: **6042**  
Date: **30 October 2026**

[Course lab instructions](https://firdaussahran.github.io/wic2005/weeks/week-04/#tab-lab)

## Setup

The lab used `firdaussahran/netlab-mininet:1.0`, with one Open vSwitch switch and three hosts.

| Host | IPv4 address | MAC address | s1 port |
|---|---|---|---|
| h1 | 10.42.0.1/24 | 00:00:00:00:00:01 | 1 |
| h2 | 10.42.0.2/24 | 00:00:00:00:00:02 | 2 |
| h3 | 10.42.0.3/24 | 00:00:00:00:00:03 | 3 |

Run inside the container shell:

```bash
mn --topo single,3 --mac --switch ovs,datapath=user --controller none --ipbase 10.42.0.0/24
```

## Observed results

| Step | Actual result | Evidence |
|---|---|---|
| 0 — Empty switch | Empty flow table; h1 to h2 lost 2/2 packets with Destination Host Unreachable. | session.log |
| 1 — Hub | FLOOD rule; pingall received 6/6. h3 captured six ICMP packets between h1 and h2. | session.log |
| 2 — Manual forwarding | ARP flood rule and three destination-MAC forwarding rules; pingall received 6/6. h1 to h2 succeeded while h3 captured zero ICMP packets. | session.log |
| 3 — Firewall | Default-priority drop rule counted zero packets and ping succeeded. Priority 40000 blocked h1 to h3 and h3 to h1, while h1 to h2 succeeded. Drop counter reached six packets. | session.log |
| 4 — Controller | Controller connected in secure mode. Both tested conversations succeeded. Table contained reactive flows with idle_timeout=60 and a priority-0 CONTROLLER:128 rule. | session.log |
| 5 — Controller failure | Following recovery, existing h1 to h2 still worked after controller shutdown. New h1 to h3 failed. After 65 seconds idle, h1 to h2 failed and only the controller rule remained. | Saved log contains disconnection and surviving h1–h2 traffic; final new-conversation and expiration results were pasted in the conversation. |
| 6 — Standalone | After selecting standalone mode and waiting 15 seconds, h1 to h3 received 2/2 packets. Switch showed fail_mode: standalone and an empty OpenFlow dump. | Terminal output pasted in the conversation only. |

## Evidence status and troubleshooting

The [original session log](evidence/session.log) has been preserved unchanged. An independent subagent review confirmed that Steps 0–4 are recorded, Step 5 is partial, and Step 6 is absent. The file reviewed was 20,865 bytes and ended mid-error after a successful post-controller h1–h2 ping. It does not contain the final new-conversation failure, successful expiration test, standalone fallback, or recording closure.

All practical steps were demonstrated in the combined saved log and terminal outputs shared in the conversation. The saved log alone is incomplete; the later results above are explicitly attributed to conversation outputs and have not been reconstructed as raw log evidence.

- Initial commands were entered at the container shell before Mininet was started; the subsequent run used the correct prompt.
- The first four-second hub capture saw no packets. A retry with a 15-second capture and one-second startup delay captured all six ICMP packets.
- A zero ARP counter after installing manual rules is consistent with hosts retaining neighbour-cache entries.
- An extra pingall created h1–h3 flows, so the failure test needed a reset before using h1–h3 as a new conversation.
- The first reset deleted the controller table-miss rule, causing the baseline ping to fail even before shutdown. Removing the controller configuration, clearing flows, restarting the controller, and reconnecting it restored that rule. A successful baseline ping was verified before repeating the experiment.
- Command-entry errors were followed by successful retries. Signal 15 after intentionally stopping the controller was expected.
- Flow duration measures total age; idle_timeout measures inactivity. Matching traffic refreshes the idle timer, so a flow can remain installed for more than 60 seconds in total.
- Standalone fallback restored learning-switch forwarding despite an empty OpenFlow dump.

## Wrap-up answers

### 1. Why did the first firewall rule have no effect, and why does blocking h1 to h3 also break h3 to h1?

The first ICMP drop rule overlapped with the destination-MAC forwarding rule at the same default priority, 32768. OpenFlow does not guarantee which equal-priority overlapping rule wins. In this run the forwarding rule was used: all three pings succeeded and the drop counter remained zero. Giving the drop rule priority 40000 made it take precedence.

When h3 pings h1, the echo request travels from h3 to h1, but its reply travels from h1 to h3 and matches the drop rule. Therefore the reverse ping also fails. The rule blocks ICMP in the h1-to-h3 direction, rather than every protocol between the hosts. The six drops correspond to three h1-to-h3 requests and three replies to h3's ping.

### 2. Why did one conversation survive controller failure while another did not?

The controller had already installed forwarding flows for h1–h2. The switch continued using those flows locally after the controller disconnected. The new h1–h3 conversation had no matching forwarding flows and needed the controller to process table-miss packets and install rules. With the controller offline, that conversation failed.

After 65 seconds without traffic, the h1–h2 flows with idle_timeout=60 expired and its ping failed too. Only the priority-0 controller rule remained, which could not restore connectivity without a running controller.

### 3. Secure or standalone: which would you choose for a campus network, and what does the other one cost?

I would choose secure mode for campus switches enforcing centrally managed security policies. It prevents fallback learning-switch forwarding that might bypass those policies during controller failure. Existing flows can continue, but new conversations and conversations whose flows expire may fail. Controller redundancy is therefore important for availability.

Standalone mode favours connectivity: h1–h3 communication returned when the switch fell back to ordinary learning behaviour. Its cost is that fallback forwarding may bypass the controller's intended firewall or access policies. For security-sensitive campus segments, I would prioritise policy enforcement and use secure mode.


