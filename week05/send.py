#!/usr/bin/env python3
"""Send one UDP packet, optionally inside the custom tunnel header.

    python3 send.py <ip address> "<message>"              plain IPv4
    python3 send.py <ip address> "<message>" --tunnel N --hops 8

The five-byte tunnel header carries proto_id, dst_id and an 8-bit visit budget.
"""
import argparse

from scapy.all import IP, UDP, Ether, Packet, ByteField, ShortField, bind_layers, get_if_hwaddr, get_if_list, sendp


class MyTunnel(Packet):
    name = "MyTunnel"
    fields_desc = [ShortField("proto_id", 0x0800), ShortField("dst_id", 0), ByteField("hops", 8)]


bind_layers(Ether, MyTunnel, type=0x1212)
bind_layers(MyTunnel, IP, proto_id=0x0800)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("message")
    ap.add_argument("--tunnel", type=int, metavar="N", help="tunnel exit to deliver to")
    ap.add_argument("--hops", type=int, metavar="N", help="tunnel visit budget, 0–255 (default: 8)")
    args = ap.parse_args()
    if args.hops is not None and not 0 <= args.hops <= 255:
        ap.error("--hops must be between 0 and 255")
    if args.hops is not None and args.tunnel is None:
        ap.error("--hops requires --tunnel")
    if args.tunnel is not None and not 0 <= args.tunnel <= 65535:
        ap.error("--tunnel must be between 0 and 65535")

    iface = next(i for i in get_if_list() if i.endswith("-eth0"))
    pkt = Ether(src=get_if_hwaddr(iface), dst="ff:ff:ff:ff:ff:ff")
    if args.tunnel is not None:
        pkt = pkt / MyTunnel(dst_id=args.tunnel, hops=8 if args.hops is None else args.hops)
    pkt = pkt / IP(dst=args.ip) / UDP(sport=4321, dport=4321) / args.message
    pkt.show2()
    sendp(pkt, iface=iface, verbose=False)
    print(f"Sent from {iface}.")


if __name__ == "__main__":
    main()
