# Required PR title

Tunnel hop limit

# PR body

The original tunnel forwarding action can circulate packets indefinitely after a runtime table change creates a loop. Add an 8-bit `hops` field after the original tunnel destination, default it to 8 in the sender, and discard incoming budgets 0 or 1 before lookup. Forwarded packets spend one budget unit per upgraded switch. The receiver displays the remaining value; `tunnel_v1.p4` preserves the completed practical for mixed-version testing.

In the supplied two-switch Mininet topology, both tunnel destinations received default-budget packets with 6 remaining, and ordinary IPv4 continued working. The all-upgraded loop terminated after eight visits. With old s2, the loop terminated after 15 visits, while a packet capture demonstrated the old parser's one-byte misalignment corrupting the enclosed IPv4 protocol/checksum. The report explains the pre-test prediction, upgrade alternatives, comparison with Week 3's path checking and hardware costs.

Validation: P4 compilation in the official course image; 26 passing delivery, argument-validation, loop-boundary and mixed-version assertions. Evidence is under `assignment/evidence/`, with design and analysis in `assignment/REPORT.md`. The Compile tunnel.p4 check runs from the repository-root workflow, which compiles in `week5/`.

Leave this PR unmerged for lecturer review. AI assistance is declared in the report.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
