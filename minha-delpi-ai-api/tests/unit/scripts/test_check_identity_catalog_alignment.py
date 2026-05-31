from scripts.check_identity_catalog_alignment import main


def test_identity_catalog_alignment_script_passes():
    assert main() == 0
