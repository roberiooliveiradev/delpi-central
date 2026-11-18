#!/usr/bin/env python3
"""Deterministic compilation-package generator for the protheus-advpl workspace.

Reads module content exclusively from an approved git commit (never from the
working tree), validates module manifests, hashes every file, produces a
consolidated manifest.json and a byte-reproducible ZIP.

No ERP connectivity, no ADVPL execution, no RPO interaction.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import PurePosixPath

try:
    import jsonschema
    import yaml
except ImportError as exc:  # pragma: no cover
    sys.exit(f"missing dependency: {exc} (pyyaml + jsonschema required)")

WORKSPACE = "api-delpi/integrations/protheus-advpl"
MODULES_DIR = f"{WORKSPACE}/modules"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "manifest.schema.json")
SOURCE_EXTENSIONS = (".prw", ".tlpp")
ALLOWED_KINDS = {"source", "contract", "doc"}
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
FORBIDDEN_PATTERNS = (
    ".env", ".env.*", "*.env", "*.key", "*.pem", "*.pfx", "*.p12",
    "*secret*", "*credential*", "*token*", "*password*", "*passwd*",
)


class PackageError(Exception):
    """Deterministic packaging failure (validation, safety or integrity)."""


def _git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise PackageError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def resolve_commit(repo: str, ref: str) -> str:
    out = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    if not out:
        raise PackageError(f"cannot resolve commit: {ref}")
    return out


def commit_timestamp(repo: str, commit: str) -> str:
    return _git(repo, "show", "-s", "--format=%cI", commit).strip()


def list_tree(repo: str, commit: str, path: str) -> dict[str, tuple[str, str]]:
    """Return {repo_path: (mode, type)} for files under path at commit."""
    out = _git(repo, "ls-tree", "-r", commit, "--", path)
    entries: dict[str, tuple[str, str]] = {}
    for line in out.splitlines():
        meta, _, rel = line.partition("\t")
        mode, obj_type, _sha = meta.split()
        entries[rel] = (mode, obj_type)
    return entries


def read_blob(repo: str, commit: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", repo, "show", f"{commit}:{path}"],
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise PackageError(f"cannot read {path} at {commit}")
    return proc.stdout


def validate_relpath(rel: str) -> None:
    p = PurePosixPath(rel)
    if rel.startswith(("/", "~")) or "\\" in rel or ".." in p.parts or not rel:
        raise PackageError(f"unsafe path: {rel!r}")


def check_forbidden(rel: str) -> None:
    base = PurePosixPath(rel).name.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if fnmatch.fnmatch(base, pattern.lower()):
            raise PackageError(f"forbidden file in package: {rel}")


def load_module_manifest(repo: str, commit: str, module_id: str) -> dict:
    mpath = f"{MODULES_DIR}/{module_id}/contracts/module.yaml"
    try:
        raw = read_blob(repo, commit, mpath)
    except PackageError:
        raise PackageError(f"module not found at commit: {module_id}")
    try:
        manifest = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise PackageError(f"invalid module.yaml for {module_id}: {exc}")
    if not isinstance(manifest, dict):
        raise PackageError(f"module.yaml is not a mapping: {module_id}")
    for key in ("module_id", "package_tag", "name", "owners", "sources"):
        if key not in manifest:
            raise PackageError(f"module.yaml missing required key {key!r}: {module_id}")
    if manifest["module_id"] != module_id:
        raise PackageError(
            f"module_id mismatch: dir {module_id} vs yaml {manifest['module_id']}"
        )
    if not isinstance(manifest["sources"], list):
        raise PackageError(f"sources must be a list: {module_id}")
    return manifest


def collect_module_files(repo: str, commit: str, module_id: str, manifest: dict) -> list[dict]:
    base = f"{MODULES_DIR}/{module_id}"
    tree = list_tree(repo, commit, base)
    files: list[dict] = []
    declared: set[str] = set()

    for rel in manifest["sources"]:
        validate_relpath(str(rel))
        full = f"{base}/src/{rel}"
        declared.add(full)
        if full not in tree:
            raise PackageError(f"declared source missing at commit: {full}")
        files.append({"path": full, "module_id": module_id, "artifact_type": "source",
                      "source_origin": "delpi-central"})

    for path, (mode, obj_type) in sorted(tree.items()):
        if mode == "120000" or obj_type == "commit":
            raise PackageError(f"symlink/submodule not allowed in package: {path}")
        if obj_type != "blob":
            continue
        rel = path[len(base) + 1:]
        check_forbidden(rel)
        in_src = rel.startswith("src/")
        ext = os.path.splitext(rel)[1].lower()
        if in_src and ext in SOURCE_EXTENSIONS and path not in declared:
            raise PackageError(f"undeclared source file: {path}")
        if in_src:
            continue  # sources already collected via declaration
        if rel.startswith("contracts/"):
            kind = "contract"
        elif ext in (".md", ".txt"):
            kind = "doc"
        else:
            raise PackageError(f"file type not allowed in package: {path}")
        files.append({"path": path, "module_id": module_id,
                      "artifact_type": kind, "source_origin": "delpi-central"})
    return files


def build_manifest(repo: str, commit: str, module_ids: list[str],
                   version: str, target_env: str, status: str) -> tuple[dict, dict[str, bytes]]:
    files_meta: list[dict] = []
    contents: dict[str, bytes] = {}
    modules_meta: list[dict] = []

    for module_id in module_ids:
        manifest = load_module_manifest(repo, commit, module_id)
        entries = collect_module_files(repo, commit, module_id, manifest)
        modules_meta.append({
            "module_id": module_id,
            "package_tag": manifest["package_tag"],
            "development_status": manifest.get("development_status", "PLANNED"),
            "source_count": sum(1 for e in entries if e["artifact_type"] == "source"),
        })
        files_meta.extend(entries)

    for entry in files_meta:
        data = read_blob(repo, commit, entry["path"])
        contents[entry["path"]] = data
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        entry["size_bytes"] = len(data)

    tags = sorted({m["package_tag"] for m in modules_meta})
    env_tag = (target_env or "UNSET").upper()
    package_id = f"DELPI-ADVPL-{'-'.join(tags) or 'EMPTY'}-{env_tag}-v{version}"

    manifest = {
        "package_id": package_id,
        "package_version": version,
        "status": status,
        "target_environment": target_env,
        "created_at": commit_timestamp(repo, commit),
        "source_repository": "roberiooliveiradev/delpi-central",
        "source_commit": commit,
        "modules": modules_meta,
        "files": files_meta,
        "dependencies": [],
        "contracts": [
            {"module_id": m["module_id"],
             "path": f"{MODULES_DIR}/{m['module_id']}/contracts/module.yaml"}
            for m in modules_meta
        ],
        "approval_status": "PENDING",
        "compilation_status": "COMPILATION_PENDING",
        "validation_status": "TEST_NOT_RUN",
    }
    return manifest, contents


def validate_manifest(manifest: dict, schema_path: str = SCHEMA_PATH) -> None:
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    jsonschema.validate(manifest, schema)


def render_zip(manifest: dict, contents: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zf:
        entries = {"manifest.json": json.dumps(manifest, indent=2,
                                               sort_keys=True).encode("utf-8")}
        entries.update(contents)
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o644 << 16
            zf.writestr(info, entries[name])
    return buf.getvalue()


def verify_package(zip_path: str) -> dict:
    """Re-hash every archived file against the embedded manifest."""
    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        validate_manifest(manifest)
        for entry in manifest["files"]:
            data = zf.read(entry["path"])
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["sha256"]:
                raise PackageError(
                    f"hash mismatch for {entry['path']}: "
                    f"manifest {entry['sha256'][:12]}… vs archive {digest[:12]}…"
                )
    return manifest


def build_package(repo: str, ref: str, module_ids: list[str], version: str,
                  target_env: str, out_dir: str,
                  status: str = "SOURCE_CANDIDATE") -> dict:
    commit = resolve_commit(repo, ref)
    manifest, contents = build_manifest(repo, commit, module_ids, version,
                                        target_env, status)
    validate_manifest(manifest)
    blob = render_zip(manifest, contents)
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, f"{manifest['package_id']}.zip")
    manifest_path = zip_path[: -len(".zip")] + ".manifest.json"
    with open(zip_path, "wb") as fh:
        fh.write(blob)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return {"zip": zip_path, "manifest": manifest_path,
            "package_id": manifest["package_id"],
            "sha256": hashlib.sha256(blob).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="delpi-central repo root")
    parser.add_argument("--commit", required=True,
                        help="approved commit ref (resolved and pinned)")
    parser.add_argument("--module", action="append", dest="modules",
                        required=True, help="module id (repeatable)")
    parser.add_argument("--version", required=True, help="package version X.Y.Z")
    parser.add_argument("--target-env", required=True,
                        help="delivery target label (e.g. TST01); metadata only")
    parser.add_argument("--status", default="SOURCE_CANDIDATE")
    parser.add_argument("--out-dir", default=f"{WORKSPACE}/packaging/out")
    parser.add_argument("--check", metavar="ZIP",
                        help="verify an existing package and exit")
    args = parser.parse_args(argv)

    try:
        if args.check:
            manifest = verify_package(args.check)
            print(json.dumps({"package_id": manifest["package_id"],
                              "verified": True}, indent=2))
            return 0
        result = build_package(args.repo, args.commit, sorted(set(args.modules)),
                               args.version, args.target_env, args.out_dir,
                               args.status)
        print(json.dumps(result, indent=2))
        return 0
    except PackageError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
