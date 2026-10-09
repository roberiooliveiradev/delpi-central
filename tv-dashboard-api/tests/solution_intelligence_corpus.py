"""P6 frozen baseline corpus — solution-intelligence route-miss scenarios.

Frozen BEFORE the Phase 6 implementation (see roadmap §39/§40). The same
cases drive the baseline run (pre-implementation behavior) and the
candidate run (post-implementation). Do not edit expectations to make the
candidate pass — corpus changes invalidate the delta.

Each case exercises ``GptActionsDispatchService.search_data_routes`` with:
- ``tv_routes``: what the TV allowlist suggest returns (hit or miss);
- ``core_result``: what the bounded Core /solutions lookup would return —
  list of safe-projection dicts, an error marker, or ``no_auth``
  (no user Bearer available at the caller);
- ``expect``: the contract the candidate must satisfy. Baseline records
  whatever the current code produces; expectations are the §39 contract.
"""

# Error markers understood by the corpus gateway stub.
CORE_TIMEOUT = "timeout"
CORE_5XX = "upstream_5xx"
CORE_INVALID = "invalid_schema"
CORE_UNAUTHORIZED = "unauthorized"
CORE_NO_AUTH = "no_auth"

_SAFE = {"id", "name", "description", "category", "accessible"}


def _solution(id_, name, description="", category=None, accessible=True):
    return {
        "id": id_,
        "name": name,
        "description": description,
        "category": category,
        "accessible": accessible,
        # Extra Core fields that MUST NOT leak into the bounded projection.
        "routes": [{"path": "/x", "label": "x"}],
        "permissions": [{"code": "x.view", "name": "x"}],
        "dependencies": ["core-api"],
        "manifestInternals": {"secret": "should-not-propagate"},
    }


P6_CORPUS = [
    # 1. direct TV route hit → no ecosystem escalation.
    {
        "id": "route_hit",
        "query": "otd comercial",
        "tv_routes": [{"operationId": "get_otd_commercial", "label": "OTD"}],
        "core_result": [_solution("commercial", "Portal Comercial")],
        "expect": {"gap": "TV_ROUTE_FOUND", "core_calls": 0},
    },
    # 2. route synonym hit → same, zero Core calls.
    {
        "id": "route_synonym_hit",
        "query": "entregas no prazo",
        "tv_routes": [{"operationId": "get_otd_commercial", "label": "OTD"}],
        "core_result": [_solution("supplies", "Suprimentos")],
        "expect": {"gap": "TV_ROUTE_FOUND", "core_calls": 0},
    },
    # 3. miss + exactly one matching solution.
    {
        "id": "miss_one_solution",
        "query": "canal de denúncia",
        "tv_routes": [],
        "core_result": [
            _solution("canal-denuncia", "Canal de Denúncia",
                      "Registro e tratamento de denúncias.", "institutional"),
        ],
        "expect": {
            "gap": "SOLUTION_FOUND_NO_TV_ROUTE",
            "candidates": ["canal-denuncia"],
            "miss_invariant": True,
        },
    },
    # 4. miss + multiple plausible solutions → ambiguous, no first-pick.
    {
        "id": "miss_ambiguous",
        "query": "dashboard financeiro",
        "tv_routes": [],
        "core_result": [
            _solution("dashboard-financial", "Dashboard Financeiro",
                      "Indicadores financeiros.", "financial"),
            _solution("financial", "Financeiro",
                      "Gestão financeira.", "financial"),
        ],
        "expect": {
            "gap": "AMBIGUOUS_SOLUTIONS",
            "candidates": ["dashboard-financial", "financial"],
            "deterministic_order": True,
        },
    },
    # 5. miss + Core healthy + nothing relevant → typed no-evidence.
    {
        "id": "miss_no_evidence",
        "query": "teletransporte quântico",
        "tv_routes": [],
        "core_result": [_solution("commercial", "Portal Comercial")],
        "expect": {"gap": "NO_SOLUTION_EVIDENCE", "no_absence_claim": True},
    },
    # 6. miss + single candidate with accessible=false → restricted.
    {
        "id": "miss_restricted",
        "query": "auditoria interna",
        "tv_routes": [],
        "core_result": [
            _solution("auditoria-5s", "Auditoria 5S",
                      "Auditorias de programa 5S.", None, accessible=False),
        ],
        "expect": {
            "gap": "SOLUTION_FOUND_ACCESS_RESTRICTED",
            "candidates": ["auditoria-5s"],
            "no_execution": True,
        },
    },
    # 7. Core unavailable → CONTRACT_GAP, miss invariant preserved.
    {
        "id": "core_timeout",
        "query": "ebitda",
        "tv_routes": [],
        "core_result": CORE_TIMEOUT,
        "expect": {"gap": "CONTRACT_GAP", "miss_invariant": True},
    },
    # 8. Core invalid payload → CONTRACT_GAP.
    {
        "id": "core_invalid",
        "query": "ebitda",
        "tv_routes": [],
        "core_result": CORE_INVALID,
        "expect": {"gap": "CONTRACT_GAP", "miss_invariant": True},
    },
    # 9. route with canonical domain metadata (hit) → still zero calls.
    {
        "id": "route_hit_with_domain",
        "query": "carteira por filial",
        "tv_routes": [
            {"operationId": "get_billing_portfolio_by_branch",
             "category": "commercial"}
        ],
        "core_result": [_solution("commercial", "Portal Comercial")],
        "expect": {"gap": "TV_ROUTE_FOUND", "core_calls": 0},
    },
    # 10. miss where caller holds no Bearer (defense in depth).
    {
        "id": "miss_no_auth",
        "query": "ebitda",
        "tv_routes": [],
        "core_result": CORE_NO_AUTH,
        "expect": {"gap_in": ["CONTRACT_GAP", "NO_SOLUTION_EVIDENCE"],
                   "no_execution": True, "miss_invariant": True},
    },
    # 11. known solution without any TV integration route.
    {
        "id": "miss_known_solution_no_tv",
        "query": "comitê de ética",
        "tv_routes": [],
        "core_result": [
            _solution("comite-etica-conduta", "Comitê de Ética e Conduta",
                      "Comitê de ética.", "institutional"),
        ],
        "expect": {
            "gap": "SOLUTION_FOUND_NO_TV_ROUTE",
            "candidates": ["comite-etica-conduta"],
            "no_execution": True,
        },
    },
    # 12. restricted among multiple → candidates bounded, never guessed.
    {
        "id": "miss_mixed_access",
        "query": "ética",
        "tv_routes": [],
        "core_result": [
            _solution("codigo-etica", "Código de Ética",
                      "Código de ética.", "institutional", accessible=False),
            _solution("comite-etica-conduta", "Comitê de Ética e Conduta",
                      "Comitê.", "institutional"),
        ],
        "expect": {
            "gap_in": ["AMBIGUOUS_SOLUTIONS",
                       "SOLUTION_FOUND_NO_TV_ROUTE"],
            "no_execution": True,
        },
    },
]

# Candidates must never copy these fields out of the Core payload.
FORBIDDEN_CANDIDATE_FIELDS = {
    "routes", "permissions", "dependencies", "manifestInternals",
}
