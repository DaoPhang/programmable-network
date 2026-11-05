# Week 5 assignment — Put a limit on the tunnel

Student ID (last 4 digits only): **6042**

Status: baseline preparation and C1 loop analysis only. The hop-limit design, implementation, protected-delivery tests and mixed-version evaluation are not yet completed.

Write each section in your own words, about your own runs. Quote the evidence files in
`assignment/evidence/` that support each point. Delete the instructions in `<!-- -->` as you go.

## 1. Analysis: the loop

### Baseline and experiment setup

The completed practical was preserved as `../tunnel_v1.p4` on branch `hop-limit`, in baseline commit `b5fc667`. It is identical to the tested practical program and contains no hop-limit field or exhaustion check. Both switches ran that baseline in the official course container using student suffix `6042`.

The automated experiment used a fresh working directory to avoid counting earlier logs. It compiled the preserved program as `tunnel.p4` and started the original topology with `--id 6042`. The runner invokes the topology's normal CLI callback with a scripted experiment and records the equivalent Mininet commands and actual outputs in [loop-before.txt](evidence/loop-before.txt).

### Creating the loop

I inspected `MyIngress.myTunnel_exact` on both switches. On s1, tunnel destination 3 already selected port 2, towards s2. On s2, destination 3 initially selected port 3, towards h3. The s2 table dump identified its handle as `0x2` (decimal 2).

The runtime modification was:

```text
sh sh ./p4cli s2 table_modify MyIngress.myTunnel_exact MyIngress.myTunnel_forward 2 1
```

The following dump confirmed that s2 now sent destination 3 out port 1, back towards s1. This created the cycle s1 → s2 → s1. I then sent exactly one test packet from h1:

```text
h1 python3 send.py 10.42.0.3 "loop before" --tunnel 3
```

### Observed counts

The runner counted `Processing packet received` records in each switch log, waited five seconds and repeated the counts without sending another packet.

| Switch | First count | Second count | Increase |
|---|---:|---:|---:|
| s1 | 18 | 192 | 174 |
| s2 | 17 | 192 | 175 |

The measured interval covering the wait and second reads was approximately **5.018 seconds**. These are switch packet-processing visits, not separately generated host packets or complete round trips. The counters are read sequentially while the packet is moving, so small differences between switches are expected.

Both counters continued increasing, demonstrating repeated circulation of the single injected packet. Tunnel ingress selects `myTunnel_exact`; its `myTunnel_forward` action only sets the output port. It does not reduce the enclosed IPv4 TTL or impose another visit limit. The result therefore shows continued looping during the observation window; the code explains why there is no automatic hop-based stopping condition.

After the second measurement, the experiment returned from the topology's CLI callback, allowing the normal `net.stop()` sequence to remove links and stop both switches. Mininet cleanup followed. The transcript records the shutdown, and the temporary Docker container was removed. The loop is no longer running.

### Does IPv4 TTL decrement stop an IPv4 loop in this program?

**No.** This conclusion comes from inspecting the supplied program; a separate ordinary-IPv4 loop was not run for C1. `ipv4_forward` sets the output port and executes:

```p4
hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
```

The field is an unsigned `bit<8>`. There is no ingress or action condition that drops a packet when TTL is 0 or 1. Consequently, a packet with incoming TTL 1 is forwarded with TTL 0. If it returns to another switch, subtracting one from 0 wraps to 255 in the eight-bit field, and forwarding can continue. IPv4 checksum recomputation does not supply an exhaustion check.

Thus this implementation's decrement alone is insufficient to stop an IPv4 forwarding loop. Correct TTL enforcement would require an explicit discard rule before an expired packet is forwarded. For tunnel traffic, the problem is even more direct: the tunnel path does not call `ipv4_forward`, so its enclosed TTL is not decremented at all.

### Supporting files

- [loop-before.txt](evidence/loop-before.txt): commands, runtime table dumps, packet fields, two count measurements and topology shutdown.
- [counts.json](evidence/loop-before-raw/counts.json): structured count values and measured interval.
- [s1 log](evidence/loop-before-raw/logs/s1.txt) and [s2 log](evidence/loop-before-raw/logs/s2.txt): raw switch records.
- [C1 walkthrough](C1-README.md): preparation, reproduction and scope.

The first attempt stopped before sending a packet because the runner expected `hdr.myTunnel.dst_id`, while the runtime CLI displays `myTunnel.dst_id`. The parser was corrected to accept either spelling. That failed attempt is preserved in `evidence/loop-before-attempt01-parser/`; the counts above come exclusively from the successful fresh run.

## 2. Design: the hop limit

<!-- Your header change and your pipeline change, and the reason for each choice:
     - the field's size, and where in the header you put it (and why there);
     - the starting value send.py uses, and how you chose it;
     - where it's decremented, and what happens when it runs out;
     - what else had to change for every part of the path to agree (parser, deparser, hosts). -->

## 3. Implementation

<!-- Summarise what you changed in tunnel.p4, send.py and receive.py. The pull request shows
     the code itself: here, explain anything a reviewer might not see from the diff alone. -->

## 4. Evidence: it works

<!-- Show, with your evidence files:
     - tunnelled delivery to h2 and h3, and the hop limit the receivers saw (delivery.txt);
     - plain IPv4 still works (delivery.txt);
     - the same loop as in section 1 now ends, and after how many passes — does that match
       your design? (loop-after.txt) -->

## 5. Evaluation

<!-- a) The mixed rollout (mixed.txt): what did you predict before running s1 with your new
        program and s2 with tunnel_v1.p4? What actually happened to delivery, and to the loop?
        Explain every difference from your prediction, byte by byte if you need to.
     b) Propose a safe way to roll out a header change across a network of switches that can't
        all be upgraded at once. Compare at least two options (for example a version field, a
        new EtherType, or ordering fields so old switches still parse them).
     c) Loop protection in the data plane (this hop limit) versus the control plane (Week 3's
        check_paths()): what can each catch that the other can't? Why do real networks use both?
     d) What would this change cost on a hardware switch running at line rate? -->

## AI use

An AI coding assistant in the Claude Code CLI helped preserve the completed practical program, create the assignment branch and baseline commit, automate the isolated C1 experiment, inspect runtime table dumps and switch logs, and draft the loop and IPv4 TTL analysis. The first attempt exposed a mismatch between CLI field names and the runner's parser; the runner was corrected and that attempt was preserved separately. Report observations are drawn from the saved experiment outputs. The student must review and understand the code, evidence and explanation. This declaration should be updated as later assignment sections are completed.

## Evidence files

| File | What it shows |
|---|---|
| `evidence/loop-before.txt` | The loop with your finished lab program: pass counts growing |
| `evidence/delivery.txt` | Tunnelled delivery with the hop limit, and a plain ping |
| `evidence/loop-after.txt` | The same loop with your hop limit: pass counts that stop |
| `evidence/mixed.txt` | The mixed rollout: s1 new, s2 old |
