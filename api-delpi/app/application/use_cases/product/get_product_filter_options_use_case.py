# app/application/use_cases/product/get_product_filter_options_use_case.py
"""Opções de filtro do catálogo de produtos — grupos e tipos distintos
observados no cadastro oficial (SB1), sem fonte paralela."""


class GetProductFilterOptionsUseCase:
    def __init__(self, repository) -> None:
        self._repository = repository

    def execute(self) -> dict:
        options = self._repository.fetch_product_filter_options()
        return {
            "groups": options.get("groups") or [],
            "types": options.get("types") or [],
        }
