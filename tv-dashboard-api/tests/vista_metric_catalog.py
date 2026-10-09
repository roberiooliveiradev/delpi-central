"""P7 metric catalog (roadmap §35.2) — bounded, machine-readable.

Test/eval code only — NOT projected into the Actions catalog and never a
runtime model surface. Every dimension declares its measurement source and
honest status; no percentages without precise denominators, no composite
score.

Corpus-native dims are computed by tests/run_vista_eval.py reusing the
FROZEN phase corpora (no copied fixtures). Suite-native dims are covered
by the named pytest files — the runner reports them as delegated gates.
"""

EVAL_CORPUS_VERSION = "vista-quality-v1"

MEASURABLE_NOW = "MEASURABLE_NOW"
NEEDS_FIXTURE = "NEEDS_FIXTURE"
NEEDS_TELEMETRY = "NEEDS_TELEMETRY"
NEEDS_HUMAN_RUBRIC = "NEEDS_HUMAN_RUBRIC"


def _m(purpose, source, numerator, denominator, status, exclusions="-", evidence="-"):
    return {
        "purpose": purpose,
        "measurementSource": source,
        "numerator": numerator,
        "denominator": denominator,
        "exclusions": exclusions,
        "evidence": evidence,
        "status": status,
    }


VISTA_METRIC_CATALOG = {
    # --- P4 grounding -----------------------------------------------------
    "OBJECT_GROUNDING": _m(
        "Correct editor grounding state for selection references",
        "suite:tests/test_editor_focus_grounding.py",
        "cases with expected selectionState",
        "all grounding corpus cases",
        MEASURABLE_NOW,
        evidence="P4 corpus (ACTIVE/STALE/ABSENT/AMBIGUOUS)",
    ),
    "TARGET_RESOLUTION": _m(
        "Resolved target object matches user intent without guessing",
        "suite:tests/test_editor_focus_grounding.py + corpus:p5 target_*",
        "cases resolved to the expected target id",
        "all cases with a resolvable target expectation",
        MEASURABLE_NOW,
        evidence="P4 corpus + P5 no_target_guess/target_id keys",
    ),
    "CREATE_VS_ALTER": _m(
        "CREATE never silently becomes ALTER and vice-versa",
        "suite:presentation suggest/mutation tests",
        "cases with correct create-vs-alter routing",
        "all create/alter fixture cases",
        MEASURABLE_NOW,
        evidence="P4 corpus CREATE-preserved cases + typed-op tests",
    ),
    "CLARIFICATION_CORRECTNESS": _m(
        "Clarification asked only for facts not readable from context",
        "corpus:p5 + suite:p4",
        "cases where clarification policy matches expectation",
        "all cases with next_action/next_question/no_target_guess keys",
        MEASURABLE_NOW,
        evidence="P5 read-before-ask + P4 clarification cases",
    ),
    # --- P5 design methodology -------------------------------------------
    "VISUAL_SELECTION": _m(
        "Recommended visual family fits the observed data shape",
        "corpus:p5",
        "cases whose visualFamily meets family_in/family_not_in",
        "all corpus cases with a family expectation",
        MEASURABLE_NOW,
        exclusions="aesthetic quality — human rubric only",
        evidence="P5 frozen corpus",
    ),
    "DATA_SHAPE_AWARENESS": _m(
        "Methodology correctly classifies data readiness from digest shape",
        "corpus:p5",
        "cases with correct readiness classification",
        "all corpus cases with readiness/readiness_in/missing_fact keys",
        MEASURABLE_NOW,
        evidence="P5 frozen corpus",
    ),
    "VISUAL_EVIDENCE_CORRECTNESS": _m(
        "Pixel claims only when canonical pixel evidence exists",
        "corpus:p5",
        "cases with correct evidence gating",
        "cases with evidence_level_in/aesthetic_claim keys",
        MEASURABLE_NOW,
        evidence="P5 frozen corpus",
    ),
    "UNSUPPORTED_CLAIM": _m(
        "Fabricated recommendations on empty/ambiguous input",
        "corpus:p5",
        "cases that fabricate (target: 0)",
        "cases asserting fabricated=False",
        MEASURABLE_NOW,
        evidence="P5 frozen corpus",
    ),
    # --- P6 solution intelligence ------------------------------------------
    "DATA_ROUTE_RETRIEVAL": _m(
        "Approved TV route retrieval for known business intents",
        "corpus:p6",
        "hit cases that return the expected route set",
        "all corpus cases with non-empty tv_routes",
        MEASURABLE_NOW,
        evidence="P6 frozen corpus",
    ),
    "FALSE_ABSENCE": _m(
        "Route miss never claims the data/solution does not exist",
        "corpus:p6",
        "miss cases preserving searchMissDoesNotProveAbsence + typed gap",
        "all corpus cases with empty tv_routes",
        MEASURABLE_NOW,
        evidence="P6 frozen corpus",
    ),
    "SOLUTION_OWNER_RESOLUTION": _m(
        "Correct Core solution candidate(s) identified after a miss",
        "corpus:p6",
        "cases whose candidates match the expected id set",
        "cases with a candidates expectation",
        MEASURABLE_NOW,
        evidence="P6 frozen corpus",
    ),
    "ROUTE_VS_SOLUTION_DISTINCTION": _m(
        "TV_ROUTE_FOUND vs ecosystem outcomes classified correctly",
        "corpus:p6",
        "cases with correct gapClassification",
        "all corpus cases",
        MEASURABLE_NOW,
        evidence="P6 frozen corpus",
    ),
    "AMBIGUITY_HANDLING": _m(
        "Multiple plausible solutions surfaced, never first-picked",
        "corpus:p6",
        "ambiguous cases classified AMBIGUOUS_SOLUTIONS with full candidate set",
        "cases expecting ambiguity",
        MEASURABLE_NOW,
        evidence="P6 frozen corpus",
    ),
    "UNAUTHORIZED_SOLUTION_LEAK": _m(
        "Candidate payloads never carry non-safe Core fields",
        "corpus:p6",
        "leaks found (target: 0)",
        "all cases that emit candidates",
        MEASURABLE_NOW,
        evidence="P6 corpus forbidden-field assertions",
    ),
    # --- suite-native dims --------------------------------------------------
    "DATA_DIAGNOSIS": _m(
        "Data-bound diagnosis across slide/data-source state",
        "suite:tests (data resolution/preview suites)",
        "diagnosis fixtures passing",
        "diagnosis fixtures",
        NEEDS_FIXTURE,
        evidence="partial — data-bound preview suites exist",
    ),
    "FILTER_LAYERING": _m(
        "Correct filter layer selected (global/slide/block/model)",
        "suite:tests/test_filter_expression_parity.py et al.",
        "layering fixtures passing",
        "layering fixtures",
        MEASURABLE_NOW,
        exclusions="contract PARTIAL coverage is not a failure",
        evidence="filter parity suite",
    ),
    "DISPLAY_FORMAT_SELECTION": _m(
        "Supported display formats chosen; unsupported addressed honestly",
        "suite:tests/test_display_format_*.py",
        "format fixtures passing",
        "format fixtures",
        MEASURABLE_NOW,
        exclusions="unsupported addressability (PARTIAL contract) excluded",
        evidence="display-format suites",
    ),
    "TYPED_OP_VALIDITY": _m(
        "Suggested ops are valid against the canonical op catalog",
        "suite:tests/test_presentation_suggest_ops_service.py",
        "invalid typed ops (target: 0)",
        "all suggested ops in fixtures",
        MEASURABLE_NOW,
        evidence="suggest-ops + schema tests",
    ),
    "PROPOSAL_VALIDITY": _m(
        "PREPARE outcomes are typed, not flattened",
        "suite:prepare/confirmation/stale-proposal tests",
        "fixtures per canonical outcome family",
        "all prepare fixtures",
        MEASURABLE_NOW,
        evidence="commit_service test suites",
    ),
    "WRITE_SAFETY": _m(
        "Governed-write contract: confirmation, AuthZ, revision, read-back",
        "suite:governed write tests",
        "unsafe writes (target: 0)",
        "all write-path fixtures",
        MEASURABLE_NOW,
        evidence="governed-write suite",
    ),
    "VERIFY_OUTCOME": _m(
        "Post-commit verification outcome recorded distinctly from commit",
        "telemetry:vista_quality_telemetry.verify + suite",
        "verify events with typed outcome",
        "commit executions observed",
        MEASURABLE_NOW,
        evidence="telemetry hook in commit_service (P7)",
    ),
    "USER_CORRECTION": _m(
        "User correction signals (re-issue, re-target, undo)",
        "none canonical",
        "corrections identified",
        "n/a",
        NEEDS_TELEMETRY,
        exclusions="no deterministic correction signal exists — not fabricated",
        evidence="no canonical correction/undo event source inventoried",
    ),
    "TRANSPORT_PARITY": _m(
        "Semantic parity between GPT Actions and MCP surfaces",
        "suite:test_mcp_* + unified boundary",
        "divergent semantics (target: 0)",
        "all parity fixtures",
        MEASURABLE_NOW,
        evidence="parity + conformance suites",
    ),
}

FORBIDDEN_TELEMETRY_KEYS = frozenset(
    {
        "authorization",
        "token",
        "jwt",
        "prompt",
        "message",
        "content",
        "nativeConfig",
        "rows",
        "rawResponse",
        "blockId",
        "playlistId",
        "userId",
        "query",
    }
)
