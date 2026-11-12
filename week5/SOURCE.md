# Source and verification record

## Upstream starter

- Repository: https://github.com/firdaussahran/p4-lab
- Retrieved revision: `88245a03baf7dac20e20969d838b1e4e1dfecc09`
- Retrieved branch: `main`
- Course environment image: `ghcr.io/firdaussahran/p4-lab:1.0`
- Upstream Git metadata was not copied into this coursework repository.

The topology, sender, receiver, runtime helper, table files, dev-container configuration, workflows and assignment skeleton came from the official starter. TEMPLATE-README.md preserves the upstream README. Stage `step03-starter.p4` preserves its original P4 source.

## Local additions and edits

- `tunnel.p4`: implement tunnel parsing, deparser emission and tunnel-first ingress selection for the practical.
- `stages/`: preserve the original and three later experimental versions.
- `run_practical.py`: run staged experiments and record raw outputs without replacing the final program.
- Documentation: README.md, START-HERE.md, PREPARATION.md, RESULTS.md and SOURCE.md.
- `p4cli`: normalise CRLF to LF so Linux can execute the shell script. Its command logic is unchanged.
- `.gitattributes`: preserve Linux line endings in code/helper files.
- `.gitignore`: anchor build/log exclusions at the week05 root, allowing saved evidence logs to be tracked.
- The parent repository README links to `week05/`.

The final source matches `stages/step05-tunnel-forwarding.p4`. Only the deliberate Step 6 program omits tunnel emission. No hop-limit field or assessed-assignment implementation has been added.

## Checks actually performed

- All four Python files parse successfully with Python's AST parser.
- All four staged P4 programs compiled with the course P4 compiler.
- Runtime experiments passed for ordinary IPv4, table deletion/restoration, the parser/deparser stage, tunnel-table forwarding and the deliberate deparser fault.
- Raw transcripts and host/switch logs are saved in `evidence/practical/`; all checks in `summary.json` are true. See RESULTS.md for interpretation.
- Final `tunnel.p4` is byte-for-byte equal to the successfully tested Step 5 version.
- Local documentation link targets exist.
- The staged source and documentation pass `git diff --check` with raw evidence excluded. Raw transcripts and switch logs retain their original trailing spaces.

## Execution and limitations

The official course image ran on local Docker Desktop (Linux x86_64), using a privileged temporary container with only week05 mounted as a workspace. An initial automatic approval block was resolved when the user explicitly approved running the course image and downloaded scripts.

The first runtime attempt exposed CRLF shell-script endings and is preserved in `evidence/practical-attempt01-crlf/`. After correction, the entire practical sequence passed. The containers were removed after execution.

No external GitHub repository/Codespace was created. Nested `week05/.github/` and `week05/.devcontainer/` preserve the template but are not root-level configuration for the parent coursework repository. LAB-ANSWERS.md contains the four practical wrap-up answers, included with the completed program and evidence in the local practical commit. No pushes, pull requests or submissions were made.
