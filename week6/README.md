# Lab 6: Linux Networking Building Blocks, VXLAN and Containers

Student ID suffix: 6042  
Date: 19 November 2026

[Course lab instructions](https://firdaussahran.github.io/wic2005/weeks/week-06/#tab-lab)

## Setup

The lab used `firdaussahran/netlab-mininet:1.0`, started with `start-lab-wsl.sh`. Addressing uses
NN = 42: IPv4 block `10.42.0.0/16`, IPv6 block `fd00:6042::/32`. Parts 1–6 ran inside the lab container
and Part 7 ran with `docker.exe` from WSL, outside it. Each part was recorded with `script`.

## Practical results (Parts 1 to 7)

| Part | Actual result | Evidence |
|---|---|---|
| 1: Mininet hosts are namespaces | `h1` and `h2` were `bash` processes (pids 1552 and 1554), each in its own network namespace. `h1` saw only `lo` and `h1-eth0`. The container saw `s1-eth1` and `s1-eth2`. | [part1.txt](practical/part1.txt) |
| 2: Week 1's network by hand | Namespaces `red` and `blue`, two veth pairs and bridge `br0`. red pinged blue 2/2. `br0` learned one MAC on each of `red-br` and `blue-br`. | [part2.txt](practical/part2.txt) |
| 3: VXLAN overlay by hand | `vxlan100` (VNI 100) between h1 and h2. The first pings failed because a garbled line left h2's `vxlan100` down. After `h2 ip link set vxlan100 up`, pings succeeded 2/2 and 3/3. The capture on h2 showed `10.42.0.1 > 10.42.0.2:4789 VXLAN vni 100` carrying the ICMP echo. | [part3-4.txt](practical/part3-4.txt) |
| 4: Cost of tunnelling | `h1-eth0` MTU 1500, `vxlan100` MTU 1450. DF ping payload 1422 worked and 1423 was refused (`message too long, mtu=1450`). iperf3: underlay 28.8 Gbit/s, overlay 22.1 Gbit/s. | [part3-4.txt](practical/part3-4.txt) |
| 5: Same tunnel over IPv6 | IPv6 ping 2/2. `vxlan106` (VNI 106) MTU 1430. Payload 1402 worked and 1403 was refused (`mtu=1430`). The capture showed `IP6 fd00:6042::1 > fd00:6042::2:4789 VXLAN vni 106` carrying IPv4 ICMP. | [part5.txt](practical/part5.txt) |
| 6: MTU mismatch | With `h2-eth0` at MTU 1400, small pings worked, a 1400-byte-payload DF ping lost 2/2, and iperf3 moved 4.5 MBytes in the first second and 0 after that. Largest working payload 1326, smallest failing 1327. `tx_dropped` on `s1-eth2` and `rx_dropped` on `h2-eth0` were both 108. After restoring MTU 1500 the ping worked and iperf3 ran at 22.1 Gbit/s with 0 retransmits. `ip link set vxlan100 mtu 1500` was refused with `Invalid argument`. | [part6.txt](practical/part6.txt) |
| 7: Containers | `alpine:3.20` container `c1`: Alpine Linux v3.20 (`VERSION_ID=3.20.10`), `eth0` 172.17.0.4/16, MTU 1500, and `ps` showed only `sleep 600` as PID 1 plus the `ps` command. Removed with `docker.exe rm -f c1`. | [part7.txt](practical/part7.txt) |

In Part 7 the plain `docker` command was not available inside the WSL distribution, so the recording
starts with that error and then uses `docker.exe`.

## Assignment: overlay your own data centre

The design in `overlay.yaml` has three hypervisors (`hv1`, `hv2` and `hv3`) on `10.42.0.0/24` and two tenants on the
same network, `10.42.50.0/24`: web (VNI 4201: web1, web2, web3) and db (VNI 4202: db1, db2).
`build_overlay.py` builds it, with `tenant_commands()` and `check_mtu()` written by me.

| Evidence file | What it shows |
|---|---|
| [evidence6/check.txt](evidence6/check.txt) | `check_mtu()` refusing the black-hole design (1550 > 1500, both tenants) |
| [evidence6/flood.txt](evidence6/flood.txt) | VTEP tables before and after traffic, and the flooded ARP captured on hv3 |
| [evidence6/isolation.txt](evidence6/isolation.txt) | web3 pinging 10.42.50.11; web2 answered, db2 captured 0 packets |
| [evidence6/blackhole.txt](evidence6/blackhole.txt) | 1500-byte DF ping lost, iperf3 0 bytes, largest working payload 1422, smallest failing 1423 |
| [evidence6/fixes.txt](evidence6/fixes.txt) | Fix A (tenant MTU 1450): 3.64 Gbit/s. Fix B (underlay 9000): 3.27 Gbit/s |
| [evidence6/session.txt](evidence6/session.txt) | Raw terminal recording, unedited, including typing mistakes and a garbled paste |

The chosen fix in `overlay.yaml` is Fix B (underlay MTU 9000). Each throughput figure is one 5-second run.

The generated page is `docs/week6/index.html`.

## Wrap-up answers

### 1. Linux building blocks behind one Mininet host and one Mininet cable

A Mininet host is a `bash` process (`bash --norc --noediting -is mininet:h1`, pid 1552 in Part 1)
running in its own network namespace, which gives it its own interfaces, routes and neighbour table.
`h1` saw only `lo` and `h1-eth0`, while the container's namespace saw `s1-eth1` and `s1-eth2`. A Mininet
cable is a veth pair: two virtual interfaces that pass frames to each other, with one end in the host's
namespace and the other on the switch. The `@if` numbers in `ip -br link` name the other end of the pair.
In this lab the switch (`lxbr`) is a Linux bridge.

### 2. MTU and throughput measurements, and the 50-byte difference

| Measurement | Result |
|---|---|
| `h1-eth0` MTU | 1500 |
| `vxlan100` MTU | 1450 |
| Largest DF ping that worked | payload 1422 (1450-byte packet) |
| Smallest DF ping that failed | payload 1423, refused locally with `mtu=1450` |
| iperf3 underlay (`10.42.0.2`) | 28.8 Gbit/s |
| iperf3 overlay (`10.42.100.2`) | 22.1 Gbit/s |

Each throughput figure is a single 5-second run, and the underlay run dipped to 16.2 Gbit/s in one
second, so the gap is indicative only. I did not measure what part of it comes from the extra headers
and what part from the cost of encapsulation.

The 50 bytes are the headers VXLAN adds around the tenant's IP packet: an inner Ethernet header (14),
a VXLAN header (8), a UDP header (8) and an outer IPv4 header (20). All of that must fit in the
underlay's 1500-byte IP packet, which leaves 1450 bytes for the tenant's IP packet. `build_overlay.py`
uses the same figures for `VXLAN_OVERHEAD`.

Over IPv6 the outer header is 40 bytes instead of 20, so the overhead is 70 bytes. Part 5 matches this:
`vxlan106` had MTU 1430, payload 1402 worked, and 1403 was refused with `mtu=1430`. The capture shows
the IPv6 outer header (`fd00:6042::1 > fd00:6042::2`, port 4789, vni 106) but does not print byte
lengths, so the 70 bytes come from the MTU and the header sizes.

### 3. Why small pings survived the MTU mismatch while TCP almost stopped

After I set `h2-eth0` to MTU 1400, a small ping still worked, and so did every size up to payload 1326.
A tunnelled packet is 50 bytes larger than the packet inside it, so only inner packets above 1354 bytes
(outer packets above 1404, which is 4 bytes over the 1400 MTU) were dropped, and a small ping is far
below that. Payload 1327 and above vanished silently, with no error message at the sender. The counters
show where: `tx_dropped` on `s1-eth2` and `rx_dropped` on `h2-eth0` were both 108.

TCP sends full-size segments, which are the packets that exceed the limit. iperf3 moved 4.5 MBytes in
the first second and nothing after that, with the congestion window stuck at 1.37 KBytes and 95
retransmits. Nothing told the sender that its packets were too big, so it kept retransmitting segments
that were dropped again. The receiver counted only 1.25 MBytes of what the sender reported as sent.
After `h2-eth0` went back to 1500, iperf3 ran at 22.1 Gbit/s with no retransmits.

### 4. What a Docker container has that a Mininet host does not

The container in Part 7 had its own operating system image (Alpine Linux v3.20) and its own process
list: `ps` showed only `sleep 600` as PID 1 and the `ps` command. It also had its own network namespace,
with an address assigned by Docker (172.17.0.4/16).

In Part 1 a Mininet host was visible from outside as an ordinary `bash` process in the lab container's
process list (pid 1552), and `lsns -t net` showed it with its own network namespace. I only listed
network namespaces there, so I cannot say from my output which other namespaces it has.

### 5. This VXLAN tunnel compared with the Week 5 tunnel

- Bytes added: Week 5's tunnel header (`tunnel.p4`) has two 16-bit fields, `proto_id` and
  `dst_id`, so it adds 4 bytes. VXLAN over IPv4 adds 50 bytes.
- Devices that must understand it: every P4 switch on the path had to understand the Week 5 header.
  With VXLAN only the VTEPs do, and the network in between only routes IP, as the header of
  `vtep.p4` states.
- What stops loops: in my Week 5 assignment I added an 8-bit `hops` field to the tunnel header. A
  switch drops a tunnelled packet whose incoming `hops` is 0 or 1 and otherwise subtracts one before
  the table lookup. Without it, a loop I created between s1 and s2 kept circulating a single packet
  (counts rose from 18 and 17 to 192 on both switches). With `--hops 8` the counts stopped at 4 and 4,
  8 visits in total. The tunnel itself carries the protection, so every switch on the path has to
  enforce it. In `vtep.p4` the VTEP gives the outer IPv4 packet a fresh TTL of 64, and the underlay
  routers count it down, so the tunnel header needs no counter of its own. The program has no TTL
  check of its own, and I did not test a loop in the VXLAN overlay.

## AI use

I used Claude Code throughout Week 6, for the practical and for the assignment. It explained what the lab
and the assignment asked for, listed the files I needed and gave me the commands one step at a time. I ran
every command myself in my own terminal and pasted the output back, so the recordings in `practical/` and
`evidence6/` come from my own runs. Claude Code did not run the lab for me.

For the assignment it downloaded the four starter files, wrote `check_mtu()` and `tenant_commands()` in
`build_overlay.py`, and helped me turn `overlay.yaml` into my own design, including `blackhole.yaml`,
`mtu_a.yaml` and `mtu_b.yaml`. It also drafted the answers in `page6.yaml` and this README from my results,
and moved the generated page into `docs/week6/`. Whenever something went wrong I pasted the error and it
helped me work out the cause. Examples are a garbled paste that left `vxlan100` down on h2, an empty
`tcpdump` capture that I redid with a packet count, a size sweep that gave wrong results because the
command was split over two lines, a `practical/` folder that WSL could not write to, and the missing
`docker` command in WSL, where `docker.exe` worked. I kept those mistakes in the recordings.

I also used it for the P4 answer. It downloaded the lecture's `vtep.p4` and I based the answer on that file.
For the Week 5 loop comparison it read my Week 5 report and `tunnel.p4` from the `hop-limit` branch. Last, it
helped me rewrite some sentences so they read more naturally.
