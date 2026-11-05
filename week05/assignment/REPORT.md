# Week 5 assignment — Put a limit on the tunnel

Student ID (last 4 digits only): **6042**

Status: C1–C5 are complete and experimentally verified. The source, report and evidence were published in the combined coursework repository as commit `e2e5040` (`Week05`). C6 still requires the separate P4 assignment PR, a green GitHub compilation check, lecturer access and Spectrum submission. Experiments used the official course image on local Docker rather than Codespaces.

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
- [Assignment README](README.md): complete C1–C6 overview, evidence and reproduction instructions.

The first attempt stopped before sending a packet because the runner expected `hdr.myTunnel.dst_id`, while the runtime CLI displays `myTunnel.dst_id`. The parser was corrected to accept either spelling. The failed attempt was removed from the current folder during cleanup and remains available in Git history; the counts above come exclusively from the retained successful fresh run.

## 2. Design: the hop limit

### Design recorded before implementation and experiments

Use an unsigned **8-bit `hops` field appended after `dst_id`**. The wire header becomes `proto_id:16 | dst_id:16 | hops:8`, in network byte order, for a total of five bytes. One byte supports values 0–255, avoids sub-byte host packing and adds only one byte per tunnel packet. Appending keeps the original four-byte prefix intact, but does **not** make old switches compatible: their IPv4 parser still starts one byte too early. The mixed-version evaluation must test that explicitly.

`send.py` will default to **8** and accept `--hops` in **0–255**. Eight comfortably exceeds the two-switch normal path while keeping a mistaken loop short. A value of zero is accepted for exhaustion testing. The sender will reject out-of-range limits and an explicit `--hops` without `--tunnel`.

In ingress, only when `hdr.myTunnel.isValid()`, test the limit **before applying the tunnel table**:

1. If incoming `hops <= 1`, mark the packet to drop and do not apply the forwarding table or subtract.
2. Otherwise subtract exactly one, then apply `myTunnel_exact`.
3. A table miss still uses the existing default drop action. Ordinary IPv4 processing remains unchanged.

This uses a TTL-style rule: an incoming value of 1 means the current switch is the final permitted processing visit and discards the packet. No exhausted value is subtracted, so 0 cannot wrap to 255. A header value is not a promise that forwarding will succeed; table misses can discard it sooner.

For an all-upgraded loop, a positive initial value **N permits at most N switch ingress visits**, of which at most **N−1 forward** and the Nth drops. For N=0, the first switch drops immediately. For N=8, the two-switch delivery path leaves 6 at the receiver; the loop has eight visits, seven forwards and a drop at s2 (four visits at each switch). For N=2, s1 forwards with 1 and s2 drops. Successful traversal of K switches therefore requires N > K.

Both Python packet definitions must use the same appended byte as P4, the sender must initialise it, and the receiver must print it. Extracting and emitting the existing header automatically includes the added field. The preserved `tunnel_v1.p4` must remain unchanged. No new match key or table entry is needed.

These bounds assume every visited switch understands and enforces the limit. With new s1 and old s2, only s1 spends the budget: for N=8 the predicted loop bound is eight s1 visits plus seven s2 visits, **15 total**, with discard at s1. A cycle consisting entirely of old switches would remain unprotected.

## 3. Implementation

- **`tunnel.p4`:** append `bit<8> hops` to `myTunnel_t`. The tunnel branch of ingress drops incoming values at or below 1; otherwise it subtracts one before `myTunnel_exact.apply()`. The guard prevents unsigned underflow and applies even if the packet will subsequently miss the table. The existing parser extraction and deparser emission now handle the full five-byte header. No forwarding-table key, entry or host address changes.
- **`send.py`:** append Scapy `ByteField("hops", 8)` after the two 16-bit fields. Add configurable `--hops`; omission uses 8. Reject limits outside 0–255 and explicit limits without `--tunnel`, before interface selection or transmission. Validate the 16-bit tunnel destination range as well.
- **`receive.py`:** use the identical five-byte definition and display `dst_id` and remaining `hops` for received lab UDP packets. Put sniffing behind a `main()` guard so importing the packet definition does not start a live receiver.
- **Preserved baseline:** `tunnel_v1.p4` remains identical to the completed practical. The original sender/receiver are retained as `stages/send_v1.py` and `stages/receive_v1.py`, and earlier experiment runners use them to avoid mixing old P4 with the new host format.
- **Experiment automation:** `assignment/run_assignment.py` creates separate fresh working directories for delivery, protected looping and mixed deployment. It uses the original topology, drives its CLI callback with equivalent recorded commands, asserts the actual observations, preserves raw logs and cleans up the network. `MIXED-PREDICTION.md` was written before implementation and before those tests.

Ordinary IPv4 retains the practical's behaviour, including its missing TTL expiration check discussed in section 1. This assignment's protection applies to the tunnel path; it does not claim to fix ordinary IPv4 looping.

## 4. Evidence: it works

### Tunnel and ordinary IPv4 delivery

[delivery.txt](evidence/delivery.txt) records successful compilation and the actual sender/receiver outputs. The default sender value of 8 delivered to h2 (identifier 2), and explicit `--hops 8` delivered to h3 (identifier 3). Each receiver printed **hops=6** and enclosed IPv4 **TTL 64**, as expected after two tunnel forwards. Plain UDP also reached h3, and `h1 ping -c 2 10.42.0.3` received **2/2 replies, TTL 62**.

Boundary delivery tests sent limits 0, 1, 2, 3 and 255. Values 0 and 1 dropped at s1; 2 reached s2 and dropped there. Their messages did not appear in the receiver log. Value 3 arrived with 1 remaining; 255 arrived with 253. Invalid CLI values −1 and 256, and `--hops` without a tunnel, exited with argument-error status 2 before transmission. All ten delivery/argument assertions passed; see [delivery checks](evidence/delivery-raw/checks.json).

### The same loop after protection

In a fresh topology I again changed s2's tunnel destination 3 to port 1. [loop-after.txt](evidence/loop-after.txt) records a single `--hops 8` packet. The first counts were **s1=4, s2=4** and remained **4,4** after a further five-second wait, compared with the growing C1 counts. This is **eight visits total**, including seven forwards and the final drop at s2. The stable counters show termination before topology shutdown.

The same isolated loop then tested exhaustion and odd-budget boundaries, taking a baseline count before each packet:

| Initial limit | New s1 visits | New s2 visits | Total visits | Result |
|---:|---:|---:|---:|---|
| 8 | 4 | 4 | 8 | Discard at s2 |
| 0 | 1 | 0 | 1 | Immediate discard at s1 |
| 1 | 1 | 0 | 1 | Immediate discard at s1 |
| 2 | 1 | 1 | 2 | Discard at s2 |
| 3 | 2 | 1 | 3 | Discard at s1 |

Every per-packet count matched the design and remained stable for five seconds. All ten loop assertions passed; see [loop checks](evidence/loop-after-raw/checks.json). The zero case explicitly confirms that the budget does not wrap to 255. These tests establish the observed cases; the guard and monotonic decrement explain the general bound.

## 5. Evaluation

### a. Mixed deployment: prediction and observation

The original [prediction](MIXED-PREDICTION.md) was saved before implementation/testing and is reproduced in [mixed.txt](evidence/mixed.txt). I predicted that old s2 would preserve the destination prefix but misparse the extra byte as IPv4, corrupt the enclosed packet through checksum recomputation, and fail normal UDP delivery. I also predicted that an 8-budget loop through new s1 and old s2 would stop after **15 total visits**, because only s1 decrements.

The topology was launched with `--id 6042 --s2-program tunnel_v1.p4`. I sent to IPv4 address `10.42.0.3` with tunnel identifier 2 and limit 8, and captured on **h2**. The frame did reach h2: the destination identifier remained 2 and the received budget was 7, confirming only s1 decremented. However, no normal UDP receiver message appeared. The [raw capture](evidence/mixed-raw/logs/h2cap.txt) and [decoded measurements](evidence/mixed-raw/checks.json) explain why.

Offsets below are measured from the start of the Ethernet frame, without an FCS:

| Bytes | Correct interpretation | Old s2's interpretation/effect |
|---|---|---|
| 14–15: `08 00` | Encapsulated protocol IPv4 | Correct tunnel `proto_id` |
| 16–17: `00 02` | Tunnel destination 2 | Correct tunnel `dst_id`, selecting h2 |
| 18: `07` | Remaining hops 7 | IPv4 first byte: version 0, IHL 7 |
| 19: `45` | Real IPv4 version 4/IHL 5 | Old parser's IPv4 service byte |
| 28–29: `0d 66` after s2 | Real protocol byte and first checksum byte | Old parser's two-byte IPv4 checksum, rewritten by its checksum stage |
| 30: `6b` | Real IPv4 checksum's second byte | Not part of the old parser's checksum field |

Before s2, the actual IPv4 protocol byte was `0x11` (17, UDP). Old s2's checksum update wrote `0x0d66` into its misaligned checksum positions, changing that real protocol byte to **`0x0d` (13)**. The real checksum bytes in the received frame were `66 6b`, which failed checksum validation over the real 20-byte IPv4 header. The UDP bytes were still present later in the frame, but the IP protocol no longer selected UDP. The old parser does not validate IPv4 version/IHL and its tunnel table remains applicable, so this damage occurs despite successful forwarding to the intended physical host.

I then created the destination-3 loop in the same mixed network. Before the loop, both switches had one reception from the delivery test. Counts rose to **s1=9, s2=8**, then stayed unchanged for five seconds. Subtracting that prior delivery gives **8 s1 visits + 7 s2 visits = 15**, with discard at new s1 on incoming budget 1. All six mixed assertions passed. The observed behaviour agrees with the prediction; the captured checksum/protocol values provide the exact bytes that were unknown before testing. This bound depends on revisiting an upgraded switch and does not protect a cycle containing only old switches.

### b. Safe upgrade approaches

| Approach | Deployment sequence | Benefits and costs |
|---|---|---|
| **New EtherType with dual-format upgraded switches** | First deploy a parser that accepts old four-byte traffic and a distinct new EtherType for the five-byte format. Continue sending old packets during preparation. Enable new packets only on paths whose switches and receivers support them; constrain paths or use boundary translation until upgrades finish. | Explicit discrimination prevents a new header being silently treated as the old layout. Old switches cannot safely transit new packets merely because another EtherType is chosen: they drop unknown traffic in this program. Requires capability/path management and temporary dual-format parsing, but enables unambiguous full enforcement on upgraded paths. |
| **Keep the legacy prefix and use a new `proto_id` for an opaque extension** | Use the existing four-byte outer header, with a new protocol discriminator meaning an extension containing hops followed by IPv4. Prepare upgraded parsers/receivers to accept both forms before changing senders. The inspected old parser accepts non-IPv4 `proto_id` without extracting IPv4, and its tunnel action can forward that opaque suffix using the unchanged destination field. | Old nodes avoid the misaligned IPv4 checksum update and preserve the extension as payload. This can maintain transit through these particular old programs, but they still do not decrement the limit. Every allowed cycle must cross an enforcing node, or old-only cycles must be prevented by configuration. Requires verifying opaque forwarding on the actual legacy target and handling boundaries explicitly. |

These are rollout proposals, not features claimed in the current implementation. Adding a version byte in front of an old header, or simply appending a field as in this experiment, is insufficient unless old nodes already know how to distinguish or skip it. For a network requiring protection at every hop, I would use dual-format switches and enable the new EtherType only on fully upgraded paths, then retire the old format after validation.

### c. Data-plane limit versus Week 3 `check_paths()`

The [Week 3 assignment](https://firdaussahran.github.io/wic2005/weeks/week-03/#tab-lab) specifies `check_paths()` as a pre-build simulation over ordered host pairs: follow modeled router next hops using longest-prefix matching, report a missing route or a revisited router, and reject faulty configurations before construction. Its [starter](https://firdaussahran.github.io/wic2005/labs/week-03/build_routed.py) contains a stub to be completed. This comparison concerns the required completed checker; this local coursework's `week3/routers.py` does not implement that function.

The checker can identify a modeled loop before traffic exists, explain the offending route/path, and detect a missing route that a hop counter cannot diagnose. It can also reject a long cyclic path even if a particular packet would have expired before traversing the whole cycle. Its result depends on the configuration model and destinations considered; it does not establish the deployed switch state, link health, packet format or later runtime edits.

The data-plane limit acts on actual traffic after deployment. It bounds repeated visits caused by stale rules, a runtime table change such as C1, or a forwarding error absent from the checked model. It does not discover or repair the bad entry, prove destination reachability, or distinguish a loop from an unusually long legitimate path. It also cannot enforce a bound on old-only cycles. Control-plane validation prevents known modeled errors, while packet-local enforcement contains residual runtime failures; both are needed.

### d. Hardware costs at line rate

The header grows from four to five bytes: one extra wire byte when not absorbed by Ethernet padding, plus one extra byte against the encapsulation/MTU budget. A fixed MTU may require reducing the maximum inner packet by one byte. The field requires at least eight more logical packet-header bits; a particular ASIC may allocate a larger slice because of its storage alignment.

Ingress adds an 8-bit comparison, a conditional drop and an 8-bit subtraction. These are simple fixed-width operations suitable for a match-action pipeline, but actual stage/ALU allocation, PHV packing and timing depend on the target compiler and available resources. I cannot claim a particular cycle count, latency or guaranteed line rate from BMv2 results. Compilation and resource reports on the intended ASIC would be required.

The existing tunnel table key and entry count do not change, so the design adds no logical match-key width or table entries and no per-flow state/registers. The comparison/decrement may still consume target action resources. The added byte is outside IPv4, so changing it does not require a new IPv4 checksum calculation; the existing computation remains. The data plane needs no controller or CPU round trip per packet. In return, expiry limits loop bandwidth and repeated processing, although an attacker or faulty sender can choose the maximum 255 and a budget alone is not admission control. BMv2 packet counts and debug-log overhead are functional evidence, not hardware throughput measurements.

## AI use

I used an AI coding assistant through Claude Code to assist me throughout the lab and assignment and to double-check whether the work met the requirements. This assistance included explaining the tasks, developing the design and prediction, helping implement and debug the P4 and Python code, running automated experiments, checking the saved logs and packet captures, and helping draft and review the report. The checks compared the observed results with the expected behaviour, including delivery, remaining hop values and loop termination. I also used Codex reviewers through Orca to independently check the implementation, evidence, documentation and assignment requirements, and to rerun the experiments in an isolated copy. All reported observations come from the saved experimental outputs. I remain responsible for reviewing and understanding the work and ensuring that the final submission is accurate.


## Evidence files

| File | What it shows |
|---|---|
| `evidence/loop-before.txt` | The loop with your finished lab program: pass counts growing |
| `evidence/delivery.txt` | Tunnelled delivery with the hop limit, and a plain ping |
| `evidence/loop-after.txt` | The same loop with your hop limit: pass counts that stop |
| `evidence/mixed.txt` | The mixed rollout: s1 new, s2 old |
