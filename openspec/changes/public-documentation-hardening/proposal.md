# Proposal: Public Documentation Hardening

## Problem

The repository needs public-grade documentation that explains its relationship with the independent
product repository without exposing deployment details, private repository coordinates, local machine
identity, project identifiers, live model configuration or credentials. Existing documentation grew
as implementation handoffs and mixes stable architecture with environment-specific evidence.

## Scope

- Add root `ARCHITECTURE.md` and `SECURITY.md` as the canonical public architecture and security entry
  points.
- Align README, CHANGELOG, current handoff and MR draft with the two-plane ownership contract.
- Mark execution-only handoff/MR/verification documents as internal-only and sanitized.
- Remove environment-specific identifiers and live provider/model evidence from repository docs and
  public package metadata.
- Add an executable publication-safety test that scans documentation and release metadata.

## Non-goals

- No runtime API, provider, model, prompt or orchestration behavior change.
- No sibling repository read or write.
- No GitLab project, issue, MR, branch, release or deployment mutation.
- No claim that the Intelligence Plane owns product data, deterministic domain logic or execution.

## Acceptance

- Public docs clearly define Intelligence Plane versus Product/Data/Domain Plane ownership and their
  peer service relationship.
- REST is the product boundary; MCP/CLI/harness adapters are Intelligence Plane interfaces.
- Security/privacy docs state data minimization, credential ownership, logging/redaction, no database,
  repository, GitLab or trading mutation, and a vulnerability reporting process.
- Automated tests fail on local absolute paths, private repository hosts, environment project IDs,
  exact internal commit identifiers, known live model evidence or token-like secrets.
- Root public docs contain no internal host/IP, username, absolute machine path, project identifier,
  live model configuration or real credential example.
- Full repository tests and builds remain green.
