from scripts.audit_llm_provider_coupling import scan_violations


def test_scan_violations_is_clean_for_current_tree():
    violations = scan_violations()
    assert violations == []
