from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_cursor_rules.py"
SPEC = importlib.util.spec_from_file_location("audit_cursor_rules", SCRIPT_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class InventoryOwnershipAuditTests(unittest.TestCase):
    def test_accepts_rule_under_declared_owner(self) -> None:
        ownership = {
            "owner-a.mdc": ["a.mdc"],
            "owner-b.mdc": ["b.mdc"],
        }
        inventory = """# Inventory

## 1. A

Owner: `owner-a.mdc`

- `a.mdc`

## 2. B

Owner: `owner-b.mdc`

- `b.mdc`
"""
        errors: list[str] = []

        AUDIT.audit_inventory_ownership(inventory, ownership, errors)

        self.assertEqual([], errors)

    def test_rejects_rule_under_wrong_owner_even_when_name_is_present(self) -> None:
        ownership = {
            "owner-a.mdc": ["a.mdc"],
            "owner-b.mdc": ["b.mdc"],
        }
        inventory = """# Inventory

## 1. A

Owner: `owner-a.mdc`

## 2. B

Owner: `owner-b.mdc`

- `a.mdc`
- `b.mdc`
"""
        errors: list[str] = []

        AUDIT.audit_inventory_ownership(inventory, ownership, errors)

        self.assertIn(
            "a.mdc: inventário lista sob [owner-b.mdc], mas responsibility-map define owner-a.mdc",
            errors,
        )

    def test_rejects_rule_mentioned_only_in_prose(self) -> None:
        ownership = {"owner-a.mdc": ["a.mdc"]}
        inventory = """# Inventory

A regra `a.mdc` existe e é importante.

## 1. A

Owner: `owner-a.mdc`
"""
        errors: list[str] = []

        AUDIT.audit_inventory_ownership(inventory, ownership, errors)

        self.assertIn(
            "a.mdc: regra não listada na seção do owner owner-a.mdc",
            errors,
        )

    def test_repository_inventory_matches_responsibility_map(self) -> None:
        map_path = REPO_ROOT / ".cursor" / "rules" / "responsibility-map.json"
        inventory_path = (
            REPO_ROOT
            / "docs"
            / "11-padroes-de-desenvolvimento"
            / "inventario-regras-cursor.md"
        )
        payload = json.loads(map_path.read_text(encoding="utf-8"))
        ownership = payload["owners"]
        inventory = inventory_path.read_text(encoding="utf-8")
        errors: list[str] = []

        AUDIT.audit_inventory_ownership(inventory, ownership, errors)

        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
