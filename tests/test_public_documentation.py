from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[1]
REQUIRED_PUBLIC_DOCS = {
    "README.md": (
        "Intelligence Plane",
        "Product/Data/Domain Plane",
        "ARCHITECTURE.md",
        "SECURITY.md",
    ),
    "ARCHITECTURE.md": (
        "Intelligence Plane",
        "Product/Data/Domain Plane",
        "REST",
        "MCP",
        "Trust boundaries",
    ),
    "SECURITY.md": (
        "Security model",
        "Privacy",
        "Credential",
        "Vulnerability reporting",
    ),
}
INTERNAL_EXECUTION_DOCS = (
    "docs/handoffs/CURRENT.md",
    "docs/agent-tools-verification.md",
    "docs/mr/2026-09-01-contract-v1-intelligence-producers.md",
    "docs/mr/2026-09-02-multi-symbol-backtest-tools.md",
    "docs/mr/2026-09-02-source-release-artifacts.md",
)
INTERNAL_MARKER = "<!-- visibility: internal-only; sanitized -->"

FORBIDDEN_PATTERNS = {
    "developer_home_path": re.compile(
        r"(?<![\w.])/(?:home|Users|tmp)/[^\s)`>]+"
    ),
    "private_repository_host": re.compile(
        r"(?:ssh://[^\s)`>]+|\b[a-z0-9.-]+\.(?:internal|local|lan)\b)",
        re.IGNORECASE,
    ),
    "private_network_address": re.compile(
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
    ),
    "environment_project_id": re.compile(
        r"(?:\b(?:gitlab\s+)?project(?:\s+id)?\s*[:#]?\s*\d+\b|项目\s*\d+|\bIID\s*\d+\b)",
        re.IGNORECASE,
    ),
    "internal_commit_hash": re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE),
    "live_provider_model_configuration": re.compile(
        r"\b(?:LLM_MODEL|REAL_PROVIDER_E2E_PROVIDER)\s*=\s*"
        r"(?!<(?:provider|model)>|redacted|configured)[^\s\\]+",
        re.IGNORECASE,
    ),
    "credential_value_example": re.compile(
        r"\b(?:[A-Z0-9_]*(?:API_KEY|TOKEN))\s*=\s*(?:\.\.\.|replace-[^\s\\]+)",
        re.IGNORECASE,
    ),
    "token_like_secret": re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{12,}|glpat-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{20,})\b"
    ),
}
ALLOWED_PUBLIC_URL_HOSTS = {"127.0.0.1", "docs.pytest.org", "github.com"}
HTTP_URL = re.compile(r"https?://[^\s)`>]+", re.IGNORECASE)


def publication_text_files() -> list[Path]:
    paths = set(ROOT.glob("*.md"))
    paths.update(ROOT.glob("docs/**/*.md"))
    paths.update(ROOT.glob("openspec/**/*.md"))
    paths.update(ROOT.glob("packages/**/README.md"))
    paths.add(ROOT / "pyproject.toml")
    paths.add(ROOT / "package.json")
    paths.update(ROOT.glob("packages/*/package.json"))
    return sorted(path for path in paths if path.is_file())


def test_required_public_documents_define_canonical_boundaries() -> None:
    for relative_path, required_phrases in REQUIRED_PUBLIC_DOCS.items():
        path = ROOT / relative_path
        assert path.is_file(), f"missing public document: {relative_path}"
        text = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, f"{relative_path}: missing required public section"


def test_execution_history_documents_are_marked_internal_and_sanitized() -> None:
    for relative_path in INTERNAL_EXECUTION_DOCS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert text.startswith(INTERNAL_MARKER), (
            f"{relative_path}: missing internal-only sanitized marker"
        )


def test_repository_publication_text_has_no_sensitive_identifiers() -> None:
    failures: list[str] = []
    for path in publication_text_files():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        for rule, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{relative}: {rule}")
        for match in HTTP_URL.finditer(text):
            hostname = urlsplit(match.group(0)).hostname
            if hostname not in ALLOWED_PUBLIC_URL_HOSTS:
                failures.append(f"{relative}: external_url_not_allowlisted")

    assert failures == [], "publication safety violations:\n" + "\n".join(failures)
