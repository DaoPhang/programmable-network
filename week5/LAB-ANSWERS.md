# Week 05 practical — lab question answers

Student ID suffix: **6042**

Host addresses: **10.42.0.1**, **10.42.0.2**, **10.42.0.3**

[Official lab questions](https://firdaussahran.github.io/wic2005/weeks/week-05/#tab-lab)

These answers refer to the completed practical program and the actual experiments recorded in `evidence/practical/`. The experiments ran in the official course image using local Docker. All 31 checks passed; see [RESULTS.md](RESULTS.md) and the [check summary](evidence/practical/summary.json).

## 1. Give two further runtime changes and two changes requiring a new P4 program

Two changes possible without recompiling the completed program are:

1. **Change a tunnel destination's output port.** The control plane can modify an entry in `MyIngress.myTunnel_exact`, for example mapping destination identifier 2 to a different output port using the existing `myTunnel_forward` action. This changes an entry's action parameter while keeping the table key and action definition unchanged.
2. **Change the IPv4 table's default action.** The control plane can change `MyIngress.ipv4_lpm` from default `drop` to its existing `ipv4_forward` action with a chosen output port. Both actions are already allowed by that table, and its default action is not declared constant. This changes what happens on a lookup miss without changing the P4 pipeline.

These are examples supported by the completed program, not additional experiments claimed as part of the saved run. The runtime experiment actually recorded was deleting and restoring h3's IPv4 entry.

Two changes requiring a revised program and compilation are:

1. **Introduce a new header field and processing logic**, such as adding a hop limit to `myTunnel_t`, decrementing it and dropping exhausted packets. This changes the packet format and switch behaviour; the sender and receiver must also agree on the new format.
2. **Change a table's key**, such as matching both tunnel `dst_id` and `proto_id` instead of `dst_id` alone. The key is defined by the P4 source, so changing it requires recompilation and loading the updated pipeline, with compatible table entries.

Runtime entries choose among the matches, actions and parameters the installed program already supports. They cannot add new parser states, header layouts or action logic.

## 2. Why did Step 4 deliver to h3 rather than h2, and why did the tunnel header remain?

The test packet contained two different destinations: IPv4 address **10.42.0.3**, belonging to h3, and tunnel destination identifier **2**, associated with h2.

Step 4 added tunnel parsing and emission, but ingress still selected `ipv4_lpm` for a valid IPv4 header. It did not apply `myTunnel_exact`. Both switches therefore forwarded using the enclosed IPv4 destination, and s2 sent the packet to h3 on port 3. The compiler's unused-table warning confirmed that the tunnel table was not applied.

The parser extracted `hdr.myTunnel`, making it valid. The deparser explicitly emitted that header between Ethernet and IPv4. No action invalidated or removed it, so forwarding preserved the tunnel header even though its destination identifier was not used for the forwarding decision.

The [h3 receiver log](evidence/practical/step04-parser-deparser/logs/h3.txt) records `test 2` with `dst_id=2` and TTL 62. This demonstrates that parsing a header and forwarding according to that header are separate parts of the program.

## 3. Why did the Step 5 tunnel packet retain TTL 64 while ping replies showed TTL 62?

In Step 5, ingress first checks whether `hdr.myTunnel` is valid. A tunnelled packet uses `myTunnel_exact`, whose `myTunnel_forward` action only sets the output port. It does not decrement the enclosed IPv4 TTL. The sender's initial TTL of 64 therefore remains 64 through both switches.

An ordinary ping has no tunnel header, so it uses `ipv4_lpm`. Its `ipv4_forward` action subtracts one from IPv4 TTL at each switch, and checksum computation updates the IPv4 header checksum. A packet starting at TTL 64 arrives after two switches with TTL **64 − 2 = 62**.

The ping reply is a newly generated IP packet with its own initial TTL. The TTL 62 printed by h1 reflects the reply's two-switch return journey; it is not the original request's TTL reduced across a four-switch round trip.

The [Step 5 transcript](evidence/practical/step05-tunnel-forwarding/session.txt) records the tunnel packet arriving at h2 with TTL 64 and ordinary h1-to-h3 ping succeeding with reply TTL 62.

## 4. Which mistakes produced compiler warnings, which escaped detection, and what does this imply for P4 testing?

| Stage | Compiler observation | What packet tests established |
|---|---|---|
| Starter before Step 4 | Warnings reported unused `TYPE_MYTUNNEL` and unused table `myTunnel_exact`; the table was removed. | The starter did not support the tunnel EtherType, and neither host received the tunnel test packet. |
| Step 4: parsing/emission added, tunnel table still not applied | The compiler still warned that `myTunnel_exact` was unused and removed it. | The packet was delivered to h3 using its IPv4 address, even though its tunnel destination was 2. |
| Step 5: tunnel table applied | The unused tunnel-table warning disappeared. | h2 received the packet using the tunnel destination, and ordinary IPv4 still worked. |
| Step 6: tunnel emission deliberately omitted | The program compiled without a P4 warning about the missing emission. | The outgoing wire format was wrong. s2 misread IPv4 bytes as tunnel fields and dropped the packet. |

The unused-table warning exposed an unused forwarding path, but the compiler did not determine whether the program matched the intended forwarding policy. In particular, it accepted the Step 6 deparser because emitting Ethernet followed by IPv4 is syntactically and structurally legal, even when Ethernet's type field still advertises a tunnel header.

The [Step 6 s2 log](evidence/practical/step06-broken-deparser/logs/s2.txt) shows parser key `4500`, tunnel destination `0022` and the default drop action. These bytes came from IPv4's first four bytes: `0x4500` contains the version/header-length and service byte, while `0x0022` is the 34-byte IPv4 total length for this test packet.

P4 testing must therefore combine compilation and warning review with packet experiments and switch-log inspection. Tests should check the receiving host, header preservation, TTL and expected drops. A successful compilation alone does not prove that the emitted bytes or forwarding decisions are correct. Mininet's resource-limit warning and Scapy's interface-down messages during teardown are environment/runtime messages, not P4 compiler warnings.

## Completed program and assistance

The completed practical is preserved as [tunnel_v1.p4](tunnel_v1.p4), including tunnel parsing, tunnel-first forwarding and `packet.emit(hdr.myTunnel);`. The Step 6 fault is restored, and this baseline matches the tested [Step 5 program](stages/step05-tunnel-forwarding.p4). The current `tunnel.p4` adds the later assignment's hop limit.

AI assistance was used to prepare the P4 changes, automate the practical experiments, analyse the saved logs and draft these answers. The observations above are supported by the saved experimental evidence. Review the program and answers so you can explain and defend the work.
