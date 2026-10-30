"""Constants for the R10 cost-center-expenses report (doc 126 §§5/16/17).

Historical selection reproduced 1:1 against the 09/2026 artifact
``CC matriz.xlsb`` / ``SCAGQGA0.XML`` (branch 01): 353 SD1 item rows /
R$ 169.704,12 / 139 documents / 46 cost centers (doc 84 §R10, doc 126 §2).

Selection evidence (doc 85 BR-R10-001..005):
- competence axis ``D1_DTDIGIT`` (never ``D1_EMISSAO``);
- the thirteen TES codes the historical export excluded;
- raw-material lines (``D1_TP='MP'``) out of the expense universe;
- six benefit lines (health/dental, TES 046, type GG, group 4100,
  no cost center) out of the expense universe.

The same predicate, evaluated over the full competence, defines the two
universes: ``calculation`` (inside the official selection) and
``investigation`` (in-competence rows the selection excluded). Totals are
never combined across universes (doc 127 §3, invariant B).
"""

UNIVERSE_CALCULATION = "calculation"
UNIVERSE_INVESTIGATION = "investigation"
UNIVERSES = (UNIVERSE_CALCULATION, UNIVERSE_INVESTIGATION)

# Observed historical exclusions (doc 85 BR-R10-003 / doc 126 §2). The
# narrated "twelve TES" vs the observed thirteen remains a documented
# residual — the thirteen-value set is what reproduces the artifact and
# is preserved verbatim, not promoted to a general rule beyond it.
EXCLUDED_TES = (
    "001",
    "003",
    "016",
    "020",
    "030",
    "040",
    "080",
    "083",
    "085",
    "120",
    "159",
    "204",
    "318",
)

RAW_MATERIAL_PRODUCT_TYPE = "MP"

# Benefit lines the historical selection dropped (doc 85 BR-R10-005):
# TES 046, product type GG, group 4100 (health/dental benefits), no cost
# center. Reproduces exactly the six excluded rows for 2026-09/01.
BENEFIT_TES = "046"
BENEFIT_PRODUCT_TYPE = "GG"
BENEFIT_PRODUCT_GROUP = "4100"

# Why an investigation row sits outside the calculation universe.
EXCLUSION_TES = "tes_excluded"
EXCLUSION_RAW_MATERIAL = "raw_material_product"
EXCLUSION_BENEFIT = "benefit_line"
EXCLUSION_NOT_EVALUATED = "not_evaluated"

# Listing views (doc 126 §16.3): divergences = rows with at least one
# POSSIBLE_DIVERGENCE finding; unclassified = rows without a homologated
# cost class (DV-R10-05 — every row today, D-01).
VIEW_ALL = "all"
VIEW_DIVERGENCES = "divergences"
VIEW_UNCLASSIFIED = "unclassified"
VIEWS = (VIEW_ALL, VIEW_DIVERGENCES, VIEW_UNCLASSIFIED)

# Cost class — the Direto/Indireto/Adm column is a manual annotation on
# the historical artifact, NOT a Protheus field (D-01). No row carries a
# homologated class until the E10a catalog exists.
COST_CLASS_UNCLASSIFIED = "UNCLASSIFIED"

# Finding states — never CONFIRMED_ERROR (doc 126 §16).
FINDING_POSSIBLE_DIVERGENCE = "POSSIBLE_DIVERGENCE"

# Divergence-rule catalog (doc 126 §16.1). implemented=False marks rules
# blocked by E10a (homologated CC→class catalog) — they are declared so
# consumers can explain coverage honestly, never silently skipped.
RULE_MP_WITH_COST_CENTER = "DV-R10-01"
RULE_COST_CENTER_NOT_IN_CATALOG = "DV-R10-02"
RULE_PRODUCT_COST_CENTER_MISMATCH = "DV-R10-03"
RULE_MISSING_COST_CENTER = "DV-R10-04"
RULE_UNCLASSIFIED_COST_CLASS = "DV-R10-05"
RULE_DIVERGENT_COST_CLASS = "DV-R10-06"

FINDINGS_CAP = 500

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50

SORT_FIELD_DATE = "date"
SORT_FIELD_DOCUMENT = "document"
SORT_FIELD_COST_CENTER = "cost_center"
SORT_FIELD_PRODUCT = "product"
SORT_FIELD_TOTAL_VALUE = "total_value"
SORT_FIELDS = (
    SORT_FIELD_DATE,
    SORT_FIELD_DOCUMENT,
    SORT_FIELD_COST_CENTER,
    SORT_FIELD_PRODUCT,
    SORT_FIELD_TOTAL_VALUE,
)

SORT_DIR_ASC = "asc"
SORT_DIR_DESC = "desc"
SORT_DIRS = (SORT_DIR_ASC, SORT_DIR_DESC)

REPORT_ID = "cost-center-expenses"
REPORT_LABEL = "R10 — Despesas por Centro de Custo"
