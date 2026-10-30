"""EVA MCP tool bridge — adapters over the official use cases.

Identidade: o contexto autenticado pelo transporte MCP (delpi_auth
middleware + audience/scope) é o mesmo objeto canônico do request;
``access_token`` humano é propagado aos owners downstream exatamente
como nas rotas REST — sem service token, sem elevação (F2a.R1).
AuthZ de negócio: ``engineering.access`` + ``principal_type=="user"``
aplicados aqui, idênticos às rotas /v1 — MCP não é autoridade.

ACT (EVA.ENGINEERING.FULL.CAPABILITY.PARITY): ferramentas mutáveis
executam os MESMOS use cases das rotas /v1 — confirmação humana
explícita (``confirmed``), idempotência/concorrência do contrato
oficial e postcondition por read-back. ``ENG_EVA_ACT_ENABLED`` fail-
closed por ambiente; delete/import são reforçados
(``DESTRUCTIVE_ACT_TOOLS``).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from mcp.types import CallToolResult

from delpi_auth.authz_core import has_any_permission
from delpi_mcp.errors import mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
)
from delpi_mcp.identity import (
    require_mcp_context,
)
from starlette.requests import Request

from engineering_app.application.eva.agent_intelligence_service import (
    EvaAgentIntelligenceService,
)
from engineering_app.application.models.lmp import LmpQuery
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.use_cases.nonconformity.actor import (
    nc_actor_from_principal,
)
from engineering_app.composition import nc_composer
from engineering_app.composition.lmp_composer import (
    build_delegated_auxiliary_source,
    build_get_lmp_detail_use_case,
    build_get_lmp_history_use_case,
    build_get_lmp_summary_use_case,
    build_list_lmps_dashboard_use_case,
)
from engineering_app.domain.nonconformity.errors import (
    NcConcurrencyError,
    NcNotFoundError,
    NcRepositoryError,
    NcUnsafeOperationError,
    NcValidationError,
)
from engineering_app.application.ports.overview_sources import OverviewQuery
from engineering_app.composition.home_composer import (
    build_get_engineering_home_use_case,
)
from engineering_app.composition.overview_composer import (
    build_get_engineering_overview_use_case,
)
from engineering_app.interface.mcp.branding import EVA_FULL_NAME
from engineering_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

logger = logging.getLogger(__name__)

ENGINEERING_ACCESS = "engineering.access"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPETENCE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Campos graváveis do contrato NC oficial (E-NC-07/08) — espelho de
# ``normalize_nc_payload``; chaves fora desta lista são rejeitadas no
# merge de UPDATE em vez de serem silenciosamente descartadas.
NC_WRITABLE_FIELDS: tuple[str, ...] = (
    "status",
    "sale_number",
    "lmp_number",
    "customer_name",
    "occurrence_date",
    "launch_date",
    "last_revision_date",
    "executed_by",
    "released_by",
    "defect_description",
    "corrective_actions",
    "technical_opinion",
    "problem_tags",
    "products",
    "registered_at",
)

EVA_ACT_ENV_FLAG = "ENG_EVA_ACT_ENABLED"
EVA_ACT_DELETE_ENV_FLAG = "ENG_EVA_ACT_DELETE_ENABLED"
EVA_ACT_IMPORT_ENV_FLAG = "ENG_EVA_ACT_IMPORT_ENABLED"


class EvaActDisabledError(Exception):
    """ACT EVA desabilitado neste ambiente — bloqueio honesto fail-closed."""


class EvaConfirmationRequiredError(Exception):
    """ACT invocado sem ``confirmed=true`` — confirmação humana ausente."""

_TOOL_CONTRACT: dict[str, dict[str, Any]] = {
    "get_catalog": {
        "title": "Get catalog",
        "description": "Discovery catalog of the EVA tool surface.",
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
    },
    "get_engineering_home": {
        "title": "Get engineering home",
        "description": (
            "Authorized Engineering workspace — sections, attention items, "
            "tasks, requests and LMPs with per-source availability."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/home",
    },
    "get_engineering_overview": {
        "title": "Get engineering overview",
        "description": (
            "Official six Engineering indicators (3 LMP + 3 TRANSFORMA+) "
            "with values, units, period, scope, provenance and owner-"
            "authorized goals/IDD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "competence": {"type": "string", "pattern": "^\\d{4}-(0[1-9]|1[0-2])$"},
                "branch": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/overview",
    },
    "search_nonconformities": {
        "title": "Search nonconformities",
        "description": (
            "Paginated LMP nonconformity list with filters (status, OV, "
            "LMP number, customer, product code, problem tag, occurrence "
            "period) and whitelisted sorting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["open", "in_progress", "done"]},
                "sale_number": {"type": "string"},
                "lmp_number": {"type": "string"},
                "customer_name": {"type": "string"},
                "product_code": {"type": "string"},
                "problem_tag": {"type": "string"},
                "date_start": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "date_end": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "sort_by": {"type": "string"},
                "sort_dir": {"type": "string", "enum": ["asc", "desc"]},
                "page": {"type": "integer", "minimum": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities",
    },
    "get_nonconformity": {
        "title": "Get nonconformity",
        "description": "Single nonconformity detail by UUID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "format": "uuid"},
            },
            "required": ["record_id"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/{record_id}",
    },
    "get_nonconformity_history": {
        "title": "Get nonconformity history",
        "description": (
            "Append-only audit events (created/updated diffs with actor) "
            "of a nonconformity, newest first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "format": "uuid"},
            },
            "required": ["record_id"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/{record_id}/history",
    },
    "get_nonconformity_indicators": {
        "title": "Get nonconformity indicators",
        "description": (
            "Days-without-NC streak (current and record) computed from "
            "official occurrence dates, plus counters and anchor "
            "degradation flags."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/indicators",
    },
    "get_nonconformity_tags": {
        "title": "Get nonconformity tags",
        "description": "Shared problem-tag catalog with usage counts.",
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/problem-tags",
    },
    "get_nonconformity_context": {
        "title": "Get nonconformity context",
        "description": (
            "Functional context of a nonconformity: official OV fact "
            "(TOTVS via api-delpi facts) plus product structures/BOM of "
            "linked products, with per-source honest availability."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "format": "uuid"},
            },
            "required": ["record_id"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/{record_id}/context",
    },
    "prepare_nonconformity_mutation": {
        "title": "Prepare nonconformity mutation",
        "description": (
            "PREPARE-only analysis of a candidate create/update: returns "
            "normalized payload, validation errors and the projected "
            "history diff — with ZERO side effects. Applying requires "
            "separate human confirmation through the authorized channel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create", "update"]},
                "record_id": {"type": "string", "format": "uuid"},
                "payload": {"type": "object"},
            },
            "required": ["operation", "payload"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api POST /v1/nonconformities/prepare",
    },
    "export_nonconformities": {
        "title": "Export nonconformities",
        "description": (
            "READ-only full JSON export of the nonconformity record set "
            "(backup/migration contract E-NC-06): version, generated_at, "
            "count and items."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/nonconformities/export",
    },
    "list_lmps": {
        "title": "List LMPs",
        "description": (
            "READ-only functional LMP list (orders tracked by "
            "Engineering) with period/branch/listing_type/status "
            "filters and pagination — delegated official TOTVS facts "
            "under Engineering rules."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
                "listing_type": {"type": "string"},
                "status": {"type": "string"},
                "page": {"type": "integer", "minimum": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps",
    },
    "get_lmp_summary": {
        "title": "Get LMP summary",
        "description": (
            "READ-only realized LMP KPIs (no goals/IDD): counts and "
            "lead-time aggregates for a period — official values only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps/summary",
    },
    "get_lmp_detail": {
        "title": "Get LMP detail",
        "description": (
            "READ-only functional detail of a single OV/LMP by "
            "sale_number: status, dates, proposal context and flags "
            "under Engineering rules."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sale_number": {"type": "string"},
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
            },
            "required": ["sale_number"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps/{sale_number}",
    },
    "get_lmp_history": {
        "title": "Get LMP history",
        "description": (
            "READ-only OV history by sale_number. view=events returns "
            "the audit event list; view=flow returns status "
            "transitions/lead-time flow — use it to explain why an LMP "
            "was late or how it progressed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sale_number": {"type": "string"},
                "view": {"type": "string", "enum": ["events", "flow"]},
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
                "revision": {"type": "string"},
            },
            "required": ["sale_number", "view"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": (
            "engineering-api GET /v1/lmps/{sale_number}/history/"
            "events|flow"
        ),
    },
    "get_lmp_goal_context": {
        "title": "Get LMP goal context",
        "description": (
            "READ-only goals context for the LMP dashboard — delegated "
            "to the Strategic Indicators owner; explains targets behind "
            "on-time/lead-time evaluation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps/goal-context",
    },
    "get_lmp_department_idd": {
        "title": "Get LMP department IDD",
        "description": (
            "READ-only departmental IDD score — delegated to the "
            "Strategic Indicators owner; optional competence (YYYY-MM) "
            "or period filter."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "competence": {"type": "string", "pattern": "^\\d{4}-(0[1-9]|1[0-2])$"},
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "branch": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps/department-idd",
    },
    "get_lmp_nc_streak": {
        "title": "Get LMP NC streak",
        "description": (
            "READ-only days-without-NC streak as published by the NC "
            "owner for the LMP dashboard — delegated, never recalculated."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/lmps/nonconformities/streak",
    },
    "get_product_structure": {
        "title": "Get product structure",
        "description": (
            "READ-only product structure/BOM by product_code — delegated "
            "to the Products owner (api-delpi) with the caller's Bearer; "
            "payload returned intact with honest availability."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_code": {"type": "string"},
                "max_depth": {"type": "integer", "minimum": 1, "maximum": 12},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "required": ["product_code"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/products/{product_code}/structure",
    },
    "create_nonconformity": {
        "title": "Create nonconformity",
        "description": (
            "ACT — creates a nonconformity through the official contract "
            "as the authenticated human. Requires confirmed=true after "
            "the user authorizes the candidate (present the normalized "
            "payload first via prepare_nonconformity_mutation). Optional "
            "idempotency_key deduplicates retries; postcondition is "
            "verified by read-back."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "payload": {"type": "object"},
                "confirmed": {"type": "boolean"},
                "idempotency_key": {"type": "string", "maxLength": 120},
            },
            "required": ["payload", "confirmed"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "explicit_user_authorization",
        "source": "engineering-api POST /v1/nonconformities",
    },
    "update_nonconformity": {
        "title": "Update nonconformity",
        "description": (
            "ACT — updates a nonconformity. The official contract is "
            "full-replace PUT: pass only the intended field changes in "
            "`changes`; the bridge fetches the current record and sends "
            "the merged full payload with optimistic locking "
            "(expected_updated_at). Conflicts return 409 — never loses "
            "fields. Requires confirmed=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "format": "uuid"},
                "changes": {"type": "object"},
                "confirmed": {"type": "boolean"},
                "expected_updated_at": {"type": "string"},
            },
            "required": ["record_id", "changes", "confirmed"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "explicit_user_authorization",
        "source": "engineering-api PUT /v1/nonconformities/{record_id}",
    },
    "delete_nonconformity": {
        "title": "Delete nonconformity",
        "description": (
            "ACT destructive — hard-deletes a nonconformity and its "
            "history (official cascade). HIGH RISK: requires "
            "confirmed=true only after presenting the record and "
            "receiving explicit user confirmation. Postcondition "
            "verified by read-back (404 expected)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "format": "uuid"},
                "confirmed": {"type": "boolean"},
            },
            "required": ["record_id", "confirmed"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "reinforced_explicit_confirmation",
        "destructive": True,
        "source": "engineering-api DELETE /v1/nonconformities/{record_id}",
    },
    "import_nonconformities": {
        "title": "Import nonconformities",
        "description": (
            "ACT destructive — JSON import that REPLACES the entire "
            "nonconformity record set (legacy semantics). Always run "
            "dry_run=true first and present the impact report; real "
            "import requires dry_run=false + confirm_replace=true + "
            "confirmed=true after explicit user authorization. The "
            "environment may block replacement — honor the refusal "
            "honestly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "object"}},
                "dry_run": {"type": "boolean"},
                "confirm_replace": {"type": "boolean"},
                "confirmed": {"type": "boolean"},
            },
            "required": ["items", "confirmed"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "reinforced_explicit_confirmation",
        "destructive": True,
        "source": "engineering-api POST /v1/nonconformities/import",
    },
    # --- Semantic surface (EVA.MCP.SEMANTIC.R1, plano 54) -----------------
    "get_context": {
        "title": "Get context",
        "description": (
            "EVA semantic discovery: working context, entities, actions, "
            "schemas-on-demand, risk/phase model and honest availability. "
            "Context is never authorization — call before any other tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "entity": {"type": "string"},
                "selected_ref": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "semantic catalog (engineering-api)",
    },
    "read": {
        "title": "Read",
        "description": (
            "Semantic official-data reads: entity + action dispatch over "
            "the typed registry (engineering|lmp|product|nonconformity). "
            "ref = primary identifier; filters/pagination per action — "
            "unknown actions and fields fail honestly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "action": {"type": "string"},
                "ref": {"type": "string"},
                "filters": {"type": "object"},
                "pagination": {"type": "object"},
                "projection": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["entity", "action"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "semantic dispatcher → official Engineering use cases",
    },
    "analyze": {
        "title": "Analyze",
        "description": (
            "Grounded Engineering analyses over official facts — each "
            "fact labeled OBSERVED|CALCULATED|INFERRED|UNKNOWN with "
            "verifiable method and provenance; never invents data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "analysis_type": {"type": "string"},
                "subject_refs": {"type": "array", "items": {"type": "string"}},
                "question": {"type": "string"},
                "parameters": {"type": "object"},
            },
            "required": ["analysis_type"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "semantic analyzer → official facts only",
    },
    "knowledge": {
        "title": "Knowledge",
        "description": (
            "Versioned, owner-authorized Engineering guidance (contract "
            "semantics, domain concepts, EVA operation). Not a facts "
            "source — unindexed topics answer not_implemented honestly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "task": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["topic"],
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api content/eva_engineering_knowledge.json",
    },
    "execute": {
        "title": "Execute",
        "description": (
            "Governed mutations: nonconformity create/update run "
            "directly when intent is unambiguous and authorized "
            "(idempotency + optimistic locking); phase=prepare "
            "validates without side effects. Destructive "
            "nonconformity.import requires prepare→sealed proposal→"
            "commit — confirmed=true alone is never proof."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "action": {"type": "string"},
                "target_ref": {"type": "string"},
                "payload": {"type": "object"},
                "changes": {"type": "object"},
                "idempotency_key": {"type": "string"},
                "expected_version": {"type": "string"},
                "proposal_ref": {"type": "string"},
                "phase": {"type": "string", "enum": ["act", "prepare", "commit"]},
            },
            "required": ["entity", "action"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "direct_when_unequivocal_sealed_proposal_for_destructive",
        "source": "semantic dispatcher → official Engineering use cases",
    },
    "delete": {
        "title": "Delete",
        "description": (
            "Governed destructive deletes: phase=prepare seals target + "
            "impact into a server-side proposal; phase=commit executes "
            "only with the exact proposal_ref after verifiable human "
            "confirmation. Never direct."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "target_ref": {"type": "string"},
                "proposal_ref": {"type": "string"},
                "phase": {"type": "string", "enum": ["prepare", "commit"]},
            },
            "required": ["entity", "target_ref"],
        },
        "output_schema": {"type": "object"},
        "read_only": False,
        "required_permission": ENGINEERING_ACCESS,
        "requires_human_confirmation": True,
        "confirmation_policy": "sealed_proposal_required",
        "destructive": True,
        "source": "semantic dispatcher → official Engineering use cases",
    },
}

# Tools legadas mantidas para compatibilidade durante a migração
# (plano 54 M2/M6): remoção só após consumidores migrados + gate
# separado. Cada nome aponta sua ação semântica equivalente.
_LEGACY_TOOL_SUPERSEDED_BY: dict[str, str] = {
    "get_catalog": "get_context",
    "get_engineering_home": "read(engineering.home)",
    "get_engineering_overview": "read(engineering.overview)",
    "list_lmps": "read(lmp.list)",
    "get_lmp_summary": "read(lmp.summary)",
    "get_lmp_detail": "read(lmp.detail)",
    "get_lmp_history": "read(lmp.history_events|history_flow)",
    "get_lmp_goal_context": "read(lmp.goal_context)",
    "get_lmp_department_idd": "read(lmp.department_idd)",
    "get_lmp_nc_streak": "read(lmp.nc_streak)",
    "get_product_structure": "read(product.structure)",
    "search_nonconformities": "read(nonconformity.search)",
    "get_nonconformity": "read(nonconformity.detail)",
    "get_nonconformity_history": "read(nonconformity.history)",
    "get_nonconformity_indicators": "read(nonconformity.indicators)",
    "get_nonconformity_tags": "read(nonconformity.tags)",
    "get_nonconformity_context": "read(nonconformity.context)",
    "export_nonconformities": "read(nonconformity.export)",
    "prepare_nonconformity_mutation": (
        "execute(nonconformity.*, phase=prepare)"
    ),
    "create_nonconformity": "execute(nonconformity.create)",
    "update_nonconformity": "execute(nonconformity.update)",
    "delete_nonconformity": "delete(nonconformity.delete)",
    "import_nonconformities": "execute(nonconformity.import)",
}
for _legacy_name, _semantic_target in _LEGACY_TOOL_SUPERSEDED_BY.items():
    _TOOL_CONTRACT[_legacy_name]["lifecycle"] = "deprecated"
    _TOOL_CONTRACT[_legacy_name]["superseded_by"] = _semantic_target

# Capacidades futuras — documentadas como não implementadas, nunca
# executáveis nem retornadas como tools.
_PLANNED_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "name": "engineering_products",
        "status": "not_implemented",
        "note": "Produtos DELPI — sem contrato oficial ainda.",
    },
    {
        "name": "engineering_bom",
        "status": "not_implemented",
        "note": "BOM/roteiros — sem contrato oficial ainda.",
    },
    {
        "name": "engineering_documents",
        "status": "not_implemented",
        "note": "Desenhos/especificações/inspeções — sem contrato oficial.",
    },
)


def _ok_result(data: Any, message: str = "ok") -> CallToolResult:
    payload = {"success": True, "message": message, "data": data}
    return mcp_tool_result(payload, is_error=False)


def _error_result(
    message: str,
    *,
    status_code: int = 400,
    data: dict | None = None,
    error_code: str | None = None,
) -> CallToolResult:
    err_data = dict(data or {})
    if error_code:
        err_data.setdefault("error_code", error_code)
    payload = {
        "success": False,
        "message": message,
        "status_code": status_code,
        "data": err_data,
    }
    return mcp_tool_result(payload, is_error=True)


def handle_tool_error(exc: Exception) -> CallToolResult:
    """Map adapter failures to honest typed results — never silent."""
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error_result(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error_result(
            "Forbidden",
            status_code=403,
            error_code="forbidden",
            data={"error_kind": "authz"},
        )
    if isinstance(exc, NcNotFoundError):
        return _error_result(
            "Nonconformity not found.",
            status_code=404,
            error_code="not_found",
            data={"error_kind": "not_found"},
        )
    if isinstance(exc, NcValidationError):
        return _error_result(
            str(exc),
            status_code=400,
            error_code="validation",
            data={"error_kind": "validation", "fields": exc.fields},
        )
    if isinstance(exc, NcConcurrencyError):
        return _error_result(
            str(exc),
            status_code=409,
            error_code="concurrency_conflict",
            data={"error_kind": "concurrency"},
        )
    if isinstance(exc, (NcUnsafeOperationError, EvaActDisabledError)):
        return _error_result(
            str(exc),
            status_code=403,
            error_code=(
                "act_disabled"
                if isinstance(exc, EvaActDisabledError)
                else "unsafe_operation"
            ),
            data={"error_kind": "unsafe_operation"},
        )
    if isinstance(exc, EvaConfirmationRequiredError):
        return _error_result(
            str(exc),
            status_code=400,
            error_code="confirmation_required",
            data={"error_kind": "confirmation"},
        )
    if isinstance(exc, NcRepositoryError):
        return _error_result(
            "Nonconformity source unavailable.",
            status_code=503,
            error_code="unavailable",
            data={"error_kind": "unavailable"},
        )
    if isinstance(exc, TimeoutError):
        return _error_result(
            "Upstream timeout.",
            status_code=504,
            error_code="timeout",
        )
    if isinstance(exc, (ValueError, LookupError)) and not isinstance(
        exc, KeyError
    ):
        return _error_result(
            str(exc),
            status_code=400,
            error_code="validation",
            data={"error_kind": "validation"},
        )
    logger.exception("eva_mcp_tool_error")
    return _error_result(
        "Upstream service error.",
        status_code=502,
        error_code="upstream_error",
    )


def build_mcp_request() -> Request:
    """Rebuild the adapter Request from the delpi_auth-established context."""
    context = require_mcp_context()
    return _shared_build_request(
        context=context,
        server=("engineering-api", 443),
        client=("127.0.0.1", 0),
    )


def _require_engineering_human():
    """Same gate as the REST routes: human principal + effective permission.

    Raises PermissionError — mapped by ``handle_tool_error`` (401/403).
    """
    context = require_mcp_context()
    if not context.user or not context.authorization:
        raise PermissionError("Unauthorized")
    user = context.user
    if getattr(user, "principal_type", None) != "user":
        raise PermissionError("MCP tools require a human principal.")
    if not getattr(user, "is_superadmin", False) and not has_any_permission(
        user, [ENGINEERING_ACCESS]
    ):
        raise PermissionError("Forbidden")
    return context


def _source_context(context) -> HomeSourceContext:
    access_token = str(
        getattr(context.user, "access_token", "") or ""
    ).strip()
    if not access_token:
        header = context.authorization
        access_token = (
            header.split(" ", 1)[1].strip()
            if header.lower().startswith("bearer ")
            else ""
        )
    if not access_token:
        raise PermissionError("Unauthorized")
    return HomeSourceContext(
        user_id=str(getattr(context.user, "id", "") or ""),
        access_token=access_token,
        request_id=get_request_id(),
    )


def _actor_from_context(context):
    """NcActor do humano autenticado — mesma projeção das rotas REST."""
    return nc_actor_from_principal(context.user)


def _env_flag_enabled(flag: str) -> bool:
    return os.getenv(flag, "").strip().lower() == "true"


def _eva_act_enabled() -> bool:
    return _env_flag_enabled(EVA_ACT_ENV_FLAG)


def _eva_act_delete_enabled() -> bool:
    return _eva_act_enabled() and _env_flag_enabled(EVA_ACT_DELETE_ENV_FLAG)


def _eva_act_import_enabled() -> bool:
    return _eva_act_enabled() and _env_flag_enabled(EVA_ACT_IMPORT_ENV_FLAG)


_ACT_TIER_FLAG = {
    "delete": EVA_ACT_DELETE_ENV_FLAG,
    "import": EVA_ACT_IMPORT_ENV_FLAG,
}


def _require_eva_act(act_class: str = "write") -> None:
    """Fail-closed por classe de risco — um booleano global nunca é
    autorização suficiente para todas as classes de operação.

    Tiers (todos exigem o master ``ENG_EVA_ACT_ENABLED``):
    - ``write``   — create/update não destrutivos;
    - ``delete``  — exclusão → ``ENG_EVA_ACT_DELETE_ENABLED``;
    - ``import``  — replace-all commit → ``ENG_EVA_ACT_IMPORT_ENABLED``.

    Sem a flag da classe a tool responde ``act_disabled`` honesto.
    """
    if not _eva_act_enabled():
        raise EvaActDisabledError(
            "EVA ACT indisponível neste ambiente "
            f"({EVA_ACT_ENV_FLAG} não habilitado)."
        )
    tier_flag = _ACT_TIER_FLAG.get(act_class)
    if tier_flag and not _env_flag_enabled(tier_flag):
        raise EvaActDisabledError(
            f"EVA ACT {act_class} indisponível neste ambiente "
            f"({tier_flag} não habilitado — aprovação operacional "
            "específica exigida)."
        )


def _require_confirmation(confirmed: bool | None) -> None:
    """Toda ACT exige a asserção explícita do chamador.

    ``confirmed=true`` significa que o agente apresentou a operação ao
    usuário e recebeu autorização — política de confirmação registrada
    no contrato da tool; a autorização efetiva continua sendo a Core.
    """
    if confirmed is not True:
        raise EvaConfirmationRequiredError(
            "Confirmação humana obrigatória: apresente a operação ao "
            "usuário e chame novamente com confirmed=true somente após "
            "autorização explícita."
        )


def _validate_period(
    start_date: str | None, end_date: str | None
) -> str | None:
    """Mesma validação de período das rotas /v1/lmps — sem contrato novo."""
    for name, value in (
        ("start_date", start_date),
        ("end_date", end_date),
    ):
        if value is not None and not _ISO_DATE_RE.match(value.strip()):
            return f"{name} inválida — use YYYY-MM-DD."
    if (
        start_date
        and end_date
        and _ISO_DATE_RE.match(start_date.strip())
        and _ISO_DATE_RE.match(end_date.strip())
        and start_date.strip() > end_date.strip()
    ):
        return "start_date não pode ser posterior a end_date."
    return None


def _lmp_result(
    result: dict, *, not_found_message: str
) -> CallToolResult:
    """Estados honestos das fontes LMP delegadas → resultado tipado."""
    status = result.get("status")
    if status == "forbidden":
        return _error_result(
            "Acesso negado pelo owner da fonte.",
            status_code=403,
            error_code="forbidden",
            data={"error_kind": "authz"},
        )
    if status == "not_found":
        return _error_result(
            not_found_message,
            status_code=404,
            error_code="not_found",
            data={"error_kind": "not_found"},
        )
    return _ok_result(result, "Consulta realizada com sucesso.")


# --- DISCOVERY ------------------------------------------------------------


def tool_get_catalog() -> CallToolResult:
    """EVA discovery catalog — live tools only; planning clearly marked."""
    try:
        _require_engineering_human()
        tools = []
        for name in MCP_TOOL_NAMES:
            contract = _TOOL_CONTRACT[name]
            tools.append(
                {
                    "name": name,
                    "title": contract["title"],
                    "description": contract["description"],
                    "capability_class": TOOL_CLASS[name],
                    "status": "implemented",
                    "input_schema": contract["input_schema"],
                    "output_schema": contract["output_schema"],
                    "read_only": contract["read_only"],
                    "required_permission": contract["required_permission"],
                    "requires_human_confirmation": contract.get(
                        "requires_human_confirmation", False
                    ),
                    "confirmation_policy": contract.get(
                        "confirmation_policy"
                    ),
                    "destructive": contract.get("destructive", False),
                    "lifecycle": contract.get("lifecycle", "stable"),
                    "superseded_by": contract.get("superseded_by"),
                    "source": contract.get("source"),
                    "owner": "engineering-api",
                }
            )
        data = {
            "assistant": EVA_FULL_NAME,
            "schema_version": "1.0",
            "tools": tools,
            "tool_class_legend": {
                "DISCOVERY": "Discovery only — never business data.",
                "READ": "Read-only official data — never persists.",
                "ANALYSIS": (
                    "Grounded analysis over official facts — labeled "
                    "OBSERVED|CALCULATED|INFERRED, never persists."
                ),
                "PREPARE": (
                    "Validation + projected diff only — zero side "
                    "effects; requires human confirmation to apply."
                ),
                "ACT": (
                    "Real mutation through the official Engineering "
                    "contract — requires confirmed=true after explicit "
                    "user authorization, live Core AuthZ and "
                    f"{EVA_ACT_ENV_FLAG} in the environment; "
                    "postcondition verified by read-back."
                ),
            },
            "write_tools": [
                name
                for name in MCP_TOOL_NAMES
                if TOOL_CLASS[name] == "ACT"
            ],
            "act_enabled": _eva_act_enabled(),
            "act_tiers": {
                "write": _eva_act_enabled(),
                "delete": _eva_act_delete_enabled(),
                "import": _eva_act_import_enabled(),
            },
            "agent_directives": (
                EvaAgentIntelligenceService.agent_directives()
            ),
            "planned_capabilities": list(_PLANNED_CAPABILITIES),
            "notes": [
                "Superfície semântica (EVA.MCP.SEMANTIC.R1): get_context, "
                "read, analyze, knowledge, execute, delete — 6 tools "
                "estáveis que despacham por entity+action tipadas; as "
                "tools legadas seguem ativas em deprecated durante a "
                "migração de consumidores.",
                "Tools ACT existem, mas só executam com confirmed=true "
                "após autorização explícita do usuário, AuthZ Core live "
                f"e {EVA_ACT_ENV_FLAG} habilitado no ambiente; "
                "act_enabled reflete o gate vigente.",
                "Gates por classe de risco: write (create/update) "
                f"exige {EVA_ACT_ENV_FLAG}; delete exige também "
                f"{EVA_ACT_DELETE_ENV_FLAG}; import replace-all exige "
                f"também {EVA_ACT_IMPORT_ENV_FLAG} — um booleano global "
                "não é autorização para todas as classes.",
                "delete_nonconformity e import_nonconformities são "
                "destrutivas: confirmação reforçada; import sem dry_run "
                "exige confirm_replace=true e respeita o bloqueio de "
                "ambiente do owner.",
                "Disponibilidade por fonte é preservada — unavailable ou "
                "forbidden NÃO significa ausência de dados.",
                "Metas/IDD só existem nos indicadores elegíveis "
                "(lmp_on_time, transforma_gross_savings).",
                "Permissões declaradas são requisito, não concessão — a "
                "autorização efetiva é da Core e dos owners downstream.",
                "EVA nunca acessa PostgreSQL diretamente nem usa "
                "identidade de serviço: o ator registrado em auditoria é "
                "sempre o humano autenticado.",
            ],
        }
        return _ok_result(data, "Catálogo de capacidades da EVA.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- READ tools -----------------------------------------------------------


async def tool_get_engineering_home() -> CallToolResult:
    try:
        context = _require_engineering_human()
        ctx = _source_context(context)
        home = await build_get_engineering_home_use_case().execute(ctx)
        return _ok_result(
            home.model_dump(),
            "Home de Engenharia autorizada do usuário.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def _validate_overview_filters(
    start_date: str | None,
    end_date: str | None,
    competence: str | None,
) -> str | None:
    """Mesma validação da rota REST — o MCP não inventa contrato."""
    for name, value in (
        ("start_date", start_date),
        ("end_date", end_date),
    ):
        if value is not None and not _ISO_DATE_RE.match(value.strip()):
            return f"{name} inválida — use YYYY-MM-DD."
    if (
        start_date
        and end_date
        and _ISO_DATE_RE.match(start_date.strip())
        and _ISO_DATE_RE.match(end_date.strip())
        and start_date.strip() > end_date.strip()
    ):
        return "start_date não pode ser posterior a end_date."
    if competence is not None and not _COMPETENCE_RE.match(
        competence.strip()
    ):
        return "competence inválida — use YYYY-MM."
    return None


async def tool_get_engineering_overview(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    competence: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_overview_filters(start_date, end_date, competence)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        ctx = _source_context(context)
        query = OverviewQuery(
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            competence=competence.strip() if competence else None,
            branch=branch.strip() if branch else None,
        )
        overview = await build_get_engineering_overview_use_case().execute(
            ctx, query=query
        )
        return _ok_result(
            overview.model_dump(),
            "Visão geral oficial de Engenharia.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- READ tools: nonconformities (E-NC-01..05, E-NC-11) -------------------


async def tool_search_nonconformities(
    *,
    status: str | None = None,
    sale_number: str | None = None,
    lmp_number: str | None = None,
    customer_name: str | None = None,
    product_code: str | None = None,
    problem_tag: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    try:
        _require_engineering_human()
        result = await nc_composer.build_list_nonconformities_use_case().execute(
            status=status,
            sale_number=sale_number,
            lmp_number=lmp_number,
            customer_name=customer_name,
            product_code=product_code,
            problem_tag=problem_tag,
            date_start=date_start,
            date_end=date_end,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        return _ok_result(result, "Não conformidades listadas.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_nonconformity(*, record_id: str) -> CallToolResult:
    try:
        _require_engineering_human()
        record = await nc_composer.build_get_nonconformity_use_case().execute(
            record_id
        )
        return _ok_result(record, "Detalhe da não conformidade.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_nonconformity_history(*, record_id: str) -> CallToolResult:
    try:
        _require_engineering_human()
        events = await nc_composer.build_list_nonconformity_history_use_case().execute(
            record_id
        )
        return _ok_result({"items": events}, "Histórico da não conformidade.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_nonconformity_indicators() -> CallToolResult:
    try:
        context = _require_engineering_human()
        ctx = _source_context(context)
        indicators = await nc_composer.build_get_nonconformity_indicators_use_case().execute(
            access_token=ctx.access_token
        )
        return _ok_result(indicators, "Indicadores de dias sem NC.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_nonconformity_tags() -> CallToolResult:
    try:
        _require_engineering_human()
        tags = await nc_composer.build_list_problem_tags_use_case().execute()
        return _ok_result({"items": tags}, "Catálogo de tags de problema.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_nonconformity_context(*, record_id: str) -> CallToolResult:
    try:
        context = _require_engineering_human()
        ctx = _source_context(context)
        payload = await nc_composer.build_get_nonconformity_context_use_case().execute(
            ctx, record_id=record_id
        )
        return _ok_result(payload, "Contexto OV/produtos da não conformidade.")
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_prepare_nonconformity_mutation(
    *,
    operation: str,
    payload: dict,
    record_id: str | None = None,
) -> CallToolResult:
    """EVA PREPARE — validation + projected diff, ZERO side effects."""
    try:
        _require_engineering_human()
        result = await nc_composer.build_prepare_nonconformity_mutation_use_case().execute(
            operation=operation,
            payload=payload or {},
            record_id=record_id,
        )
        return _ok_result(
            result,
            "Mutação analisada — nada foi gravado (PREPARE).",
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_export_nonconformities() -> CallToolResult:
    try:
        _require_engineering_human()
        data = await nc_composer.build_export_nonconformities_use_case().execute()
        return _ok_result(
            data, "Exportação JSON do acervo de não conformidades."
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- READ tools: LMPs e produtos (delegação governada aos owners) ------


async def tool_list_lmps(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    listing_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        query = LmpQuery(
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
            listing_type=listing_type.strip() if listing_type else None,
            status_filter=status.strip() if status else None,
            page=page,
            page_size=page_size,
        )
        result = await build_list_lmps_dashboard_use_case().execute(
            _source_context(context), query
        )
        return _lmp_result(
            result, not_found_message="Listagem de LMPs indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_summary(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        query = LmpQuery(
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
        )
        result = await build_get_lmp_summary_use_case().execute(
            _source_context(context), query
        )
        return _lmp_result(
            result, not_found_message="Resumo de LMPs indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_detail(
    *,
    sale_number: str,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        query = LmpQuery(
            sale_number=sale_number.strip(),
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
        )
        result = await build_get_lmp_detail_use_case().execute(
            _source_context(context), query
        )
        return _lmp_result(
            result,
            not_found_message=(
                "OV não encontrada na listagem de engenharia."
            ),
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_history(
    *,
    sale_number: str,
    view: str,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    revision: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        view_normalized = (view or "").strip().lower()
        if view_normalized not in {"events", "flow"}:
            return _error_result(
                "view inválida — use events|flow.",
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        query = LmpQuery(
            sale_number=sale_number.strip(),
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
            revision=revision.strip() if revision else None,
        )
        result = await build_get_lmp_history_use_case(
            view=view_normalized
        ).execute(_source_context(context), query)
        return _lmp_result(
            result,
            not_found_message=(
                "OV não encontrada na listagem de engenharia."
            ),
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_goal_context(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        result = await build_delegated_auxiliary_source().fetch_goal_context(
            _source_context(context),
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
        )
        return _lmp_result(
            result, not_found_message="Contexto de metas indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_department_idd(
    *,
    competence: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        if competence is not None and not _COMPETENCE_RE.match(
            competence.strip()
        ):
            return _error_result(
                "competence inválida — use YYYY-MM.",
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        error = _validate_period(start_date, end_date)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        result = await build_delegated_auxiliary_source().fetch_department_idd(
            _source_context(context),
            competence=competence.strip() if competence else None,
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            branch=branch.strip() if branch else None,
        )
        return _lmp_result(
            result, not_found_message="IDD departamental indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_lmp_nc_streak() -> CallToolResult:
    try:
        context = _require_engineering_human()
        result = await build_delegated_auxiliary_source().fetch_nc_streak(
            _source_context(context)
        )
        return _lmp_result(
            result, not_found_message="Streak de NC indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_product_structure(
    *,
    product_code: str,
    max_depth: int = 6,
    page_size: int = 200,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        code = (product_code or "").strip()
        if not code:
            return _error_result(
                "product_code obrigatório.",
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        result = await build_delegated_auxiliary_source().fetch_product_structure(
            _source_context(context),
            code=code,
            max_depth=max_depth,
            page_size=page_size,
        )
        return _lmp_result(
            result, not_found_message="Estrutura do produto indisponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_search_products(
    *,
    code: str | None = None,
    description: str | None = None,
    group_code: str | None = None,
    subgroup: str | None = None,
    product_type: str | None = None,
    customer_reference: str | None = None,
    page: int = 1,
    page_size: int = 50,
    sort: str | None = None,
    direction: str | None = None,
) -> CallToolResult:
    """read(product.search) — catálogo TOTVS via owner oficial."""
    try:
        context = _require_engineering_human()
        result = await build_delegated_auxiliary_source().fetch_product_search(
            _source_context(context),
            code=code,
            description=description,
            group_code=group_code,
            subgroup=subgroup,
            product_type=product_type,
            customer_reference=customer_reference,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )
        return _lmp_result(
            result, not_found_message="Nenhum produto encontrado."
        )
    except Exception as exc:
        return handle_tool_error(exc)


def _product_code_or_error(product_code: str | None):
    code = (product_code or "").strip()
    if not code:
        return None, _error_result(
            "product_code obrigatório.",
            status_code=400,
            error_code="validation",
            data={"error_kind": "validation"},
        )
    return code, None


async def tool_get_product_detail(*, product_code: str) -> CallToolResult:
    """read(product.detail) — ficha cadastral visão engineering."""
    try:
        context = _require_engineering_human()
        code, error = _product_code_or_error(product_code)
        if error:
            return error
        result = await build_delegated_auxiliary_source().fetch_product_detail(
            _source_context(context), code=code, view="engineering"
        )
        return _lmp_result(
            result, not_found_message=f"Produto {code} não encontrado."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_product_parents(
    *,
    product_code: str,
    max_depth: int | None = None,
    page: int = 1,
    page_size: int = 200,
) -> CallToolResult:
    """read(product.where_used) — BOM reversa oficial."""
    try:
        context = _require_engineering_human()
        code, error = _product_code_or_error(product_code)
        if error:
            return error
        result = await build_delegated_auxiliary_source().fetch_product_parents(
            _source_context(context),
            code=code,
            max_depth=max_depth,
            page=page,
            page_size=page_size,
        )
        return _lmp_result(
            result, not_found_message=f"Produto {code} não encontrado."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_product_suppliers(
    *,
    product_code: str,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """read(product.suppliers) — vínculos produto×fornecedor oficiais."""
    try:
        context = _require_engineering_human()
        code, error = _product_code_or_error(product_code)
        if error:
            return error
        result = await build_delegated_auxiliary_source().fetch_product_suppliers(
            _source_context(context), code=code, page=page, page_size=page_size
        )
        return _lmp_result(
            result, not_found_message=f"Produto {code} não encontrado."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_product_drawing(*, product_code: str) -> CallToolResult:
    """read(product.drawing) — metadados do desenho do acervo oficial."""
    try:
        context = _require_engineering_human()
        code, error = _product_code_or_error(product_code)
        if error:
            return error
        result = await build_delegated_auxiliary_source().fetch_product_drawing(
            _source_context(context), code=code
        )
        return _lmp_result(
            result, not_found_message=f"Produto {code} sem desenho disponível."
        )
    except Exception as exc:
        return handle_tool_error(exc)


async def tool_get_product_history(
    *,
    product_code: str,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    history_limit: int | None = None,
) -> CallToolResult:
    """read(product.history) — revisão cadastral + histórico de compras.

    Histórico de revisões cadastrais não possui contrato oficial
    (OWNER_BLOCKED — doc 63 §2.7): devolve os campos de revisão do
    cadastro mais o histórico de preço de compra quando autorizado,
    cada um rotulado com sua proveniência.
    """
    try:
        context = _require_engineering_human()
        code, error = _product_code_or_error(product_code)
        if error:
            return error
        source = build_delegated_auxiliary_source()
        ctx = _source_context(context)
        detail = await source.fetch_product_detail(
            ctx, code=code, view="engineering"
        )
        if detail.get("status") != "available":
            return _lmp_result(
                detail, not_found_message=f"Produto {code} não encontrado."
            )
        purchases = await source.fetch_product_purchase_price_history(
            ctx,
            code=code,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            history_limit=history_limit,
        )
        product = (detail.get("data") or {}).get("product") or {}
        data = {
            "cadastral_revision": {
                "status": "available",
                "current_revision": product.get("current_revision"),
                "last_revision_date": product.get("last_revision_date"),
                "source": "products.cadastral (TOTVS SB1)",
            },
            "purchase_price_history": purchases,
            "revision_history": {
                "status": "not_implemented",
                "reason": "Sem contrato oficial de histórico de revisões "
                "cadastrais (owner TOTVS/API DELPI) — doc 63 §2.7.",
            },
        }
        return _ok_result(
            {"status": "available", "data": data},
            "Histórico do produto carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- ACT tools: CRUD NC governado (E-NC-07..10) -------------------------


def _merged_update_payload(
    current: dict[str, Any], changes: dict[str, Any]
) -> dict[str, Any]:
    """Full-replace seguro: campos atuais + mudanças, chaves validadas.

    O contrato E-NC-08 é PUT full-replace — um payload parcial apagaria
    campos não informados. O merge parte do registro corrente e rejeita
    chaves fora do contrato (typo do agente nunca é descarte silencioso).
    """
    unknown = sorted(set(changes) - set(NC_WRITABLE_FIELDS))
    if unknown:
        raise NcValidationError(
            f"Campos fora do contrato NC: {', '.join(unknown)}.",
            fields={key: "unknown_field" for key in unknown},
        )
    payload = {
        field: current.get(field) for field in NC_WRITABLE_FIELDS
    }
    payload.update(changes)
    return payload


async def _create_nc_record(
    context,
    *,
    payload: dict,
    idempotency_key: str | None,
) -> dict:
    """Create NC via official use case + read-back postcondition.

    Shared by the legacy ACT tool and the semantic ``execute``
    dispatcher — governance (confirmation model) lives in each caller.
    """
    data = await nc_composer.build_create_nonconformity_use_case().execute(
        payload=payload or {},
        actor=_actor_from_context(context),
        idempotency_key=idempotency_key,
    )
    postcondition = {"verified": False}
    record_id = data.get("id")
    if record_id:
        try:
            read_back = (
                await nc_composer.build_get_nonconformity_use_case().execute(
                    record_id
                )
            )
            postcondition = {
                "verified": read_back is not None,
                "record_id": record_id,
                "check": "read_back",
            }
        except Exception:
            postcondition = {
                "verified": False,
                "record_id": record_id,
                "check": "read_back_failed",
            }
    return {**data, "postcondition": postcondition}


async def tool_create_nonconformity(
    *,
    payload: dict,
    confirmed: bool = False,
    idempotency_key: str | None = None,
) -> CallToolResult:
    """EVA ACT — create via contrato oficial com postcondition read-back."""
    try:
        context = _require_engineering_human()
        _require_eva_act()
        _require_confirmation(confirmed)
        data = await _create_nc_record(
            context, payload=payload, idempotency_key=idempotency_key
        )
        return _ok_result(data, "Não conformidade criada com sucesso.")
    except Exception as exc:
        return handle_tool_error(exc)


async def _update_nc_record(
    context,
    *,
    record_id: str,
    changes: dict,
    expected_updated_at: str | None,
) -> dict:
    """Update NC — safe full-replace merge + optimistic locking + read-back."""
    if not isinstance(changes, dict) or not changes:
        raise NcValidationError(
            "changes é obrigatório (objeto com os campos a alterar).",
            fields={"changes": "required"},
        )
    current = await nc_composer.build_get_nonconformity_use_case().execute(
        record_id
    )
    merged = _merged_update_payload(current, changes)
    etag = expected_updated_at or current.get("updated_at")
    data = await nc_composer.build_update_nonconformity_use_case().execute(
        record_id=record_id,
        payload=merged,
        actor=_actor_from_context(context),
        expected_updated_at=etag,
    )
    postcondition = {"verified": False}
    try:
        read_back = await nc_composer.build_get_nonconformity_use_case().execute(
            record_id
        )
        postcondition = {
            "verified": read_back is not None
            and read_back.get("updated_at") != current.get("updated_at"),
            "record_id": record_id,
            "check": "read_back",
        }
    except Exception:
        postcondition = {
            "verified": False,
            "record_id": record_id,
            "check": "read_back_failed",
        }
    return {**data, "postcondition": postcondition}


async def tool_update_nonconformity(
    *,
    record_id: str,
    changes: dict,
    confirmed: bool = False,
    expected_updated_at: str | None = None,
) -> CallToolResult:
    """EVA ACT — update full-replace com merge + optimistic locking."""
    try:
        context = _require_engineering_human()
        _require_eva_act()
        _require_confirmation(confirmed)
        data = await _update_nc_record(
            context,
            record_id=record_id,
            changes=changes,
            expected_updated_at=expected_updated_at,
        )
        return _ok_result(data, "Não conformidade atualizada com sucesso.")
    except Exception as exc:
        return handle_tool_error(exc)


async def _delete_nc_record(context, *, record_id: str) -> dict:
    """Delete NC (hard-delete + cascade) with prior impact + read-back."""
    current = await nc_composer.build_get_nonconformity_use_case().execute(
        record_id
    )
    data = await nc_composer.build_delete_nonconformity_use_case().execute(
        record_id
    )
    postcondition = {"verified": False}
    try:
        await nc_composer.build_get_nonconformity_use_case().execute(record_id)
        postcondition = {
            "verified": False,
            "check": "read_back_still_present",
        }
    except NcNotFoundError:
        postcondition = {"verified": True, "check": "read_back_gone"}
    return {
        **data,
        "deleted_record_summary": {
            "sale_number": current.get("sale_number"),
            "lmp_number": current.get("lmp_number"),
            "status": current.get("status"),
            "defect_description": current.get("defect_description"),
        },
        "postcondition": postcondition,
    }


async def tool_delete_nonconformity(
    *,
    record_id: str,
    confirmed: bool = False,
) -> CallToolResult:
    """EVA ACT destrutiva — delete com impacto prévio + postcondition."""
    try:
        context = _require_engineering_human()
        _require_eva_act("delete")
        _require_confirmation(confirmed)
        data = await _delete_nc_record(context, record_id=record_id)
        return _ok_result(data, "Não conformidade excluída com sucesso.")
    except Exception as exc:
        return handle_tool_error(exc)


async def _import_nc_records(
    context,
    *,
    items: list,
    dry_run: bool,
    confirm_replace: bool,
) -> dict:
    """Import NC via official use case — dry_run or governed replace."""
    if not isinstance(items, list) or not items:
        raise NcValidationError(
            "items é obrigatório (lista de não conformidades).",
            fields={"items": "required"},
        )
    result = await nc_composer.build_import_nonconformities_use_case().execute(
        items=items,
        actor=_actor_from_context(context),
        dry_run=bool(dry_run),
        confirm_replace=bool(confirm_replace),
    )
    report = result.to_dict()
    return {
        **report,
        "postcondition": {
            "verified": True,
            "check": "import_report",
            "deleted": report.get("deleted"),
            "created": report.get("created"),
            "skipped": report.get("skipped"),
            "errors": report.get("errors"),
        },
    }


async def tool_import_nonconformities(
    *,
    items: list,
    confirmed: bool = False,
    dry_run: bool = True,
    confirm_replace: bool = False,
) -> CallToolResult:
    """EVA ACT destrutiva — import com dry-run padrão + confirmação
    reforçada. A substituição total só ocorre com dry_run=false +
    confirm_replace=true + confirmed=true; o bloqueio de ambiente do
    owner (ENG_NC_IMPORT_REPLACE_ENABLED) continua valendo."""
    try:
        context = _require_engineering_human()
        # dry_run não tem efeitos colaterais (equivale a PREPARE) —
        # tier write basta; a substituição real exige o tier import
        # (flag específica) + confirmação reforçada.
        if dry_run is True:
            _require_eva_act()
        else:
            _require_eva_act("import")
            _require_confirmation(confirmed)
        report = await _import_nc_records(
            context,
            items=items,
            dry_run=dry_run,
            confirm_replace=confirm_replace,
        )
        return _ok_result(
            report,
            "Importação de não conformidades concluída."
            if not dry_run
            else "Simulação de importação concluída (dry_run).",
        )
    except Exception as exc:
        return handle_tool_error(exc)
