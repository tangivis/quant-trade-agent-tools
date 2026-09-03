from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RELEASE_VERSION = "0.4.0"
PUBLISHED_MANIFESTS = (
    ROOT / "package.json",
    ROOT / "packages/cli-bridge/package.json",
    ROOT / "packages/agent-tools-pi/package.json",
    ROOT / "packages/agent-tools-dsh/package.json",
)
SDIST_INCLUDE = [
    "/src/agent_tools",
    "/tests",
    "/LICENSE",
    "/README.md",
    "/ARCHITECTURE.md",
    "/SECURITY.md",
    "/CHANGELOG.md",
    "/openapi",
    "/pyproject.toml",
]


def ci_job(ci: str, name: str, *following_jobs: str) -> str:
    section = ci.split(f"{name}:\n", 1)[1]
    offsets = [section.find(f"\n{job}:\n") for job in following_jobs]
    boundaries = [offset for offset in offsets if offset >= 0]
    return section[: min(boundaries)] if boundaries else section


def load_pyproject() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_all_release_versions_are_synchronized() -> None:
    python_version = load_pyproject()["project"]["version"]
    versions = {
        json.loads(path.read_text())["version"] for path in PUBLISHED_MANIFESTS
    }
    assert python_version == EXPECTED_RELEASE_VERSION
    assert versions == {EXPECTED_RELEASE_VERSION}
    assert f'__version__ = "{EXPECTED_RELEASE_VERSION}"' in (
        ROOT / "src/agent_tools/__init__.py"
    ).read_text()
    assert f'version = "{EXPECTED_RELEASE_VERSION}"' in (ROOT / "uv.lock").read_text()
    assert (ROOT / "bun.lock").read_text().count(
        f'"version": "{EXPECTED_RELEASE_VERSION}"'
    ) == 3


def test_python_sdist_has_an_explicit_allowlist() -> None:
    config = load_pyproject()
    sdist = config["tool"]["hatch"]["build"]["targets"]["sdist"]
    assert sdist["include"] == SDIST_INCLUDE


def test_python_wheel_ships_the_producer_contract_snapshot() -> None:
    config = load_pyproject()
    wheel = config["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["force-include"] == {
        "openapi/agent-gateway-v1.json": "agent_tools/openapi/agent-gateway-v1.json"
    }


def test_release_inputs_do_not_contain_developer_home_paths() -> None:
    release_text = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "docs/migration-from-quant-trade.md",
        ROOT / "packages/agent-tools-pi/README.md",
        ROOT / "packages/agent-tools-dsh/README.md",
    ]
    local_home = re.compile(r"(?:/home|/Users)/[A-Za-z0-9._-]+/")
    offenders = [
        str(path.relative_to(ROOT))
        for path in release_text
        if local_home.search(path.read_text())
    ]
    assert offenders == []


def test_ci_builds_and_inspects_artifacts_before_publish() -> None:
    ci = (ROOT / ".gitlab-ci.yml").read_text()
    test_job = ci.split("agent-tools-python-publish:", 1)[0]
    assert 'UV_PYTHON: "3.14"' in ci
    assert ci.count("$(mise where bun)/bin") == ci.count("export PATH=")
    assert "uv build" in test_job
    assert test_job.count("npm pack --dry-run --json") == 2
    assert 'test "$CI_COMMIT_TAG" = "v$(uv version --short)"' in test_job


def test_tag_pipeline_retains_installable_source_release_artifacts() -> None:
    ci = (ROOT / ".gitlab-ci.yml").read_text()
    artifact_job = ci_job(
        ci,
        "source-release-artifacts",
        "agent-tools-python-publish",
        "agent-tools-npm-publish-pi",
        "agent-tools-npm-publish-dsh",
    )

    assert "  - package" in ci
    assert "stage: package" in artifact_job
    assert "uv build" in artifact_job
    assert artifact_job.count("npm pack --workspace") == 2
    assert "--pack-destination release-artifacts/npm" in artifact_job
    assert "artifacts:" in artifact_job
    assert "dist/*.tar.gz" in artifact_job
    assert "dist/*.whl" in artifact_job
    assert "release-artifacts/npm/*.tgz" in artifact_job
    assert "expire_in:" in artifact_job
    assert "CI_COMMIT_TAG =~ /^v" in artifact_job
    assert "PYPI_TOKEN" not in artifact_job
    assert "NPM_TOKEN" not in artifact_job


def test_public_registry_jobs_are_opt_in_and_consume_retained_artifacts() -> None:
    ci = (ROOT / ".gitlab-ci.yml").read_text()
    python_job = ci_job(
        ci,
        "agent-tools-python-publish",
        "agent-tools-npm-publish-pi",
        "agent-tools-npm-publish-dsh",
    )
    pi_job = ci_job(
        ci,
        "agent-tools-npm-publish-pi",
        "agent-tools-npm-publish-dsh",
    )
    dsh_job = ci_job(ci, "agent-tools-npm-publish-dsh")

    assert "ENABLE_PYPI_PUBLISH" in python_job
    assert "PYPI_TOKEN" in python_job
    assert any(
        "ENABLE_PYPI_PUBLISH" in line and "PYPI_TOKEN" in line and "&&" in line
        for line in python_job.splitlines()
    )
    assert "uv build" not in python_job
    assert "dist/*" in python_job
    assert "source-release-artifacts" in python_job
    assert "artifacts: true" in python_job
    assert "when: never" in python_job

    for job in (pi_job, dsh_job):
        assert "ENABLE_NPM_PUBLISH" in job
        assert "NPM_TOKEN" in job
        assert any(
            "ENABLE_NPM_PUBLISH" in line and "NPM_TOKEN" in line and "&&" in line
            for line in job.splitlines()
        )
        assert "source-release-artifacts" in job
        assert "artifacts: true" in job
        assert "npm pack" not in job
        assert "bun install" not in job
        assert "when: never" in job

    assert "release-artifacts/npm/quant-trade-agent-tools-pi-*.tgz" in pi_job
    assert "release-artifacts/npm/quant-trade-agent-tools-dsh-*.tgz" in dsh_job
    assert "--tag latest" in pi_job
    assert "--tag experimental" in dsh_job


def test_npm_prepublish_lifecycle_uses_a_shell_for_shell_scripts() -> None:
    for package_dir in ("agent-tools-pi", "agent-tools-dsh"):
        manifest = json.loads(
            (ROOT / "packages" / package_dir / "package.json").read_text()
        )
        assert manifest["scripts"]["build"] == "bash scripts/build.sh"
        assert manifest["scripts"]["prepublishOnly"] == "npm run build"


def test_dsh_tag_release_stays_experimental() -> None:
    ci = (ROOT / ".gitlab-ci.yml").read_text()
    dsh_job = ci.split("agent-tools-npm-publish-dsh:", 1)[1]
    assert "npm publish --access public --tag experimental" in dsh_job


def test_ci_npm_auth_uses_only_the_masked_environment_variable() -> None:
    npmrc = (ROOT / ".npmrc.ci").read_text().strip()
    assert npmrc == "//registry.npmjs.org/:_authToken=${NPM_TOKEN}"

    ci = (ROOT / ".gitlab-ci.yml").read_text()
    publish_jobs = ci.split("agent-tools-npm-publish-pi:", 1)[1]
    assert publish_jobs.count("NPM_CONFIG_USERCONFIG") == 2


def test_public_packages_point_to_public_source_and_current_tool_count() -> None:
    expected_repository = {
        "type": "git",
        "url": "git+https://github.com/tangivis/quant-trade-agent-tools.git",
    }
    for path in PUBLISHED_MANIFESTS:
        manifest = json.loads(path.read_text())
        assert manifest["repository"] == expected_repository
        assert manifest["homepage"] == (
            "https://tangivis.github.io/quant-trade-agent-tools/"
        )
        assert manifest["bugs"] == {
            "url": "https://github.com/tangivis/quant-trade-agent-tools/issues"
        }
    for path in (
        ROOT / "packages/agent-tools-pi/package.json",
        ROOT / "packages/agent-tools-dsh/package.json",
    ):
        description = json.loads(path.read_text())["description"]
        assert "12" in description
        assert "9" not in description


def test_ci_runs_python_lint_gate() -> None:
    ci = (ROOT / ".gitlab-ci.yml").read_text()
    assert "uv run ruff check src tests" in ci


def test_public_pull_requests_run_credential_free_release_gates() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()

    assert "permissions:\n  contents: read" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "RUN_REAL_PROVIDER_E2E" not in workflow
    assert "PYPI_TOKEN" not in workflow
    assert "NPM_TOKEN" not in workflow

    required_commands = (
        "uv sync --extra dev --locked",
        "uv run pytest tests/ -v",
        "uv run ruff check src tests",
        "bun install --frozen-lockfile",
        "bun test packages/",
        "bun run typecheck",
        "bun run build",
        "uv build",
        "npm pack --dry-run --json --workspace packages/agent-tools-pi",
        "npm pack --dry-run --json --workspace packages/agent-tools-dsh",
    )
    for command in required_commands:
        assert command in workflow

    action_uses = set(re.findall(r"uses:\s+([^\s#]+)", workflow))
    assert action_uses == {
        "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
        "actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444",
        "astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78",
        "oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6",
    }
    assert all(
        re.fullmatch(r"[^@]+@[0-9a-f]{40}", action_use)
        for action_use in action_uses
    )


def test_public_pages_deploys_only_the_curated_site() -> None:
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    site = (ROOT / "site/index.html").read_text()

    assert "push:" in workflow
    assert "      - main" in workflow
    assert "pull_request:" not in workflow
    assert "contents: read" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "path: site" in workflow
    assert "path: docs" not in workflow
    assert set(re.findall(r"uses:\s+([^\s#]+)", workflow)) == {
        "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
        "actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d",
        "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9",
        "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346",
    }
    assert "Intelligence Plane" in site
    assert "Product/Data/Domain Plane" in site
    assert "Install from PyPI" in site
    assert "0.4.0 released" in site
    assert "pending" not in site.lower()
    assert "release candidate" not in site.lower()
    assert "<script" not in site
    assert "docs/handoffs" not in site


def test_github_tag_release_retains_artifacts_and_gates_oidc_pypi() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text()

    assert "tags:" in workflow
    assert '      - "v*"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "release_tag:" in workflow
    assert "required: true" in workflow
    assert "RELEASE_TAG: ${{ inputs.release_tag || github.ref_name }}" in workflow
    assert "fetch-depth: 0" in workflow
    assert "ref: ${{ inputs.release_tag || github.ref }}" in workflow
    assert 'git fetch --no-tags origin main:refs/remotes/origin/main' in workflow
    assert (
        "git merge-base --is-ancestor HEAD refs/remotes/origin/main"
        in workflow
    )
    assert 'test "$RELEASE_TAG" = "v$(uv version --short)"' in workflow
    for command in (
        "uv sync --extra dev --locked",
        "uv run pytest tests/ -v",
        "uv run ruff check src tests",
        "bun install --frozen-lockfile",
        "bun test packages/",
        "bun run typecheck",
        "bun run build",
        "uv build",
        "npm pack --workspace packages/agent-tools-pi",
        "npm pack --workspace packages/agent-tools-dsh",
    ):
        assert command in workflow

    assert "name: source-release-artifacts" in workflow
    assert "dist/*.tar.gz" in workflow
    assert "dist/*.whl" in workflow
    assert "release-artifacts/npm/*.tgz" in workflow
    assert "sha256sum dist/*.tar.gz dist/*.whl release-artifacts/npm/*.tgz" in workflow
    assert "release-artifacts/SHA256SUMS" in workflow
    assert "gh release create" in workflow
    assert 'gh release view "$RELEASE_TAG" --repo "$GITHUB_REPOSITORY"' in workflow
    assert '--repo "$GITHUB_REPOSITORY"' in workflow
    assert "--clobber" not in workflow
    assert "contents: write" in workflow
    assert "vars.ENABLE_PYPI_PUBLISH == 'true'" in workflow
    assert "environment:\n      name: pypi" in workflow
    assert "id-token: write" in workflow
    assert "PYPI_TOKEN" not in workflow
    assert "password:" not in workflow
    assert set(re.findall(r"uses:\s+([^\s#]+)", workflow)) == {
        "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
        "astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78",
        "actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444",
        "oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6",
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
    }


def test_python_metadata_exposes_future_public_release_urls() -> None:
    urls = load_pyproject()["project"]["urls"]
    assert urls["Homepage"] == "https://tangivis.github.io/quant-trade-agent-tools/"
    assert urls["Documentation"] == (
        "https://tangivis.github.io/quant-trade-agent-tools/"
    )
    assert urls["PyPI"] == "https://pypi.org/project/quant-trade-agent-tools/"


def test_readme_declares_the_current_public_release_without_claiming_npm() -> None:
    readme = (ROOT / "README.md").read_text()

    assert "| 当前正式 release | `0.4.0` |" in readme
    assert "[PyPI](https://pypi.org/project/quant-trade-agent-tools/)" in readme
    assert "待 Trusted Publisher" not in readme
    assert "尚未 tag、publish 或 deploy" not in readme
    assert "npm packages 尚未公开发布" in readme
