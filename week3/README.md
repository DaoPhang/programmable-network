# Lab 3 Inside the Forwarding Path

Student suffix: 6042. IPv4 block: 10.42.0.0/16.
IPv6 block: fd00:6042::/32.

Start Docker Desktop and run the shared container command from the root
README. Inside that container:

~~~bash
cd /lab/week3
python3 routers.py --id 6042
~~~

The routers.py topology is the lecturer's existing script.
Hosts have addresses and default gateways. Configure forwarding and static
router routes at mininet> following the course lab.

Experiments completed in the pasted run:

1. Gateway reachable; remote host initially unreachable.
2. Directly connected routes and forwarding disabled.
3. IPv4 forwarding enabled; missing route produces network unreachable.
4. Static routes added; h2 and h3 reachable.
5. Longest-prefix lookup selects /24 for h2, /20 for h3.
6. IPv4 traces show three hops to h2, four to h3.
7. Deleting /24 causes fallback; removing r3's route produces !N.
8. Routing loop alternates r1/r3 until TTL expires.
9. IPv6 pings, lookups and traceroute succeed.

The IPv6 h3 trace identifies r2 at fd00:6042:23::2; IPv4 identified it at
10.42.12.2. See [the write-up](6042_Lab3_Writeup.md) for all five answers
and excerpts from the user's observed outputs.

No raw session log was supplied as a file; none is invented here.
For future sessions, optional recording from the container shell:

~~~bash
mkdir -p evidence
script -q -f evidence/session-01.txt
python3 routers.py --id 6042
~~~

After finishing, exit Mininet, exit the recording shell if used, then exit
the container. Use a fresh log filename for later runs.

Review the write-up and submit it through the appropriate Spectrum activity.
Course instructions:
https://firdaussahran.github.io/wic2005/weeks/week-03/#tab-lab