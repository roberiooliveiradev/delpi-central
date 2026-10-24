"""Deterministic DAVI governed-knowledge bundle builder (provider-neutral).

TASK: DAVI-GOVERNED-KNOWLEDGE-RUNTIME-IMPLEMENTATION-001

Produces a derived corpus for Workspace Agent Files upload. Governance
authority: the freeze artifact owns corpus membership; the pinned manifest
owns content hashes. This module never uploads, never calls provider APIs,
never mutates source documents, and never touches network.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

CORPUS_ID = "davi-governed-knowledge"
CORPUS_VERSION = 1
PUBLISHED_V1_MANIFEST_IDENTITY = "b830a6a979a27bdbf1845d4e7128cc00aaa2fe75d2b095cbdb4af56b79449f49"

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent

FREEZE_ARTIFACT = (
    "api-delpi/docs/integrations/evidence/davi-governed-knowledge-freeze-001.md"
)
FREEZE_SHA = "d9926cc14a8a4edd1b52775b82cf7353aede75b4"
MANIFEST_REPO_PATH = (
    "api-delpi/docs/integrations/evidence/davi-governed-knowledge-manifest-v1.json"
)
OUTPUT_DIR = API_ROOT / "dist" / "davi-governed-knowledge" / "v1"
TOPIC_INDEX_REPO_PATH = (
    "api-delpi/docs/integrations/evidence/davi-governed-knowledge-topics-v1.json"
)
TOPIC_INDEX_FILENAME = "DAVI-topic-index.md"
TOPIC_INDEX_SCHEMA = "davi-governed-knowledge-topics-v1"

_DOC_PREFIX = "api-delpi/"
_CORPUS_SECTION = "## FROZEN_FIRST_CORPUS"
_CORPUS_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class BundleError(RuntimeError):
    """Fail-closed corpus validation/build error."""


def resolve_source_path(rel: str, repo_root: Path = REPO_ROOT) -> Path:
    """Resolve a repo-relative doc path in monorepo or flat (container) layout."""
    rooted = repo_root / rel
    if rooted.exists():
        return rooted
    if rel.startswith(_DOC_PREFIX):
        return API_ROOT / rel[len(_DOC_PREFIX):]
    return rooted


def _parse_corpus_paths(text: str) -> list[str]:
    """Corpus membership parser over freeze artifact text."""
    if _CORPUS_SECTION not in text:
        raise BundleError("freeze artifact lacks FROZEN_FIRST_CORPUS section")
    section = text.split(_CORPUS_SECTION, 1)[1]
    end = section.find("\n## ")
    if end > 0:
        section = section[:end]
    paths = _CORPUS_ROW.findall(section)
    if len(set(paths)) != len(paths):
        raise BundleError("freeze artifact contains duplicate corpus paths")
    return paths


def frozen_corpus_paths(repo_root: Path = REPO_ROOT) -> list[str]:
    """Corpus membership authority: parse the current freeze artifact."""
    text = resolve_source_path(FREEZE_ARTIFACT, repo_root).read_text(
        encoding="utf-8"
    )
    return _parse_corpus_paths(text)


def _git_show_blob(sha: str, repo_rel: str, repo_root: Path) -> bytes:
    """Read blob <sha>:<repo_rel> via local git (monorepo or flat layout)."""
    candidates = [repo_rel]
    if repo_rel.startswith(_DOC_PREFIX):
        candidates.append(repo_rel[len(_DOC_PREFIX):])
    error = ""
    for rel in candidates:
        result = subprocess.run(
            ["git", "show", f"{sha}:{rel}"],
            cwd=repo_root,
            capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout
        error = result.stderr.decode("utf-8", "replace").strip()
    raise BundleError(f"git object not found at {sha}: {repo_rel} ({error})")


def _git_ref_resolvable(sha: str, repo_root: Path) -> bool:
    """True when <sha> resolves to a commit in the local repository."""
    if not _GIT_SHA_RE.match(sha):
        return False
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
        ).returncode
        == 0
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_git_sha(repo_root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _manifest_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    """Content-identity subset of a manifest (excludes generated metadata)."""
    return {
        "corpus_id": manifest["corpus_id"],
        "corpus_version": manifest["corpus_version"],
        "source_git_sha": manifest["source_git_sha"],
        "freeze_artifact": manifest["freeze_artifact"],
        "freeze_sha": manifest["freeze_sha"],
        "documents": manifest["documents"],
    }


def manifest_sha256(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(
        _manifest_identity(manifest), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def emit_manifest(
    *,
    generated_at: str,
    repo_root: Path = REPO_ROOT,
    source_git_sha: str | None = None,
) -> dict[str, Any]:
    """Derive the pinned manifest from the freeze artifact corpus."""
    paths = frozen_corpus_paths(repo_root)
    documents: list[dict[str, str]] = []
    for rel in paths:
        src = resolve_source_path(rel, repo_root)
        if not src.is_file():
            raise BundleError(f"corpus source missing: {rel}")
        documents.append({"path": rel, "sha256": sha256_file(src)})
    manifest: dict[str, Any] = {
        "corpus_id": CORPUS_ID,
        "corpus_version": CORPUS_VERSION,
        "source_git_sha": source_git_sha or current_git_sha(repo_root),
        "freeze_artifact": FREEZE_ARTIFACT,
        "freeze_sha": FREEZE_SHA,
        "generated_at": generated_at,
        "documents": documents,
    }
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def _provenance_header(doc: dict[str, str], manifest: dict[str, Any]) -> str:
    return (
        "DAVI GOVERNED KNOWLEDGE\n"
        f"corpus_id: {manifest['corpus_id']}\n"
        f"corpus_version: {manifest['corpus_version']}\n"
        f"source_path: {doc['path']}\n"
        f"source_git_sha: {manifest['source_git_sha']}\n"
        f"source_sha256: {doc['sha256']}\n"
        "\n---\n\n"
    )


def _manifest_schema(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Step 1 — schema/basic fields; returns the document list."""
    if manifest.get("corpus_id") != CORPUS_ID:
        raise BundleError("manifest corpus_id mismatch")
    if manifest.get("corpus_version") != CORPUS_VERSION:
        raise BundleError("manifest corpus_version mismatch")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise BundleError("manifest has no documents")
    paths = [d.get("path") for d in documents]
    if any(not p for p in paths):
        raise BundleError("manifest document missing path")
    if len(set(paths)) != len(paths):
        raise BundleError("manifest contains duplicate source paths")
    names = [Path(p).name for p in paths]
    if len(set(names)) != len(names):
        raise BundleError("duplicate output filename in corpus")
    return documents


def verify_manifest(
    manifest: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    blob_reader=None,
    ref_resolver=None,
) -> dict[str, Any]:
    """Fail-closed integrity verification of the pinned manifest.

    Proves, in order:

    1. manifest schema/basic fields
    2. manifest_sha256 (identity over content fields)
    3. corpus membership at pinned freeze_sha
    4. current freeze membership == pinned membership
    5. source_git_sha resolves to a local commit
    6. document hashes at source_git_sha
    7. current working-tree source hashes

    Returns concise evidence on PASS. Never regenerates hashes.
    """
    documents = _manifest_schema(manifest)
    if manifest.get("manifest_sha256") != manifest_sha256(manifest):
        raise BundleError("manifest_sha256 mismatch: manifest is stale or tampered")

    reader = blob_reader or (
        lambda sha, rel: _git_show_blob(sha, rel, repo_root)
    )
    resolver = ref_resolver or (
        lambda sha: _git_ref_resolvable(sha, repo_root)
    )

    freeze_sha = str(manifest.get("freeze_sha") or "")
    if not _GIT_SHA_RE.match(freeze_sha):
        raise BundleError("freeze_sha is not a full git SHA")
    if not resolver(freeze_sha):
        raise BundleError(f"freeze_sha does not resolve: {freeze_sha}")
    freeze_text = reader(freeze_sha, FREEZE_ARTIFACT).decode("utf-8")
    pinned = set(_parse_corpus_paths(freeze_text))
    manifest_set = {d["path"] for d in documents}
    extra = manifest_set - pinned
    missing = pinned - manifest_set
    if extra:
        raise BundleError(f"unapproved path in manifest: {sorted(extra)}")
    if missing:
        raise BundleError(f"expected corpus member missing: {sorted(missing)}")

    current = set(frozen_corpus_paths(repo_root))
    if current != pinned:
        raise BundleError(
            "current freeze membership diverges from pinned freeze_sha"
        )

    source_git_sha = str(manifest.get("source_git_sha") or "")
    if not _GIT_SHA_RE.match(source_git_sha):
        raise BundleError("source_git_sha is not a full git SHA")
    if not resolver(source_git_sha):
        raise BundleError(f"source_git_sha does not resolve: {source_git_sha}")
    for doc in documents:
        blob = reader(source_git_sha, doc["path"])
        if hashlib.sha256(blob).hexdigest() != doc["sha256"]:
            raise BundleError(
                f"pinned source hash mismatch at {source_git_sha}: {doc['path']}"
            )

    for doc in documents:
        rel = doc["path"]
        src = resolve_source_path(rel, repo_root)
        if not src.is_file():
            raise BundleError(f"corpus source missing: {rel}")
        if sha256_file(src) != doc["sha256"]:
            raise BundleError(f"current source hash mismatch: {rel}")

    return {
        "corpus_id": manifest["corpus_id"],
        "corpus_version": manifest["corpus_version"],
        "documents": len(documents),
        "freeze_sha": freeze_sha,
        "source_git_sha": source_git_sha,
        "manifest_sha256": manifest["manifest_sha256"],
    }



def load_topic_index(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load curated source pointers; this catalog is not domain authority."""
    path = resolve_source_path(TOPIC_INDEX_REPO_PATH, repo_root)
    if not path.is_file():
        raise BundleError(f"topic index missing: {TOPIC_INDEX_REPO_PATH}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise BundleError("topic index invalid JSON") from exc
    if not isinstance(value, dict):
        raise BundleError("topic index must be an object")
    return value


def verify_topic_index(
    topic_index: dict[str, Any], manifest: dict[str, Any], *,
    repo_root: Path = REPO_ROOT,
    source_exists=None,
) -> dict[str, Any]:
    """Reject undocumented source promotion, alias injection, and stale freezes."""
    if topic_index.get("schema_version") != TOPIC_INDEX_SCHEMA:
        raise BundleError("topic index schema mismatch")
    if topic_index.get("corpus_id") != manifest.get("corpus_id"):
        raise BundleError("topic index corpus_id mismatch")
    if topic_index.get("corpus_version") != manifest.get("corpus_version"):
        raise BundleError("topic index corpus_version mismatch")
    if topic_index.get("freeze_sha") != manifest.get("freeze_sha"):
        raise BundleError("topic index freeze_sha mismatch")
    if topic_index.get("authority") != "GUIDANCE_NOT_DOMAIN_TRUTH":
        raise BundleError("topic index cannot claim business/domain authority")
    approved = {doc["path"] for doc in _manifest_schema(manifest)}
    topics = topic_index.get("topics")
    if not isinstance(topics, list) or len(topics) != len(approved):
        raise BundleError("topic index membership/cardinality mismatch")
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise BundleError("topic entry must be an object")
        identity = topic.get("id")
        path = topic.get("source_path")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", identity):
            raise BundleError("invalid topic id")
        if identity in seen_ids or path in seen_paths:
            raise BundleError("duplicate knowledge topic id/source")
        seen_ids.add(identity)
        seen_paths.add(path)
        if topic.get("status") != "FROZEN_V1":
            raise BundleError("unapproved topic status")
        if topic.get("intent") != "CONCEPTUAL_GUIDANCE_ONLY":
            raise BundleError("knowledge topic cannot authorize live data")
        title, aliases = topic.get("title"), topic.get("aliases")
        if not isinstance(title, str) or not title.strip():
            raise BundleError("topic title missing")
        if not isinstance(aliases, list) or not (1 <= len(aliases) <= 12):
            raise BundleError("topic aliases missing/out of bounds")
        if any(
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 120
            or any(c in value for c in ("\n", "\r", "|", "<", ">"))
            for value in [title, *aliases]
        ):
            raise BundleError("unsafe topic title/alias")
        if len({value.casefold().strip() for value in aliases}) != len(aliases):
            raise BundleError("duplicate aliases in topic")
        if path not in approved:
            raise BundleError(f"unapproved topic source: {path}")
    if seen_paths != approved:
        raise BundleError("topic index missing frozen sources")
    deferred = topic_index.get("deferred_sources")
    if not isinstance(deferred, list):
        raise BundleError("topic index deferred_sources missing")
    deferred_ids: set[str] = set()
    for candidate in deferred:
        if not isinstance(candidate, dict):
            raise BundleError("invalid deferred source")
        identity, path = candidate.get("id"), candidate.get("source_path")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", identity):
            raise BundleError("invalid deferred source id")
        if identity in deferred_ids or identity in seen_ids:
            raise BundleError("duplicate deferred source id")
        deferred_ids.add(identity)
        if not isinstance(path, str) or not path.startswith("api-delpi/docs/api/"):
            raise BundleError("invalid deferred source path")
        if path in approved or path in seen_paths:
            raise BundleError("deferred source cannot be promoted silently")
        if candidate.get("status") != "TO_INVENTORY":
            raise BundleError("deferred source is not approved")
        if candidate.get("authority") != "EXTERNAL_VENDOR_REFERENCE_NOT_HOMOLOGATED_AT_DELPI":
            raise BundleError("deferred source authority mismatch")
        exists = source_exists(path) if source_exists else resolve_source_path(path, repo_root).is_file()
        if not exists:
            raise BundleError(f"deferred source missing: {path}")
    return {"topics": len(topics), "deferred_sources": len(deferred)}


def _published_bytes(api_root: Path, source_path: str) -> bytes:
    relative = Path(source_path)
    if relative.is_absolute() or ".." in relative.parts or not source_path.startswith("api-delpi/docs/"):
        raise BundleError("Invalid published source")
    target = api_root / source_path.removeprefix("api-delpi/")
    if any(part.is_symlink() for part in (target, *target.parents)):
        raise BundleError("Symlinked published source")
    if not target.resolve().is_relative_to(api_root.resolve()):
        raise BundleError("Published source escapes corpus")
    with target.open("rb") as source:
        content = source.read(262145)
    if len(content) > 262144:
        raise BundleError("Published source exceeds size limit")
    return content


def read_published_corpus(*, api_root: Path = API_ROOT) -> tuple[dict, dict, dict[str, bytes]]:
    manifest = json.loads(_published_bytes(api_root, MANIFEST_REPO_PATH))
    documents = _manifest_schema(manifest)
    if manifest.get("manifest_sha256") != manifest_sha256(manifest) or manifest["manifest_sha256"] != PUBLISHED_V1_MANIFEST_IDENTITY:
        raise BundleError("Published manifest identity mismatch")
    if manifest.get("freeze_sha") != FREEZE_SHA or not _GIT_SHA_RE.fullmatch(str(manifest.get("source_git_sha", ""))):
        raise BundleError("Published source version mismatch")
    membership = _parse_corpus_paths(_published_bytes(api_root, FREEZE_ARTIFACT).decode("utf-8"))
    if len(documents) != 15 or {doc["path"] for doc in documents} != set(membership):
        raise BundleError("Published membership mismatch")
    index = json.loads(_published_bytes(api_root, TOPIC_INDEX_REPO_PATH))
    verify_topic_index(index, manifest, source_exists=lambda path: bool(_published_bytes(api_root, path)))
    content = {}
    for doc in documents:
        if not doc["path"].startswith("api-delpi/docs/api/"):
            raise BundleError("Unapproved published document")
        raw = _published_bytes(api_root, doc["path"])
        if hashlib.sha256(raw).hexdigest() != doc["sha256"]:
            raise BundleError("Published document hash mismatch")
        raw.decode("utf-8")
        content[doc["path"]] = raw
    return manifest, index, content


def render_topic_index(topic_index: dict[str, Any], manifest: dict[str, Any]) -> bytes:
    """Only approved source metadata; excludes every deferred title and path."""
    hashes = {doc["path"]: doc["sha256"] for doc in manifest["documents"]}
    lines = [
        "# DAVI — Índice de conhecimento governado (derivado)",
        "",
        "> Índice de localização do corpus aprovado, NÃO fonte de dados operacionais.",
        "> Arquivos não aprovados não são carregados. Nenhum item autoriza negócio.",
        "> Para valores atuais, usar READ autenticado sujeito à AuthZ do backend.",
        "",
        f"corpus_id: {manifest['corpus_id']}",
        f"corpus_version: {manifest['corpus_version']}",
        f"freeze_sha: {manifest['freeze_sha']}",
        f"source_git_sha: {manifest['source_git_sha']}",
        f"manifest_sha256: {manifest['manifest_sha256']}",
        "",
        "## Tópicos e origens aprovados",
        "",
    ]
    for topic in topic_index["topics"]:
        path = topic["source_path"]
        lines.extend([
            f"### {topic['title']}",
            f"topic_id: {topic['id']}",
            f"source_path: {path}",
            f"source_sha256: {hashes[path]}",
            f"sinônimos: {', '.join(topic['aliases'])}",
            "status: FROZEN_V1 / CONCEPTUAL_GUIDANCE_ONLY",
            "",
        ])
    lines.extend([
        "## Limites",
        "",
        "- Conferir trecho no documento original antes de responder conceitos.",
        "- Não usar conhecimento estático como dados operacionais atuais.",
        "- Não ampliar tools, campos, contas nem permissões por este índice.",
        "- Fontes pendentes não fazem parte desta versão distribuível.",
        "",
    ])
    return "\n".join(lines).encode("utf-8")


def build_bundle(
    manifest: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = OUTPUT_DIR,
    blob_reader=None,
    ref_resolver=None,
) -> list[Path]:
    """Verify the pinned manifest (full path) and emit derived files.

    Impossible to build from a manifest that would fail ``verify_manifest``.
    No network, no provider calls, no source mutation.
    """
    verify_manifest(
        manifest,
        repo_root=repo_root,
        blob_reader=blob_reader,
        ref_resolver=ref_resolver,
    )
    topic_index = load_topic_index(repo_root)
    verify_topic_index(topic_index, manifest, repo_root=repo_root)
    outputs: list[tuple[Path, bytes]] = []
    for doc in manifest["documents"]:
        rel = doc["path"]
        src = resolve_source_path(rel, repo_root)
        content = _provenance_header(doc, manifest).encode("utf-8") + src.read_bytes()
        outputs.append((output_dir / Path(rel).name, content))
    # Derived search metadata, not a new source document.
    outputs.append(
        (output_dir / TOPIC_INDEX_FILENAME, render_topic_index(topic_index, manifest))
    )
    # Refuse stale or symlinked generated files; never silently publish
    # an old/deferred source from a previous local Files build.
    expected_names = {path.name for path, _ in outputs} | {"manifest.json"}
    if output_dir.is_symlink():
        raise BundleError("unsafe symlinked bundle directory")
    if output_dir.exists():
        if not output_dir.is_dir():
            raise BundleError("bundle output path is not a directory")
        unexpected = {path.name for path in output_dir.iterdir()} - expected_names
        if unexpected:
            raise BundleError(f"unexpected files in bundle output: {sorted(unexpected)}")
        if any((output_dir / name).is_symlink() for name in expected_names):
            raise BundleError("unsafe symlink in bundle output")
    output_dir.mkdir(parents=True, exist_ok=True)
    written = [path for path, content in outputs if _write(path, content)]
    manifest_out = output_dir / "manifest.json"
    _write(
        manifest_out,
        (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    )
    written.append(manifest_out)
    if {path.name for path in output_dir.iterdir()} != expected_names:
        raise BundleError("generated bundle membership mismatch")
    return written


def _write(path: Path, content: bytes) -> bool:
    path.write_bytes(content)
    return True
