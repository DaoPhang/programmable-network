# Assignment completion report

## Completed

- Kept the existing three-switch, six-host, eight-link network and address suffix 6042.
- Regenerated topology.json from topology.yaml and checked equality of their loaded data.
- Implemented links_section() and mermaid_diagram() from topology links. HTML names are escaped and diagram identifiers are independent of display labels.
- Created bad.yaml containing duplicate IPv4, duplicate IPv6 and an unknown switch s9. Confirmed validation stops before constructing this network.
- Recorded all five required files: evidence/check.txt, pingall.txt, neigh.txt, macs.txt and dad.txt. Additional evidence/session.txt preserves the test session; ipv6all.txt records every directed IPv6 host pair.
- Set the real repository URL in page.yaml.
- Added seven technically grounded draft answers. These were prepared by the assistant and must be reviewed, understood and rewritten in the student's own words before submission.
- Generated docs/index.html with topology, eight links, diagram source, evidence and populated answers.

## Verified results

- IPv4 all-pairs: 0% dropped, 30/30 received.
- IPv6 all-pairs: 30/30 probes received; separate h1-to-h6 run: 3/3 replies.
- h1 neighbour table contains IPv4 neighbours and IPv6 neighbour fd00:6042::6.
- s1 learned host MAC endings 01, 02, 03 on ports 1, 2, 3; host endings 04, 05, 06 on its inter-switch port 4.
- Duplicate IPv6 fd00:6042::1 on h2 was marked dadfailed. Duplicate IPv4 10.42.0.1 was accepted as a secondary address. These temporary changes were confined to a disposable test network; topology.yaml remains valid.
- Invalid input reports duplicate addresses 10.42.0.2 and fd00:6042::2, and unknown node s9.
- Generated HTML contains no missing-evidence warnings, blank answers or TODO placeholders. Link count and Mermaid edge count both match all eight links.
- Tests used separate disposable containers; the existing interactive lab container was left running untouched.

## Still manual

1. Review the code and seven draft answers. Use your own explanations and confirm you can explain the experiments.
2. Open docs/index.html in a browser with internet access and check the Mermaid diagram renders. The diagram source and HTML structure were verified; browser rendering depends on the external Mermaid CDN.
3. Re-run `python3 make_page.py topology.yaml` inside the lab container after editing page.yaml or other displayed inputs.
4. Review changes, commit and push from your local repository. No commits or uploads were made by these agents.
5. Enable GitHub Pages from main and /docs, then check the public page.
6. Submit the published page URL through Spectrum under the course's current submission instructions.

No Docker Compose file is required for the supplied single-container workflow.
