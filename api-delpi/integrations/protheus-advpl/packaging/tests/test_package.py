"""Deterministic tests for packaging/package.py.

Fixtures are small artificial ADVPL-like files committed to a temporary git
repository — no ERP connectivity, no real sources, no Protheus interaction.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package  # noqa: E402

WS = package.MODULES_DIR

MODULE_YAML = """module_id: {mid}
package_tag: {tag}
name: "Fixture {mid}"
owners:
  technical: t
  erp: e
sources: {sources}
"""


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, *args], check=True,
                   capture_output=True)


class RepoFixture:
    def __init__(self) -> None:
        self.dir = tempfile.mkdtemp(prefix="advpl-pkg-test-")
        git(self.dir, "init", "-q")
        git(self.dir, "config", "user.email", "test@example.invalid")
        git(self.dir, "config", "user.name", "fixture")

    def write(self, rel: str, content: str) -> None:
        path = Path(self.dir, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, msg: str = "fixture") -> str:
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-qm", msg)
        return subprocess.run(
            ["git", "-C", self.dir, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()


def make_module(repo: RepoFixture, mid: str, tag: str,
                sources: list[str] | None = None,
                extra_src: dict[str, str] | None = None,
                yaml_override: str | None = None,
                extra_files: dict[str, str] | None = None) -> None:
    sources = sources or []
    src_list = "[" + ", ".join(f'"{s}"' for s in sources) + "]"
    yaml_text = yaml_override if yaml_override is not None else MODULE_YAML.format(
        mid=mid, tag=tag, sources=src_list)
    repo.write(f"{WS}/{mid}/contracts/module.yaml", yaml_text)
    repo.write(f"{WS}/{mid}/README.md", f"# {mid}\n")
    for src in sources:
        repo.write(f"{WS}/{mid}/src/{src}",
                   f"User Function {mid.replace('-', '_')}()\n  Return Nil\n")
    for rel, content in (extra_src or {}).items():
        repo.write(f"{WS}/{mid}/src/{rel}", content)
    for rel, content in (extra_files or {}).items():
        repo.write(f"{WS}/{mid}/{rel}", content)


class PackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = RepoFixture()
        self.out = tempfile.mkdtemp(prefix="advpl-pkg-out-")

    def build(self, commit: str, modules: list[str], **kw):
        out = kw.pop("out", None) or tempfile.mkdtemp(prefix="advpl-pkg-out-")
        return package.build_package(
            self.repo.dir, commit, modules,
            kw.get("version", "0.1.0"), kw.get("env", "TST01"), out)

    # --- positive ---------------------------------------------------------

    def test_valid_module_builds_and_manifest_matches_schema(self):
        make_module(self.repo, "product-master", "SB1", ["DLP04I01.PRW"])
        commit = self.repo.commit()
        result = self.build(commit, ["product-master"])
        manifest = package.verify_package(result["zip"])
        self.assertEqual(manifest["source_commit"], commit)
        self.assertEqual(manifest["package_id"],
                         "DELPI-ADVPL-SB1-TST01-v0.1.0")
        kinds = {f["artifact_type"] for f in manifest["files"]}
        self.assertIn("source", kinds)
        self.assertIn("contract", kinds)

    def test_manifest_points_to_requested_commit(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        c1 = self.repo.commit("first")
        self.repo.write(f"{WS}/m-a/src/X.PRW", "User Function V2()\n")
        c2 = self.repo.commit("second")
        r1 = self.build(c1, ["m-a"])
        r2 = self.build(c2, ["m-a"])
        m1 = package.verify_package(r1["zip"])
        m2 = package.verify_package(r2["zip"])
        self.assertEqual(m1["source_commit"], c1)
        self.assertEqual(m2["source_commit"], c2)
        self.assertNotEqual(r1["sha256"], r2["sha256"])

    def test_working_tree_changes_do_not_leak_into_package(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        commit = self.repo.commit()
        self.repo.write(f"{WS}/m-a/src/X.PRW", "User Function Dirty()\n")
        result = self.build(commit, ["m-a"])
        with zipfile.ZipFile(result["zip"]) as zf:
            data = zf.read(f"{WS}/m-a/src/X.PRW").decode()
        self.assertNotIn("Dirty", data)

    def test_deterministic_zip_same_content_same_sha(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        commit = self.repo.commit()
        r1 = self.build(commit, ["m-a"])
        out2 = tempfile.mkdtemp(prefix="advpl-pkg-out2-")
        r2 = package.build_package(self.repo.dir, commit, ["m-a"],
                                   "0.1.0", "TST01", out2)
        self.assertEqual(r1["sha256"], r2["sha256"])

    def test_only_selected_modules_are_packaged(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        make_module(self.repo, "m-b", "B", ["Y.PRW"])
        commit = self.repo.commit()
        result = self.build(commit, ["m-a"])
        with zipfile.ZipFile(result["zip"]) as zf:
            names = zf.namelist()
        self.assertTrue(any("/m-a/" in n for n in names))
        self.assertFalse(any("/m-b/" in n for n in names))

    def test_content_change_produces_new_hash(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        c1 = self.repo.commit()
        r1 = self.build(c1, ["m-a"])
        self.repo.write(f"{WS}/m-a/src/X.PRW", "User Function Changed()\n")
        c2 = self.repo.commit()
        r2 = self.build(c2, ["m-a"])
        self.assertNotEqual(r1["sha256"], r2["sha256"])

    # --- negatives --------------------------------------------------------

    def test_incomplete_module_manifest_rejected(self):
        bad = "module_id: m-a\nname: nope\n"
        make_module(self.repo, "m-a", "A", [], yaml_override=bad)
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["m-a"])

    def test_nonexistent_module_rejected(self):
        make_module(self.repo, "m-a", "A", [])
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["ghost-module"])

    def test_declared_source_missing_rejected(self):
        make_module(self.repo, "m-a", "A", ["MISSING.PRW"])
        os.remove(Path(self.repo.dir, f"{WS}/m-a/src/MISSING.PRW"))
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["m-a"])

    def test_undeclared_source_rejected(self):
        make_module(self.repo, "m-a", "A", [],
                    extra_src={"STOWAWAY.PRW": "User Function S()\n"})
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["m-a"])

    def test_path_traversal_rejected(self):
        yaml_text = MODULE_YAML.format(
            mid="m-a", tag="A", sources='"../../etc/passwd"')
        make_module(self.repo, "m-a", "A", [], yaml_override=yaml_text)
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["m-a"])

    def test_forbidden_secret_file_rejected(self):
        make_module(self.repo, "m-a", "A", [],
                    extra_files={"contracts/.env": "PASSWORD=x\n"})
        commit = self.repo.commit()
        with self.assertRaises(package.PackageError):
            self.build(commit, ["m-a"])

    def test_hash_divergence_detected_on_verify(self):
        make_module(self.repo, "m-a", "A", ["X.PRW"])
        commit = self.repo.commit()
        result = self.build(commit, ["m-a"])
        tampered = Path(result["zip"] + ".tampered.zip")
        with zipfile.ZipFile(result["zip"]) as zin, \
                zipfile.ZipFile(tampered, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in zin.namelist():
                data = zin.read(name)
                if name.endswith("X.PRW"):
                    data = b"User Function Evil()\n"
                zout.writestr(name, data)
        with self.assertRaises(package.PackageError):
            package.verify_package(str(tampered))

    def test_empty_module_without_sources_still_packages(self):
        make_module(self.repo, "m-a", "A", [])
        commit = self.repo.commit()
        manifest = package.verify_package(
            self.build(commit, ["m-a"])["zip"])
        self.assertEqual(manifest["modules"][0]["source_count"], 0)

    # --- structural guarantees -------------------------------------------

    def test_packaging_has_no_erp_interaction(self):
        src = Path(package.__file__).read_text(encoding="utf-8")
        for forbidden in ("pyodbc", "requests", "urllib.request",
                          "socket", "odbc", "protheus://"):
            self.assertNotIn(forbidden, src)
        self.assertNotIn("MSExecAuto(", src)


if __name__ == "__main__":
    unittest.main()
