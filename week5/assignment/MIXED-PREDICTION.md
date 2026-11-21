# Mixed-version prediction, recorded before implementation and testing

This prediction was written before changing the packet layout and before sending any C4/C5 packets. It is kept separately so the original expectation stays visible.

## Chosen format and semantics

New header: `proto_id` (2 bytes), `dst_id` (2 bytes), `hops` (1 byte), then IPv4. Default hops 8. An upgraded switch drops incoming hops 0 or 1; otherwise it subtracts one before the tunnel lookup. EtherType remains 0x1212 for this deliberate compatibility experiment. The old header is only four bytes.

## Delivery prediction

For new s1 and original s2, s1 changes hops 8 to 7. s2 reads the unchanged proto_id/dst_id prefix correctly, so destination 2 still selects h2. However, s2 interprets the hop byte as IPv4's first byte. Its parsed version becomes 0 and IHL becomes 7 (from 0x07); its fields are shifted one byte. The supplied old program does not validate those fields and still applies the tunnel table.

The old program recomputes the checksum of its misaligned IPv4 header. Its checksum positions correspond to bytes 9 and 10 of the real IPv4 header: the real protocol byte and the first checksum byte. I predict a frame reaches h2 with the hop byte still 7 but damaged enclosed IPv4 protocol/checksum, preventing the normal UDP receiver from reporting a valid test message. A raw 0x1212 capture should reveal this. Keeping the four-byte prefix is not enough for safe compatibility.

## Loop prediction

After setting old s2's tunnel destination 3 to port 1, s1 and s2 will still use the correct tunnel destination field. s2 will not decrement hops. New s1 will decrement it on successive returns and eventually drop incoming 1. With initial 8, I predict s1=8 visits, s2=7 visits, total=15, followed by stable counts. The enclosed IPv4 fields may be damaged, but the tunnel prefix/hop positions remain available to s1 and still bound this particular loop.

This does not prove safety for loops that visit no upgraded switch. The all-upgraded loop should instead stop after eight total visits (s1=4, s2=4).
