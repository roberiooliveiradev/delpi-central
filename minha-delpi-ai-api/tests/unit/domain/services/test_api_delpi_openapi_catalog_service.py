from app.domain.services.api_delpi_openapi_catalog_service import (
    build_openapi_catalog_markdown,
)


def test_build_openapi_catalog_markdown_groups_by_tag():
    markdown = build_openapi_catalog_markdown(
        {
            "paths": {
                "/products/search": {
                    "get": {
                        "tags": ["products"],
                        "operationId": "search_products",
                        "summary": "Buscar produtos no Protheus",
                    }
                },
                "/financial/rol": {
                    "get": {
                        "tags": ["Financeiro"],
                        "operationId": "get_rol_financial_rol_get",
                        "summary": "ROL financeiro",
                    }
                },
            }
        }
    )

    assert "Buscar produtos no Protheus" in markdown
    assert "`GET` | `/financial/rol`" in markdown
    assert "**Rotas:** 2" in markdown
