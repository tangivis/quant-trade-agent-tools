# Source release artifacts

## Problem

The `0.3.0` tag pipeline proved that tests can pass while public registry publication fails for reasons
outside the source tree: no PyPI credential was configured and the npm scope was not publishable by the
runner identity. The same pipeline did not provide an independent, durable source/artifact release state,
so consumers could not retrieve the already buildable Python and harness archives from GitLab.

The npm package lifecycle also invokes a shell build script through Bun. During `prepublishOnly`, Bun tries
to interpret the shell builtin `set` as a command, which prevents otherwise valid tarballs from being made.

## Proposed change

- Bump all synchronized package and runtime identities to `0.3.1`.
- Add a tag-only artifact job that always builds Python sdist/wheel plus pi and dsh npm tarballs after the
  full test gate, and retains them as GitLab artifacts without registry credentials.
- Make PyPI and npm publication opt-in. A public registry job can run only when its explicit enable flag
  and its corresponding credential are both present; otherwise it is skipped and no published claim is
  made.
- Fix npm lifecycle builds so shell scripts are executed by a shell, including `prepublishOnly` package
  creation.
- Document source/artifact release and public registry publication as separate, independently observable
  states. Recommend protected variables or registry-supported OIDC/trusted publishing for future rollout.

## Out of scope

- Creating a tag, publishing a package, deploying a service, or merging this hotfix.
- Recording a real token, account, scope owner, private registry, or runner-specific secret.
- Changing tool contracts, product APIs, harness stability labels, or trading boundaries.

## Acceptance criteria

- Static CI contracts fail on the old pipeline and pass only when tag artifacts are retained and public
  publication is fail-closed behind explicit enable-plus-credential rules.
- A package lifecycle test fails on the old Bun/shell invocation and passes when both npm tarballs build.
- Python, runtime, npm manifests, and locks report `0.3.1`.
- Full Python/TypeScript tests, typecheck, builds, artifact inspection, and security audits pass.
