<!-- visibility: internal-only; sanitized -->

# Current Handoff

## Objective and Git state

- Objective: deliver the `0.3.1` source/artifact release-governance hotfix after a prior tag proved that
  repository tests and public registry publication can have different outcomes.
- Branch: `hotfix/source-release-artifacts`, created cleanly from the then-latest `origin/main`.
- Active OpenSpec: `openspec/changes/source-release-artifacts/`.
- Protected state: the previous feature branch was clean and synchronized before switching. No stash,
  reset, clean, rewrite, merge, tag, public publication or deployment was performed.

## Release contract

- Every valid version tag runs the full test gate, then builds and retains Python sdist/wheel plus pi and
  dsh npm tarballs as GitLab artifacts without requiring registry credentials.
- Source/artifact release and public PyPI/npm publication are separate states. Artifact success never
  implies a public package exists.
- PyPI requires its explicit enable flag and protected credential. npm independently requires its enable
  flag and protected credential. Missing prerequisites end in a skipped public job, not a failed upload
  or a false published claim.
- Public jobs consume retained archives instead of rebuilding. pi stays on the stable npm tag; dsh stays
  experimental.
- Future OIDC/trusted publishing is preferred. No real credential, registry owner or account information
  is stored in this repository or its artifacts.

## TDD evidence

- CI/lifecycle RED: 3 failed / 7 passed because the baseline lacked a tag artifact job, public jobs were
  unconditional for tags, and Bun was asked to interpret shell build scripts.
- CI/lifecycle GREEN: 10 passed; both npm `prepublishOnly` dry-runs invoked Bash and completed without an
  upload.
- Version RED: Python 1 failed / 9 passed and TypeScript 1 failed while identities remained `0.3.0`.
- Version GREEN: release metadata plus Gateway capabilities 50 passed; TypeScript version test 1 passed
  after `0.3.1` propagation.
- Documentation RED: public-documentation suite 1 failed / 2 passed until this MR handoff document existed
  with the mandatory internal-only sanitized marker.

## Full verification

- Python: 233 passed / 1 opt-in real-provider test skipped.
- Bun: 39 passed / 153 assertions.
- TypeScript typecheck, pi/dsh builds and Python sdist/wheel build passed.
- Strict artifact audit produced two Python release archives and two npm tarballs at `0.3.1`.
- Extracted archives contain no credential/auth file, workstation path or workspace-only runtime
  dependency; tracked-publication scans remain value-redacted.

## Delivery state

- Conventional SDD, CI/lifecycle and version commits were pushed immediately to the hotfix branch.
- Final documentation and static publication scan passed. A Ready MR targets protected `main`; its first
  complete head pipeline succeeded without conflicts or auto-merge.
- Do not merge, tag, publish or deploy from this handoff.
