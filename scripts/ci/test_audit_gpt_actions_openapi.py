#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_gpt_actions_openapi.py")
spec = importlib.util.spec_from_file_location("audit_gpt_actions_openapi", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def write_artifact(root: Path, api: str, document: dict) -> Path:
    path = root / api / "docs" / "gpt-actions" / "openapi-gpt-actions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def operation(
    *,
    operation_id: str,
    method: str = "post",
    request_body: dict | None = None,
    extra: dict | None = None,
) -> dict:
    op = {"operationId": operation_id, **(extra or {})}
    if request_body is not None:
        op["requestBody"] = request_body
    return {method: op}


class GptActionsOpenApiAuditTest(unittest.TestCase):
    def test_typed_object_request_body_passes(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/preview": operation(
                    operation_id="gpt_preview_change",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ops": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Op"},
                                        }
                                    },
                                },
                                "example": {"ops": [{"op": "create_playlist"}]},
                            }
                        }
                    },
                )
            },
            "components": {"schemas": {"Op": {"type": "object", "properties": {"op": {"type": "string"}}}}},
        }
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_request_body_object_without_properties_fails(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/commit": operation(
                    operation_id="gpt_commit_change",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"},
                                "example": {"ops": []},
                            }
                        }
                    },
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertIn("GPT_ACTION_OBJECT_WITHOUT_PROPERTIES", [item.rule for item in findings])

    def test_typed_ref_request_body_passes(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/commit": operation(
                    operation_id="gpt_commit_change",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Commit"},
                                "example": {"target": {"playlistId": "p1"}},
                            }
                        }
                    },
                )
            },
            "components": {
                "schemas": {
                    "Commit": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "object",
                                "properties": {"playlistId": {"type": "string"}},
                            }
                        },
                    }
                }
            },
        }
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_no_body_operation_passes(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/catalog": operation(
                    operation_id="gpt_get_catalog",
                    method="get",
                )
            },
        }
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_fake_empty_body_fails(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/activate": operation(
                    operation_id="gpt_activate_revision",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": False,
                                },
                                "example": {},
                            }
                        }
                    },
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        rules = [item.rule for item in findings]
        self.assertIn("GPT_ACTION_FAKE_EMPTY_BODY", rules)
        self.assertIn("GPT_ACTION_OBJECT_WITHOUT_PROPERTIES", rules)

    def test_duplicate_operation_id_fails(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/a": operation(operation_id="gpt_get_catalog", method="get"),
                "/b": operation(operation_id="gpt_get_catalog", method="get"),
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertEqual([item.rule for item in findings], ["GPT_ACTION_OPERATION_ID_DUPLICATE"])

    def test_write_body_without_example_fails(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/commit": operation(
                    operation_id="gpt_commit_change",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"ops": {"type": "array", "items": {"type": "string"}}},
                                }
                            }
                        }
                    },
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertEqual([item.rule for item in findings], ["GPT_ACTION_BODY_WITHOUT_EXAMPLE"])

    def test_untyped_semantic_array_fails(self):
        document = {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/preview": operation(
                    operation_id="gpt_preview_change",
                    request_body={
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ops": {"type": "array", "items": {"type": "object"}}
                                    },
                                },
                                "example": {"ops": [{}]},
                            }
                        }
                    },
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertIn("GPT_ACTION_UNTYPED_ARRAY_ITEM", [item.rule for item in findings])

    def test_discover_and_audit_real_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_artifact(
                root,
                "demo-api",
                {
                    "openapi": "3.1.1",
                    "paths": {
                        "/gpt-actions/v1/catalog": {
                            "get": {"operationId": "gpt_get_catalog"}
                        }
                    },
                },
            )
            findings = mod.audit_repository(root)
        self.assertEqual(findings, [])

    def test_current_repo_artifacts_pass(self):
        findings = mod.audit_repository(mod.ROOT)
        self.assertEqual(findings, [], [item.format() for item in findings])


if __name__ == "__main__":
    unittest.main()
