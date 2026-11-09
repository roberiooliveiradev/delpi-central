"""EVA semantic action registry — typed allowlist (EVA.MCP.SEMANTIC.R1).

Pure-data model, no transport/framework imports: the six public MCP
tools dispatch on ``(entity, action)`` — never on URLs, HTTP methods,
SQL or model-supplied function names. New Engineering capabilities
are added here as registry entries, never as new MCP tools.

Classification legend (``risk``):
- ``read``        — official facts, no side effects;
- ``analysis``    — derived, labeled computation over official facts;
- ``moderate``    — non-destructive mutation (create/update);
- ``destructive`` — delete / replace-all import — sealed proposal only.

``status``: ``proven`` = executed and evidenced; ``planned`` /
``not_implemented`` are catalogued honestly, never executable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEMANTIC_CATALOG_VERSION = "1.0"

SEMANTIC_TOOL_NAMES: tuple[str, ...] = (
    "get_context",
    "read",
    "analyze",
    "knowledge",
    "execute",
    "delete",
)


@dataclass(frozen=True)
class SemanticAction:
    entity: str
    action: str
    tool: str
    description: str
    risk: str
    status: str = "proven"
    destructive: bool = False
    ref_arg: str | None = None
    ref_description: str | None = None
    requires: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()
    paginated: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def capability(self) -> str:
        return f"{self.entity}.{self.action}"

    def public_dict(self) -> dict:
        out: dict = {
            "entity": self.entity,
            "action": self.action,
            "tool": self.tool,
            "description": self.description,
            "risk": self.risk,
            "status": self.status,
        }
        if self.destructive:
            out["destructive"] = True
        if self.ref_arg:
            out["ref_arg"] = self.ref_arg
            if self.ref_description:
                out["ref_description"] = self.ref_description
        if self.requires:
            out["requires"] = list(self.requires)
        if self.fields:
            out["fields"] = list(self.fields)
        if self.phases:
            out["phases"] = list(self.phases)
        if self.paginated:
            out["paginated"] = True
        if self.notes:
            out["notes"] = list(self.notes)
        return out


def _a(
    entity: str,
    action: str,
    tool: str,
    description: str,
    risk: str,
    **kw,
) -> SemanticAction:
    return SemanticAction(
        entity=entity,
        action=action,
        tool=tool,
        description=description,
        risk=risk,
        **kw,
    )


_NC_LIST_FIELDS = (
    "status", "sale_number", "lmp_number", "customer_name", "product_code",
    "problem_tag", "date_start", "date_end", "sort_by", "sort_dir",
)
_LMP_PERIOD_FIELDS = ("start_date", "end_date", "branch")
# Writable NC fields — mirrors the official E-NC-07/08 contract; the
# authoritative check stays in tool_bridge.NC_WRITABLE_FIELDS (unknown
# keys are rejected there, never silently dropped).
_NC_WRITE_FIELDS = (
    "status", "sale_number", "lmp_number", "customer_name",
    "occurrence_date", "launch_date", "last_revision_date",
    "executed_by", "released_by", "defect_description",
    "corrective_actions", "technical_opinion", "problem_tags",
    "products", "registered_at",
)

SEMANTIC_ACTIONS: tuple[SemanticAction, ...] = (
    # --- get_context ------------------------------------------------------
    _a(
        "catalog", "capabilities", "get_context",
        "Live capability discovery: entities, actions, schemas, risk, "
        "phases and honest availability — call before any other tool.",
        "read",
    ),
    # --- read: avatar (narrative asset — AVATAR-INLINE-MCP-V1) ------------
    _a(
        "avatar", "get", "read",
        "Official approved avatar image of the specialist — narrative "
        "asset returned as an ImageContent block, never authorization.",
        "read",
    ),
    # --- read: engineering ------------------------------------------------
    _a(
        "engineering", "home", "read",
        "Authorized Engineering workspace: sections, attention items, "
        "tasks, requests and LMPs with per-source availability.",
        "read",
    ),
    _a(
        "engineering", "overview", "read",
        "Official Engineering indicators (3 LMP + 3 TRANSFORMA+) with "
        "values, units, period, scope and provenance — never recalculated.",
        "read",
        fields=("start_date", "end_date", "competence", "branch"),
    ),
    # --- read: lmp ----------------------------------------------------------
    _a(
        "lmp", "list", "read",
        "Engineering LMP/sales-order dashboard list with period and "
        "status filters.",
        "read",
        fields=_LMP_PERIOD_FIELDS + ("listing_type", "status"),
        paginated=True,
    ),
    _a(
        "lmp", "summary", "read",
        "Aggregated official LMP summary for the period.",
        "read", fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "detail", "read",
        "Single LMP/sales-order detail by sale number.",
        "read", ref_arg="sale_number",
        ref_description="Sales order number (e.g. 003306).",
        fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "history_events", "read",
        "Chronological event history of an LMP.",
        "read", ref_arg="sale_number",
        fields=_LMP_PERIOD_FIELDS + ("revision",),
    ),
    _a(
        "lmp", "history_flow", "read",
        "Stage/flow timeline of an LMP.",
        "read", ref_arg="sale_number",
        fields=_LMP_PERIOD_FIELDS + ("revision",),
    ),
    _a(
        "lmp", "goal_context", "read",
        "Official goal context for eligible LMP indicators.",
        "read", fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "department_idd", "read",
        "Departmental IDD indicator by competence.",
        "read", fields=("competence",) + _LMP_PERIOD_FIELDS,
    ),
    _a(
        "lmp", "nc_streak", "read",
        "Days-without-nonconformity streak indicator.",
        "read",
    ),
    # --- read: product ------------------------------------------------------
    _a(
        "product", "search", "read",
        "Search the official product catalog (TOTVS SB1 via API DELPI) "
        "by code, description, group, subgroup, type or customer "
        "reference.",
        "read",
        fields=(
            "code", "description", "group_code", "subgroup",
            "product_type", "customer_reference", "sort", "direction",
        ),
        paginated=True,
    ),
    _a(
        "product", "detail", "read",
        "Product cadastral record — engineering view (no cost/price/"
        "fiscal fields, per contract view=engineering).",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
    ),
    _a(
        "product", "structure", "read",
        "Official product structure/BOM tree from the owning source.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        fields=("max_depth", "page_size"),
    ),
    _a(
        "product", "where_used", "read",
        "Reverse BOM — official parent products that consume this item.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        fields=("max_depth", "page_size"),
        paginated=True,
    ),
    _a(
        "product", "suppliers", "read",
        "Official product×supplier links (TOTVS SA5).",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        paginated=True,
    ),
    _a(
        "product", "drawing", "read",
        "Official technical drawing metadata from the file-server "
        "library (Cockpit do Operador contract) — filename, revision, "
        "variant, size and modified date.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        notes=(
            "PDF bytes are served by the Engineering API route "
            "/v1/products/{code}/drawing/pdf — and by the MCP action "
            "product.drawing_download as an embedded resource.",
        ),
    ),
    _a(
        "product", "drawing_download", "read",
        "Official technical drawing PDF bytes (full document) — "
        "delivered as an MCP EmbeddedResource (BlobResourceContents "
        "base64, mimeType application/pdf) alongside filename, size "
        "and SHA-256 in the typed payload. Read-only, delegated "
        "user identity; the client must materialize embedded "
        "resources to obtain the file.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        notes=(
            "Transport = EmbeddedResource inside tools/call (MCP "
            "spec 2025-06-18+); base64 in a typed blob — never plain "
            "text. Not every MCP host surfaces binary content: "
            "materialization depends on the client's capabilities.",
        ),
    ),
    _a(
        "product", "history", "read",
        "Product history: cadastral revision fields plus official "
        "purchase-price history when authorized — each section labeled "
        "with its provenance/status.",
        "read", ref_arg="product_code",
        ref_description="Product code in the official catalog.",
        fields=("start_date", "end_date", "branch", "history_limit"),
        notes=(
            "No official cadastral revision-history contract exists "
            "(OWNER_BLOCKED, doc 63 §2.7) — that section reports "
            "not_implemented honestly.",
        ),
    ),
    # --- read: nonconformity ------------------------------------------------
    _a(
        "nonconformity", "search", "read",
        "Search nonconformities with filters, sorting and pagination.",
        "read", fields=_NC_LIST_FIELDS,
        paginated=True,
    ),
    _a(
        "nonconformity", "detail", "read",
        "Full nonconformity record by id.",
        "read", ref_arg="record_id", ref_description="NC UUID.",
    ),
    _a(
        "nonconformity", "history", "read",
        "Append-only audit history of a nonconformity.",
        "read", ref_arg="record_id",
    ),
    _a(
        "nonconformity", "indicators", "read",
        "Official nonconformity indicators (totals, open, streak).",
        "read",
    ),
    _a(
        "nonconformity", "tags", "read",
        "Nonconformity problem tags in use.",
        "read",
    ),
    _a(
        "nonconformity", "context", "read",
        "Contextual official data around a nonconformity (LMP, product).",
        "read", ref_arg="record_id",
    ),
    _a(
        "nonconformity", "export", "read",
        "Full nonconformity export (all records, official format).",
        "read",
    ),
    # --- analyze ------------------------------------------------------------
    _a(
        "nonconformity", "recurrence", "analyze",
        "Recurrence analysis: group NCs by product, problem tag, status "
        "or customer — verifiable counts labeled CALCULATED, never "
        "recomputed official indicators.",
        "analysis",
        fields=("group_by",) + _NC_LIST_FIELDS,
        notes=(
            "Result is CALCULATED from a bounded sample of official "
            "records; coverage (analyzed vs total) is always reported.",
        ),
    ),
    _a(
        "lmp", "performance", "analyze",
        "LMP performance briefing: official summary + goal context + "
        "NC streak, each fact labeled OBSERVED; goal comparisons "
        "labeled CALCULATED.",
        "analysis",
        fields=_LMP_PERIOD_FIELDS,
    ),
    _a(
        "product", "drawing_analysis", "analyze",
        "Technical drawing analysis: official PDF of a product "
        "(identified by product_code) is extracted and cross-checked "
        "against the registered product card and BOM — revision, "
        "identification, item presence, MP/PI description rules. "
        "Optionally receives `visual_observations[]` (untrusted ChatGPT "
        "perception of a drawing: kind/raw_observation/page/document_"
        "identity/confidence) which are compared to the same verified "
        "document and to official facts as hypotheses. Emits a "
        "DRAFT/CANDIDATE technical report; never approves technically.",
        "analysis",
        fields=(
            "product_code", "visual_observations", "scope",
        ),
        notes=(
            "Deterministic text-layer extraction only — scanned PDFs "
            "yield INCONCLUSIVE; absence of visual evidence never "
            "equals a proven BOM divergence; visual observations are "
            "untrusted input (schema-limited, hypotheses only); "
            "routing/inspection/PA-description checks report "
            "NOT_CHECKED while contracts remain owner-blocked "
            "(docs 69–71)."
        ),
    ),
    _a(
        "product", "drawing_benchmark", "analyze",
        "Governed extraction benchmark: the official product drawing "
        "PDF is fetched once via the delegated gateway and processed "
        "by the backend-defined provider profile (default "
        "approved_local_extractors; experimental visual profile "
        "approved_local_visual_ocr = PDFium render + optional OpenCV "
        "preprocess + local PaddleOCR, gated by its own flag) — same "
        "bytes, same SHA-256, per-provider coverage, spatial evidence "
        "and field matrix. Read-only; requires "
        "ENG_DRAWING_BENCHMARK_ENABLED; results are coverage evidence, "
        "never engineering accuracy or ground truth.",
        "analysis",
        fields=("product_code", "benchmark_profile", "fields"),
        notes=(
            "Fail-closed feature flag; provider allowlist is backend-"
            "defined — the consumer cannot pick providers, paths, URLs "
            "or modules; no SaaS egress; no writes; OCR tokens carry "
            "pixel/PDF-pt boxes + confidence as hypotheses only; "
            "quality metrics remain EVAL_PENDING without owner-approved "
            "ground truth."
        ),
    ),
    _a(
        "product", "drawing_understanding", "analyze",
        "Experimental structural understanding of the official product "
        "drawing (drawing_understanding.v1): region candidates (title "
        "block, component table, revision history, notes, drawing "
        "area), identifier/revision/dimension candidates, table rows "
        "and cells, multiplicity-aware BOM comparison and explicit "
        "ambiguity — all built from OCR token evidence with full "
        "provenance. Candidates are DRAFT only; never promoted to "
        "engineering facts. Requires ENG_DRAWING_BENCHMARK_ENABLED and "
        "ENG_DRAWING_OCR_BENCHMARK_ENABLED.",
        "analysis",
        fields=("product_code",),
        notes=(
            "Deterministic, explainable rules only (position/alignment "
            "clustering); OCR confidence is never association "
            "confidence; DIMENSION_TEXT_FOUND is not a verified "
            "geometry association; BOM stays source of truth; absence "
            "in OCR never proves absence in the drawing; read-only."
        ),
    ),
    # --- knowledge ----------------------------------------------------------
    _a(
        "nonconformity", "guide", "knowledge",
        "Versioned Engineering guidance on the nonconformity contract: "
        "fields, statuses, tags, import semantics and governance.",
        "read",
    ),
    _a(
        "lmp", "guide", "knowledge",
        "Versioned Engineering guidance on LMP domain concepts and "
        "indicator semantics.",
        "read",
    ),
    _a(
        "eva", "usage", "knowledge",
        "How to operate EVA: tools, phases, confirmation model and "
        "availability semantics.",
        "read",
    ),
    # --- execute --------------------------------------------------------------
    _a(
        "nonconformity", "create", "execute",
        "Create a nonconformity via the official contract — direct "
        "execution when the request is unambiguous; idempotency_key "
        "supported; phase=prepare validates without side effects.",
        "moderate",
        phases=("act", "prepare"),
        fields=_NC_WRITE_FIELDS,
        notes=(
            "Direct ACT: no redundant confirmation when intent, data "
            "and authorization are unequivocal.",
        ),
    ),
    _a(
        "nonconformity", "update", "execute",
        "Update a nonconformity — safe full-replace merge of `changes` "
        "over the current record with optimistic locking "
        "(expected_version = updated_at of the record you read).",
        "moderate",
        phases=("act", "prepare"),
        ref_arg="record_id",
        requires=("changes",),
        fields=_NC_WRITE_FIELDS,
        notes=(
            "Never sends a partial payload that would erase fields: "
            "the bridge merges current + changes and rejects keys "
            "outside the contract.",
        ),
    ),
    _a(
        "nonconformity", "import", "execute",
        "JSON import — destructive replace-all semantics. phase=prepare "
        "runs a dry-run report and seals a proposal; phase=commit "
        "requires the sealed proposal_ref and still honors the owner "
        "environment gate (ENG_NC_IMPORT_REPLACE_ENABLED).",
        "destructive",
        destructive=True,
        phases=("prepare", "commit"),
        requires=("items",),
        notes=(
            "No direct phase=act — replace-all always goes through a "
            "sealed proposal verified server-side.",
        ),
    ),
    # --- delete -----------------------------------------------------------------
    _a(
        "nonconformity", "delete", "delete",
        "Hard-delete a nonconformity and its history (irreversible). "
        "phase=prepare seals target + impact into a proposal; "
        "phase=commit executes only with the exact proposal_ref after "
        "verifiable human confirmation.",
        "destructive",
        destructive=True,
        phases=("prepare", "commit"),
        ref_arg="record_id",
        notes=(
            "confirmed=true from the model is NOT proof of "
            "confirmation — the sealed proposal handle is.",
        ),
    ),
    # --- product_registration (PRC — matriz 18 operações do contrato §4) --------
    # Status="planned": catálogo honesto — NUNCA executável até o
    # dispatch estar integrado e testado no mesmo SHA (PARITY_GAP de
    # integração serializada com VAL-01 em semantic_bridge.py).
    _a(
        "product_registration", "list", "read",
        "Product-registration case queue with authorized scope filters "
        "(status, type, assignee, source, search, period).",
        "read", status="planned", paginated=True,
        fields=("status", "type", "assignee", "source", "search",
                "dateFrom", "dateTo"),
    ),
    _a(
        "product_registration", "detail", "read",
        "Case detail: original payload, technical draft, version, "
        "allowedActions and verification summary.",
        "read", status="proven", ref_arg="request_id",
        ref_description="Request UUID.",
    ),
    _a(
        "product_registration", "timeline", "read",
        "Append-only case timeline (actions and decisions).",
        "read", status="planned", ref_arg="request_id", paginated=True,
    ),
    _a(
        "product_registration", "verifications", "read",
        "Official TOTVS verification attempts and divergences.",
        "read", status="planned", ref_arg="request_id",
    ),
    _a(
        "product_registration", "record", "read",
        "Current verified technical record (official code + revision "
        "pointer + freshness).",
        "read", status="planned", ref_arg="record_id",
    ),
    _a(
        "product_registration", "revisions", "read",
        "Immutable revision index of a technical record.",
        "read", status="planned", ref_arg="record_id", paginated=True,
    ),
    _a(
        "product_registration", "revision", "read",
        "Immutable snapshot of a single revision + per-field diff.",
        "read", status="planned", ref_arg="record_id",
        fields=("revision_number",),
    ),
    _a(
        "product_registration", "reference_data", "read",
        "Field catalog, schema version, statuses, sources and "
        "verifiability policy.",
        "read", status="planned",
    ),
    _a(
        "product_registration", "outbound_result", "read",
        "Outbound contract: status/result of a case for its origin.",
        "read", status="planned", ref_arg="request_id",
    ),
    _a(
        "product_registration", "submit", "execute",
        "Create/update intake request — requester is always the human "
        "principal; source attributed by the system.",
        "moderate", status="planned", phases=("act", "prepare"),
        requires=("payload",),
    ),
    _a(
        "product_registration", "start", "execute",
        "Start processing a submitted case (assigns the analyst).",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id", requires=("expected_version",),
    ),
    _a(
        "product_registration", "update_draft", "execute",
        "Field-by-field draft changes — catalog allowlist + CAS + "
        "mandatory reason.",
        "moderate", status="planned", phases=("act", "prepare"),
        ref_arg="request_id", requires=("changes", "expected_version"),
    ),
    _a(
        "product_registration", "request_information", "execute",
        "Open a typed clarification round (PRC-REF-019) and move the case "
        "to needs_information. Payload: questions[] "
        "{targetType: FIELD|SUPPLIER_LINK|GENERAL, targetPath, "
        "targetAttribute, supplierKey, questionText} + optional message; "
        "legacy reason + pending_fields still accepted.",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("expected_version",),
        fields=("questions", "message", "reason", "pending_fields"),
        notes=(
            "Provide questions[] or a legacy reason; resume stays gated "
            "while a round is open (waiver: reason prefix resolves it).",
        ),
    ),
    _a(
        "product_registration", "information_round_list", "read",
        "List clarification rounds of a case (PRC-REF-019) with "
        "hasOpenBlocker; scope enforced by the service.",
        "read", status="proven", ref_arg="request_id",
    ),
    _a(
        "product_registration", "information_round_get", "read",
        "Clarification round detail with typed questions and answers.",
        "read", status="proven", ref_arg="request_id",
        fields=("round_id",),
    ),
    _a(
        "product_registration", "information_question_accept", "execute",
        "Analyst accepts a submitted clarification answer (CAS on the "
        "round version). Payload: round_id, question_id, "
        "expected_round_version.",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("round_id", "question_id", "expected_round_version"),
    ),
    _a(
        "product_registration", "information_follow_up", "execute",
        "Analyst requests a follow-up round for submitted questions "
        "(CAS on the parent round). Payload: round_id, "
        "expected_round_version, questions[], follow_up_question_ids[], "
        "message.",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=(
            "round_id", "expected_round_version",
            "questions", "follow_up_question_ids",
        ),
    ),
    _a(
        "product_registration", "resume", "execute",
        "Resume a needs_information case back to in_progress "
        "(PRC-REF-019). Blocked while an information round is open "
        "unless reason starts with 'waiver:' (explicit dispensa).",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id", requires=("expected_version",),
        fields=("reason",),
        notes=(
            "Gate has_open_information_blocker; waiver: resolves open "
            "rounds before transition.",
        ),
    ),
    _a(
        "product_registration", "submit_review", "execute",
        "LEGACY: submit draft for under_review. Prefer "
        "product_registration.complete (PRC-REF-020).",
        "moderate", status="planned", phases=("act", "prepare"),
        ref_arg="request_id", requires=("expected_version",),
        notes=("Deprecated operational step; kept for REST/EVA alias.",),
    ),
    _a(
        "product_registration", "return_to_attendance", "execute",
        "Reopen legacy under_review cases back to in_progress "
        "(PRC-REF-020 migration path).",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id", requires=("expected_version",),
        fields=("reason",),
    ),
    _a(
        "product_registration", "reject", "execute",
        "Terminal rejection — sealed proposal + verifiable human "
        "confirmation before commit; never touches the live record.",
        "moderate", status="proven", phases=("prepare", "commit"),
        ref_arg="request_id",
        requires=("reason", "expected_version"),
        notes=(
            "Terminal: PREPARE seals target/impact; commit exige "
            "proposal_ref + confirmação humana verificável (elicitation)."
        ),
    ),
    _a(
        "product_registration", "complete", "execute",
        "Concluir atendimento: technical validation + fresh official "
        "TOTVS read/compare; publishes immutable revision ONLY on full "
        "match. Failure keeps in_progress (PRC-REF-020).",
        "moderate", status="proven", phases=("prepare", "commit"),
        ref_arg="request_id",
        requires=("expected_version",),
        fields=("official_code", "reason"),
        notes=(
            "Terminal/high-impact: PREPARE readiness; ACT exige "
            "confirmação humana + leitura oficial fresca — "
            "mismatch/unverifiable/unavailable nunca conclui. "
            "Same Application use case as verify_and_complete."
        ),
    ),
    _a(
        "product_registration", "verify_and_complete", "execute",
        "LEGACY alias of product_registration.complete — same use case.",
        "moderate", status="proven", phases=("prepare", "commit"),
        ref_arg="request_id",
        requires=("expected_version",),
        fields=("official_code", "reason"),
        notes=(
            "Deprecated name; maps to complete_attendance. Prefer "
            "product_registration.complete."
        ),
    ),
    # --- D16 attendance flags (mesmos use cases REST; sem nova MCP tool) ---
    _a(
        "product_registration", "flag_list", "read",
        "List attendance flags for a product-registration case "
        "(operational annotations; not SB1/SA5).",
        "read", status="proven", ref_arg="request_id", paginated=True,
        fields=("status", "page", "page_size"),
    ),
    _a(
        "product_registration", "flag_detail", "read",
        "Attendance flag detail scoped to the authorized request.",
        "read", status="proven", ref_arg="request_id",
        fields=("flag_id",),
    ),
    _a(
        "product_registration", "flag_create", "execute",
        "Create an attendance flag (title/description/subject) — "
        "does not mutate official product data.",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("title", "description"),
        fields=("subject", "target_path", "supplier_key"),
    ),
    _a(
        "product_registration", "flag_update", "execute",
        "Update attendance flag content with CAS expected_version.",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("flag_id", "expected_version"),
        fields=("title", "description", "subject", "target_path",
                "supplier_key"),
    ),
    _a(
        "product_registration", "flag_resolve", "execute",
        "Mark attendance flag RESOLVED (CAS).",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("flag_id", "expected_version"),
        fields=("reason",),
    ),
    _a(
        "product_registration", "flag_reopen", "execute",
        "Reopen a RESOLVED attendance flag (CAS).",
        "moderate", status="proven", phases=("act", "prepare"),
        ref_arg="request_id",
        requires=("flag_id", "expected_version"),
        fields=("reason",),
    ),
    _a(
        "product_registration", "flag_delete", "execute",
        "Soft-delete attendance flag — sealed proposal + verifiable "
        "human confirmation; events retained.",
        "destructive", status="proven", phases=("prepare", "commit"),
        ref_arg="request_id",
        requires=("flag_id", "expected_version"),
        notes=(
            "confirmed=true from the model is NOT authorization — "
            "proposal_ref + human elicitation required on commit."
        ),
    ),
)

_ACTION_INDEX: dict[tuple[str, str], SemanticAction] = {
    (a.entity, a.action): a for a in SEMANTIC_ACTIONS
}


def semantic_action(entity: str, action: str) -> SemanticAction | None:
    return _ACTION_INDEX.get((entity, action))


def actions_for_tool(tool: str) -> tuple[SemanticAction, ...]:
    return tuple(a for a in SEMANTIC_ACTIONS if a.tool == tool)


def actions_for_entity(entity: str) -> tuple[SemanticAction, ...]:
    return tuple(a for a in SEMANTIC_ACTIONS if a.entity == entity)


def entities_summary() -> list[dict]:
    entities: dict[str, list[SemanticAction]] = {}
    for action in SEMANTIC_ACTIONS:
        entities.setdefault(action.entity, []).append(action)
    return [
        {
            "entity": entity,
            "actions": sorted(a.action for a in items),
            "proven": sum(1 for a in items if a.status == "proven"),
            "total": len(items),
        }
        for entity, items in sorted(entities.items())
    ]


def unknown_action_error(entity: str, action: str) -> dict:
    """Honest typed error payload for unregistered (entity, action)."""
    allowed = sorted(
        a.action for a in actions_for_entity(entity)
    ) or sorted({a.entity for a in SEMANTIC_ACTIONS})
    return {
        "error_kind": "validation",
        "entity": entity,
        "action": action,
        "allowed": allowed,
    }


# PLANNED extension surface (Plan 54 §5) — catalogued, never executable.
PLANNED_SEMANTIC_ACTIONS: tuple[dict, ...] = (
    {
        "entity": "product", "action": "update", "tool": "execute",
        "status": "not_implemented",
        "note": "Edição de cadastro de produto — sem contrato WRITE "
                "oficial no owner (doc 63 §2.8, OWNER_BLOCKED).",
    },
    {
        "entity": "routing", "action": "steps", "tool": "read",
        "status": "not_implemented",
        "note": "Roteiros de fabricação — sem contrato oficial.",
    },
    {
        "entity": "raw_material", "action": "specification",
        "tool": "read", "status": "not_implemented",
        "note": "Matérias-primas/especificações — sem fonte oficial.",
    },
    {
        "entity": "inspection", "action": "report", "tool": "read",
        "status": "not_implemented",
        "note": "Inspeções — sem contrato oficial.",
    },
    {
        "entity": "technical_document", "action": "prepare_draft",
        "tool": "execute", "status": "planned",
        "note": "Documentos candidatos DRAFT → revisão → publicação "
                "pelo owner técnico; nunca publicação direta.",
    },
)
