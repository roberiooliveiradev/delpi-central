"""Task 17 (DELIA-C3-LOCAL-ORCHESTRATION-NATIVE-ASSESSMENT-REWORK-01):
the native_assessment instruction contract must name every legitimate
owner-native designation resolver class.

Task 16/17 replay proved the over-firing mechanism: the decision rule
told the model to scan the capability list for documentation, guide,
catalog, context, methodology or knowledge READs that could resolve a
descriptive designation — but owner designation resolvers are also
DISCOVERY-class capabilities (role owner_vocabulary_discovery) such
as DAVI discover_delpi_information and TÉO/VISTA get_catalog.
A literal scan found no listed noun on those surfaces, concluded that
no resolver existed, and selected foreign_evidence_required even
though the selected owner could resolve the designation itself.

The contract under test is semantic (the instruction text is the
contract consumed by the governed stage). These assertions pin the
contract elements the diagnosis proved necessary — they are not
keyword routing: the model still decides the status; the contract
merely stops hiding a legitimate resolver class from its scan.
"""

from __future__ import annotations

import json
from pathlib import Path

_RESOURCE = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "orchestration_instructions.delpi.json"
)
_KEY = "delia.capability_orchestration.native_assessment"


def _instruction() -> str:
    return json.loads(_RESOURCE.read_text(encoding="utf-8"))[
        "instructions"
    ][_KEY]


def test_discovery_role_is_a_designation_resolver_class():
    """The designation-resolver scan must include DISCOVERY-role
    capabilities — the class that actually resolves descriptive
    designations on DAVI/TÉO/VISTA surfaces."""
    text = _instruction()
    assert "owner_vocabulary_discovery" in text
    assert "DISCOVERY" in text


def test_governed_actions_are_natively_self_contained():
    """Create/modify/prepare goals on the owner are never a foreign
    designation problem — missing user inputs resolve via
    clarification, not foreign evidence."""
    text = _instruction()
    assert "governed actions are natively self-contained" in text
    assert "clarified with the user" in text


def test_selected_resolver_capability_never_triggers_exception():
    """When the selected capability IS the owner discovery/catalog
    read, foreign designation evidence cannot be required — the
    capability resolves designations by design."""
    text = _instruction()
    assert "already resolve designations by design" in text


def test_owner_native_ordering_is_not_a_foreign_problem():
    """Latest/most-recent/all/count over the owner's own records is a
    native owner query — an ordinal, not an unresolved designation."""
    text = _instruction()
    assert "latest" in text and "native" in text


def test_decision_rule_is_the_final_block():
    """Recency placement (proven on this model family in Task 16):
    the DECISION RULE must appear after the status vocabulary so the
    governing rule is the last contract text the model reads."""
    text = _instruction()
    assert text.index("DECISION RULE") > text.index('"inconclusive"')


def test_canonical_status_vocabulary_unchanged():
    """The remediation must not alter the four-status contract."""
    text = _instruction()
    for status in (
        "sufficient",
        "foreign_evidence_required",
        "corroboration_requested",
        "inconclusive",
    ):
        assert f'"{status}"' in text
