"""P7 residual closure — frozen DATA_DIAGNOSIS corpus (roadmap §35.2 residual A).

Test/eval code only — NOT a runtime surface. The corpus measures whether the
existing canonical diagnosis surfaces distinguish, deterministically:

  ERROR IS_NOT EMPTY            EMPTY IS_NOT ERROR
  ROUTE MISS IS_NOT ABSENCE     FILTERED-TO-ZERO IS_NOT SOURCE FAILURE
  MISSING FIELD IS_NOT NULL VALUE   PREVIEW FAILURE IS_NOT ZERO ROWS

Every case declares the OWNER that produces the diagnosis, the expected
diagnosis class (closed vocabulary below), the expected typed code when the
canonical contract defines one, and the expected next-evidence step. No case
duplicates production diagnosis logic — the evaluator calls the owner
services directly with minimal synthetic fixtures.

Diagnosis classes are EVAL vocabulary, not new product error codes. The typed
codes asserted (PARAM_REQUIRED, PARAM_INVALID, DATA_BINDING_FIELD_MISSING,
RESOURCE_NOT_FOUND, DATA_RESOLUTION_FAILED, m.*) already exist in the
canonical owners; the corpus reuses them verbatim.

Cross-boundary: data-shape-vs-intended-visual is DESIGN_METHODOLOGY's owner
(P5 corpus), not a data failure — case d12 asserts that classification.
Route-miss semantics belong to P6 solution intelligence — d11 delegates to
the frozen P6 corpus instead of re-fixturing.
"""

DATA_DIAGNOSIS_CORPUS_VERSION = "data-diagnosis-v1"

# --- closed diagnosis vocabulary (eval-side classes) -----------------------
DIAGNOSIS_VOCABULARY = frozenset(
    {
        "HEALTHY_DATA",            # rows returned, no preview error envelope
        "EMPTY_RESULT",            # zero rows, source/runtime healthy
        "PARAM_REQUIRED",          # contract validation: required param absent
        "PARAM_INVALID",           # contract validation: param violates schema
        "BINDING_FIELD_MISSING",   # consumer references field transform removed
        "MODEL_NOT_FOUND",         # persisted DataModel id not found
        "TRANSFORM_ERROR",         # typed m.* transform-stage failure
        "RUNTIME_SOURCE_ERROR",    # resolution-stage upstream/runtime failure
        "WRONG_LAYER_FILTER",      # filterDigest wrongLayerHints non-empty
        "ROUTE_MISS_NOT_ABSENCE",  # route search miss, typed gap — not absence
        "CROSS_BOUNDARY_DESIGN",   # owned by DESIGN_METHODOLOGY, not data
    }
)

# --- closed next-evidence vocabulary ---------------------------------------
NEXT_STEP_VOCABULARY = frozenset(
    {
        "PROCEED",                    # healthy data — continue to visual choice
        "REPORT_EMPTY",               # state emptiness honestly; not an error
        "WIDEN_FILTER_OR_PERIOD",     # valid source; filter excluded all rows
        "PROVIDE_REQUIRED_PARAM",     # ask/read for the missing required param
        "FIX_PARAM_VALUE",            # correct the invalid param to schema
        "REPAIR_BINDING_OR_FIELD",    # restore field or rebind consumer
        "VERIFY_MODEL_ID",            # read dataModels[] before inspecting
        "READ_TRANSFORM_ERROR",       # surface the typed m.* step failure
        "RETRY_OR_CHECK_UPSTREAM",    # runtime/upstream issue, retryable class
        "RE_LAYER_FILTERS",           # apply re_layer_playlist_filters guidance
        "READ_SOLUTION_ECOSYSTEM",    # miss → typed gap / candidate evidence
        "DELEGATE_TO_DESIGN_METHODOLOGY",  # not a data diagnosis at all
    }
)

# diagnosis class -> next steps consistent with it (integrity gate)
NEXT_STEP_ALLOWED = {
    "HEALTHY_DATA": {"PROCEED"},
    "EMPTY_RESULT": {"REPORT_EMPTY", "WIDEN_FILTER_OR_PERIOD"},
    "PARAM_REQUIRED": {"PROVIDE_REQUIRED_PARAM"},
    "PARAM_INVALID": {"FIX_PARAM_VALUE"},
    "BINDING_FIELD_MISSING": {"REPAIR_BINDING_OR_FIELD"},
    "MODEL_NOT_FOUND": {"VERIFY_MODEL_ID"},
    "TRANSFORM_ERROR": {"READ_TRANSFORM_ERROR"},
    "RUNTIME_SOURCE_ERROR": {"RETRY_OR_CHECK_UPSTREAM"},
    "WRONG_LAYER_FILTER": {"RE_LAYER_FILTERS"},
    "ROUTE_MISS_NOT_ABSENCE": {"READ_SOLUTION_ECOSYSTEM"},
    "CROSS_BOUNDARY_DESIGN": {"DELEGATE_TO_DESIGN_METHODOLOGY"},
}

_OTD_OP = "get_sales_order_otd_series"
_OTD_PARAMS = {
    "granularity": "month",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31",
}
_ROL_OP = "get_commercial_rol_summary"
_ROL_PARAMS = {
    "branch": "01",
    "customer_segment": "weg",
    "dateRangePreset": "this_year",
}


def _series_payload(points):
    return {"meta": {"shape": "series"}, "data": {"points": list(points)}}


def _series_block(params=None):
    return {
        "id": "src-1",
        "type": "data_source",
        "dataBinding": {"operationId": _OTD_OP, "params": params or dict(_OTD_PARAMS)},
    }


def _rol_payload():
    return {
        "meta": {"shape": "scalar"},
        "data": {"branch": "01", "rol": 4516461.10},
        "route": {"label": "ROL", "valueFields": ["rol"]},
    }


def _merge_block():
    """Block whose transform merges a sibling source absent from context."""
    return {
        "id": "cur",
        "type": "data_source",
        "dataBinding": {"operationId": _ROL_OP, "params": dict(_ROL_PARAMS)},
        "dataTransform": {
            "steps": [
                {
                    "op": "merge",
                    "sourceId": "absent-src",
                    "leftKey": "join_key",
                    "rightKey": "join_key",
                    "columns": ["rol_prev"],
                }
            ]
        },
    }


DATA_DIAGNOSIS_CORPUS = [
    {
        "caseId": "d01_healthy_rows",
        "kind": "preview",
        "category": "healthy_runtime",
        "authoritativeSource": "dispatch.preview_data_block + slide_data_resolution",
        "fixture": {
            "block": _series_block(),
            "payloads": {
                _OTD_OP: _series_payload(
                    [
                        {"period": "2026-01", "otd_pct": 98.1},
                        {"period": "2026-02", "otd_pct": 97.5},
                    ]
                )
            },
        },
        "expect": {
            "diagnosis": "HEALTHY_DATA",
            "code": None,
            "min_rows": 1,
            "next_step": "PROCEED",
        },
        "dimensions": ["healthy", "error_is_not_empty"],
    },
    {
        "caseId": "d02_empty_rows",
        "kind": "preview",
        "category": "empty_data",
        "authoritativeSource": "dispatch.preview_data_block + slide_data_resolution",
        "fixture": {
            "block": _series_block(),
            "payloads": {_OTD_OP: _series_payload([])},
        },
        "expect": {
            "diagnosis": "EMPTY_RESULT",
            "code": None,
            "max_rows": 0,
            "next_step": "REPORT_EMPTY",
        },
        "dimensions": ["empty_is_not_error"],
    },
    {
        "caseId": "d03_required_param_missing",
        "kind": "preview",
        "category": "param_validation",
        "authoritativeSource": "validate_route_params + dispatch PARAM_REQUIRED mapping",
        "fixture": {
            "operationId": "eval_required_param_route",
            "route": {
                "operationId": "eval_required_param_route",
                "paramSchema": {
                    "period": {
                        "type": "string",
                        "required": True,
                        "label": "Período",
                    }
                },
            },
            "params": {},
        },
        "expect": {
            "diagnosis": "PARAM_REQUIRED",
            "code": "PARAM_REQUIRED",
            "next_step": "PROVIDE_REQUIRED_PARAM",
        },
        "dimensions": ["contract_validation"],
    },
    {
        "caseId": "d04_invalid_param_enum",
        "kind": "preview",
        "category": "param_validation",
        "authoritativeSource": "validate_route_params + dispatch PARAM_INVALID mapping",
        "fixture": {
            "operationId": _OTD_OP,
            "params": {**_OTD_PARAMS, "granularity": "fortnight"},
        },
        "expect": {
            "diagnosis": "PARAM_INVALID",
            "code": "PARAM_INVALID",
            "next_step": "FIX_PARAM_VALUE",
        },
        "dimensions": ["contract_validation"],
    },
    {
        "caseId": "d05_binding_field_missing",
        "kind": "binding",
        "category": "binding_contract",
        "authoritativeSource": "patch_service consumer-safety gate (DATA_BINDING_FIELD_MISSING)",
        "fixture": {
            "consumer_block": {
                "id": "kpi-1",
                "type": "kpi_view",
                "dataSourceId": "src-1",
                "kpiProjection": {"metrics": [{"field": "rol"}]},
            },
            "source_block": {
                "id": "src-1",
                "type": "data_source",
                "dataBinding": {"operationId": _ROL_OP, "params": {}, "label": "ROL"},
            },
            "ops": [
                {
                    "op": "set_data_transform",
                    "blockId": "src-1",
                    "steps": [{"op": "select", "columns": ["branch", "segment"]}],
                }
            ],
        },
        "expect": {
            "diagnosis": "BINDING_FIELD_MISSING",
            "code": "DATA_BINDING_FIELD_MISSING",
            "next_step": "REPAIR_BINDING_OR_FIELD",
        },
        "dimensions": ["missing_field_is_not_null_value"],
    },
    {
        "caseId": "d06_model_not_found",
        "kind": "model",
        "category": "datamodel_lookup",
        "authoritativeSource": "dispatch.inspect_data_model (RESOURCE_NOT_FOUND + modelId)",
        "fixture": {"modelId": "absent-model"},
        "expect": {
            "diagnosis": "MODEL_NOT_FOUND",
            "code": "RESOURCE_NOT_FOUND",
            "next_step": "VERIFY_MODEL_ID",
        },
        "dimensions": ["typed_not_found"],
    },
    {
        "caseId": "d07_transform_failure",
        "kind": "preview",
        "category": "transform_failure",
        "authoritativeSource": "transform engine m.* + preview error stage=transform",
        "fixture": {
            "block": _merge_block(),
            "payloads": {_ROL_OP: _rol_payload()},
        },
        "expect": {
            "diagnosis": "TRANSFORM_ERROR",
            "code": "m.merge_source_unavailable",
            "stage": "transform",
            "next_step": "READ_TRANSFORM_ERROR",
        },
        "dimensions": ["preview_failure_is_not_zero_rows"],
    },
    {
        "caseId": "d08_runtime_unavailable",
        "kind": "preview",
        "category": "runtime_failure",
        "authoritativeSource": "resolution error + preview error stage=resolution",
        "fixture": {
            "block": _series_block(),
            "payloads": {},
            "fails": {_OTD_OP: "synthetic upstream failure"},
        },
        "expect": {
            "diagnosis": "RUNTIME_SOURCE_ERROR",
            "code": "DATA_RESOLUTION_FAILED",
            "stage": "resolution",
            "next_step": "RETRY_OR_CHECK_UPSTREAM",
        },
        "dimensions": ["error_is_not_empty"],
    },
    {
        "caseId": "d09_filter_to_zero",
        "kind": "preview",
        "category": "filter_effect",
        "authoritativeSource": "dispatch.preview_data_block — healthy source + empty selection",
        "fixture": {
            "block": _series_block(
                params={**_OTD_PARAMS, "customer_codes": "NO_MATCH_001"}
            ),
            "payloads": {_OTD_OP: _series_payload([])},
        },
        "expect": {
            "diagnosis": "EMPTY_RESULT",
            "code": None,
            "max_rows": 0,
            "next_step": "WIDEN_FILTER_OR_PERIOD",
        },
        "dimensions": ["filtered_to_zero_is_not_source_failure"],
    },
    {
        "caseId": "d10_wrong_layer_filter",
        "kind": "filter_digest",
        "category": "filter_layering",
        "authoritativeSource": "FilterDigestService.digest_slide wrongLayerHints",
        "fixture": {
            "native_config": {
                "version": 5,
                "blocks": [
                    {
                        "id": "s1",
                        "type": "data_source",
                        "dataBinding": {
                            "operationId": _ROL_OP,
                            "params": {"branch": "01"},
                        },
                    },
                    {
                        "id": "s2",
                        "type": "data_source",
                        "dataBinding": {
                            "operationId": _ROL_OP,
                            "params": {"branch": "01"},
                        },
                    },
                ],
            },
            "programming_defaults": {},
        },
        "expect": {
            "diagnosis": "WRONG_LAYER_FILTER",
            "code": None,
            "hint_prefix": "shared_branch",
            "next_step": "RE_LAYER_FILTERS",
        },
        "dimensions": ["layering_signal_is_not_runtime_failure"],
    },
    {
        "caseId": "d11_route_miss_not_absence",
        "kind": "route_miss",
        "category": "route_discovery_gap",
        "authoritativeSource": "P6 frozen corpus case miss_no_evidence (delegated eval)",
        "fixture": {"p6_case_id": "miss_no_evidence"},
        "expect": {
            "diagnosis": "ROUTE_MISS_NOT_ABSENCE",
            "code": None,
            "next_step": "READ_SOLUTION_ECOSYSTEM",
        },
        "dimensions": ["route_miss_is_not_absence"],
    },
    {
        "caseId": "d12_shape_vs_visual",
        "kind": "cross_boundary",
        "category": "cross_boundary",
        "authoritativeSource": "P5 frozen corpus case high_cardinality_rejects_pie (delegated)",
        "fixture": {"p5_case_id": "high_cardinality_rejects_pie"},
        "expect": {
            "diagnosis": "CROSS_BOUNDARY_DESIGN",
            "code": None,
            "next_step": "DELEGATE_TO_DESIGN_METHODOLOGY",
        },
        "dimensions": ["design_problem_is_not_data_failure"],
    },
]
