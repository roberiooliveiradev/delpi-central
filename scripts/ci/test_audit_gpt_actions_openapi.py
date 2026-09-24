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
        self.assertIn("GPT_ACTION_EMPTY_OBJECT_SCHEMA", [item.rule for item in findings])

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
        self.assertIn("GPT_ACTION_EMPTY_OBJECT_SCHEMA", rules)

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

    def test_nullable_type_union_fails(self):
        document = {
            "openapi": "3.1.1",
            "components": {
                "schemas": {
                    "Envelope": {
                        "type": "object",
                        "properties": {
                            "error": {"type": ["object", "null"]},
                        },
                    }
                }
            },
            "paths": {
                "/gpt-actions/v1/catalog": operation(
                    operation_id="gpt_get_catalog", method="get"
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertEqual(
            [item.rule for item in findings], ["GPT_ACTION_NULLABLE_TYPE_UNION"]
        )

    def test_multi_scalar_type_union_fails(self):
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
                                        "periodDays": {"type": ["integer", "string"]},
                                    },
                                },
                                "example": {"periodDays": 7},
                            }
                        }
                    },
                )
            },
        }
        findings = mod.validate_document("x.json", document)
        self.assertEqual([item.rule for item in findings], ["GPT_ACTION_TYPE_UNION"])

    def test_scalar_nullable_passes(self):
        document = {
            "openapi": "3.1.1",
            "components": {
                "schemas": {
                    "Envelope": {
                        "type": "object",
                        "properties": {
                            "error": {
                                "type": "object",
                                "nullable": True,
                                "additionalProperties": True,
                            },
                        },
                    }
                }
            },
            "paths": {
                "/gpt-actions/v1/catalog": operation(
                    operation_id="gpt_get_catalog", method="get"
                )
            },
        }
        self.assertEqual(mod.validate_document("x.json", document), [])

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
        self.assertIn("GPT_ACTION_UNTYPED_NESTED_ARRAY_ITEM", [item.rule for item in findings])

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

    def _write_body(self, schema: dict, example: dict | None = None) -> dict:
        media = {"schema": schema, "example": example or {"ok": True}}
        return {
            "openapi": "3.1.1",
            "paths": {
                "/gpt-actions/v1/preview": operation(
                    operation_id="gpt_preview_change",
                    request_body={"content": {"application/json": media}},
                )
            },
        }

    def test_typed_map_additional_properties_passes(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "fieldLabels": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    }
                },
            }
        )
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_oneof_typed_branches_pass(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "op": {"type": "string", "const": "keepRows"},
                                        "count": {"type": "integer"},
                                    },
                                }
                            ]
                        },
                    }
                },
            }
        )
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_explicit_opaque_object_passes(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "block": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                        "x-delpi-gpt-opaque-object": True,
                        "description": "Editor blob",
                    }
                },
            }
        )
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_typed_nested_array_items_pass(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "sortOrder": {"type": "integer"},
                            },
                        },
                    }
                },
            }
        )
        self.assertEqual(mod.validate_document("x.json", document), [])

    def test_empty_freeform_without_marker_fails(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    }
                },
            }
        )
        rules = [item.rule for item in mod.validate_document("x.json", document)]
        self.assertIn("GPT_ACTION_OPAQUE_OBJECT_NOT_EXPLICIT", rules)

    def test_nested_items_empty_object_fails(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "object", "properties": {}},
                    }
                },
            }
        )
        rules = [item.rule for item in mod.validate_document("x.json", document)]
        self.assertTrue(
            {"GPT_ACTION_UNTYPED_NESTED_ARRAY_ITEM", "GPT_ACTION_EMPTY_OBJECT_SCHEMA"}
            & set(rules)
        )

    def test_opaque_marker_without_description_fails(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "blob": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                        "x-delpi-gpt-opaque-object": True,
                    }
                },
            }
        )
        rules = [item.rule for item in mod.validate_document("x.json", document)]
        self.assertIn("GPT_ACTION_OPAQUE_OBJECT_NOT_EXPLICIT", rules)

    def test_untyped_oneof_branch_fails(self):
        document = self._write_body(
            {
                "type": "object",
                "properties": {
                    "op": {
                        "oneOf": [
                            {"type": "object"},
                            {
                                "type": "object",
                                "properties": {"op": {"type": "string"}},
                            },
                        ]
                    }
                },
            }
        )
        rules = [item.rule for item in mod.validate_document("x.json", document)]
        self.assertIn("GPT_ACTION_UNTYPED_ONEOF_BRANCH", rules)


if __name__ == "__main__":
    unittest.main()
