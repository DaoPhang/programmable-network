# Independent pre-submission review

Result: PASS for local C1 to C5 implementation and experiments. C6 is the PR from `hop-limit`; its GitHub check is reported on the PR.

Three independent Codex workers, coordinated through Orca, reviewed the implementation, audited the report/evidence against the course requirements, and reran the experiments. The requested `codex-luna` model was rejected by the connected ChatGPT account before review work began; the workers were restarted with the configured default Codex model.

## Implementation review

No concrete C2/C3 defects were found. The reviewer checked the matching five-byte P4/Python formats, parsing/deparsing, guarded decrement, exhaustion handling, unchanged ordinary IPv4 path, receiver display and unchanged baseline. Nine sender argument/default/boundary cases were also checked without network operations.

## Documentation and evidence audit

The report's C1 to C5 coverage, visit-count mathematics, mixed-version byte analysis, Week 3 comparison and hardware-cost limitations agreed with the saved evidence and course requirements. Relative links and standalone export layout were valid.

The audit found two problems, both now fixed:

- The course's required PR title is Tunnel hop limit; PR-DESCRIPTION.md now uses that exact title.
- REPORT.md's AI-use section now includes the independent Codex/Orca review contribution.

The audit could not independently prove the claimed pre-test prediction chronology from saved files alone. It also noted that the course requests Codespaces while these experiments transparently used the official image on local Docker; lecturer acceptance of that environment substitution has not been confirmed. No unsupported ASIC throughput claim is made.

## Fresh live tests

The test worker copied the current sources into a fresh isolated review workspace and used the approved official privileged Docker image. Existing original evidence was not replaced. All three runners exited successfully.

| Fresh execution | Outcome |
|---|---|
| `run_practical.py` | 31/31 assertions passed |
| `assignment/run_loop_before.py` | Counts grew on both switches: s1 23 to 157, s2 23 to 157 over 5.021 seconds |
| `assignment/run_assignment.py` | 26/26 assertions passed: delivery 10, protected loop 10, mixed 6 |
| Independent C1 and mixed-capture verification | Both passed |

Total: 59 checks passed, 0 failed in the live review: 57 runner assertions plus two independent evidence checks. The implementation review's separate nine argument checks are not included in this total.

The normal tunnel receivers reported hops 6; ordinary IPv4 worked; the upgraded loop stopped after eight visits; the mixed loop stopped after 15. The fresh capture again showed mixed remaining hops 7, actual IPv4 protocol 13 and invalid checksum. C1's exact counts depend on timing; their difference from the original report is not a contradiction.

All tested source/config/stage files and original evidence retained their initial hashes. Only REPORT.md and PR-DESCRIPTION.md changed concurrently for the two documentation corrections. The test container was removed and no live Mininet jobs remained. Teardown interface-down and container resource-limit warnings did not prevent the tests passing.

The full rerun used a disposable isolated workspace under `week5/build/`. That workspace was removed during cleanup after its results were recorded here. Required original evidence remains in assignment/evidence/ and agrees with the independent rerun.

## Publication state

No changes were staged, committed or pushed during these independent reviews. The history was later rebuilt on `hop-limit` for the PR; see [README.md](README.md#c6-prepare-and-submit).
