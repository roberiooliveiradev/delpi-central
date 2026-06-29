from app.application.services.audit_5s.catalog_service import fallback_catalog_version


def test_fallback_catalog_version_filial_01() -> None:
    assert fallback_catalog_version("01") == 2


def test_fallback_catalog_version_filial_02() -> None:
    assert fallback_catalog_version("02") == 1


def test_fallback_catalog_version_unknown_defaults_to_v1() -> None:
    assert fallback_catalog_version("99") == 1
