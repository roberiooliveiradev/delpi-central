"""Constants for the R11 billing-exclusion roster (doc 126 §§16.2/17).

Historical selection reproduced 1:1 against the 09/2026 artifact
``NF a desconsiderar.xlsb`` / ``Planilha2`` (branch 01): 11 SD2 item rows /
R$ 97.462,71 / 11 documents (doc 84 §5.5, doc 85 BR-R11-001/002).

Selection evidence (doc 85 BR-R11-002):
- competence axis ``D2_EMISSAO``;
- observed intersection ``D2_GRUPO='9035' AND D2_TES='594'`` — the two
  predicates are indistinguishable inside the artifact competence
  (E11b: which one the operator filtered is a residual decision);
- the roster is an INVESTIGATIVE review list — membership never means
  confirmed error, and nothing is excluded automatically from CPV,
  billing, DRE or any other calculation (D-02, doc 126 §16.2).

Views: ``candidates`` = rows matching the observed historical criteria;
``out_of_criteria`` = in-competence rows related to the criteria
(group 9035 XOR TES 594 — DV-R11-04); ``all`` = both populations, each
with its own totals — never blended into one number.
"""

VIEW_CANDIDATES = "candidates"
VIEW_OUT_OF_CRITERIA = "out_of_criteria"
VIEW_ALL = "all"
VIEWS = (VIEW_CANDIDATES, VIEW_OUT_OF_CRITERIA, VIEW_ALL)

# Observed historical criteria (doc 85 BR-R11-002). Kept verbatim as
# the roster predicate; NOT promoted to a universal official rule while
# E11b remains a residual decision of the Controladoria owner.
ROSTER_PRODUCT_GROUP = "9035"
ROSTER_TES = "594"

# Selection states per line.
SELECTION_MATCHES = "matches_historical_criteria"
SELECTION_OUT_OF_CRITERIA = "related_out_of_criteria"

# Cost status — D2_CUSTO1 = 0 with F4_ESTOQUE='N' is the EXPECTED
# structural condition for a TES that does not move stock (doc 85
# BR-R11-003): it explains the absence in CPV/kardex and is never a
# divergence by itself.
COST_STATUS_STRUCTURAL_ZERO = "structural_zero_expected"
COST_STATUS_STANDARD = "standard"

# Finding states — never CONFIRMED_ERROR (doc 126 §16).
FINDING_POSSIBLE_DIVERGENCE = "POSSIBLE_DIVERGENCE"

# Divergence-rule catalog (doc 126 §16.2).
RULE_HISTORICAL_SELECTION = "DV-R11-01"
RULE_STRUCTURAL_ZERO_COST = "DV-R11-02"
RULE_MISSING_STOCK_SIBLING = "DV-R11-03"
RULE_RELATED_OUT_OF_CRITERIA = "DV-R11-04"

FINDINGS_CAP = 500

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50

SORT_FIELD_DATE = "date"
SORT_FIELD_DOCUMENT = "document"
SORT_FIELD_PRODUCT = "product"
SORT_FIELD_TOTAL_VALUE = "total_value"
SORT_FIELDS = (
    SORT_FIELD_DATE,
    SORT_FIELD_DOCUMENT,
    SORT_FIELD_PRODUCT,
    SORT_FIELD_TOTAL_VALUE,
)

SORT_DIR_ASC = "asc"
SORT_DIR_DESC = "desc"
SORT_DIRS = (SORT_DIR_ASC, SORT_DIR_DESC)

REPORT_ID = "billing-exclusion-roster"
REPORT_LABEL = "R11 — Notas Fiscais a Desconsiderar"
