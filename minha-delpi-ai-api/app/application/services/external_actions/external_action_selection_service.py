import re


class ExternalActionSelectionService:
    def __init__(self, repository):
        self.repository = repository

    def select_action(self, message: str) -> dict | None:
        candidates = self.repository.find_candidate_actions(message, limit=12)

        if not candidates:
            return None

        product_code = self._extract_numeric_code(message)

        if product_code:
            product_action = self._select_product_action(candidates)

            if product_action:
                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": product_action["actionId"],
                        "parameters": self._build_parameters(product_action, product_code),
                    },
                    "reason": "A pergunta solicita informações operacionais de produto via OpenAPI.",
                }

        return None

    def _extract_numeric_code(self, message: str) -> str | None:
        match = re.search(r"\b\d{4,}\b", message or "")

        if not match:
            return None

        return match.group(0)

    def _select_product_action(self, candidates: list[dict]) -> dict | None:
        preferred_terms = [
            "analysis",
            "análise",
            "analise",
            "detail",
            "details",
            "search",
            "product",
            "products",
            "produto",
        ]

        for term in preferred_terms:
            for candidate in candidates:
                haystack = " ".join(
                    str(candidate.get(key) or "")
                    for key in ["actionId", "operationId", "path", "summary", "description"]
                ).lower()

                if term in haystack and candidate.get("method") == "GET":
                    return candidate

        return candidates[0] if candidates else None

    def _build_parameters(self, action: dict, code: str) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")
            location = parameter.get("in")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"code", "product_code", "productcode", "codigo", "item", "id"}:
                parameters[name] = code

            if location == "query" and lowered in {"query", "q", "search", "description"}:
                parameters[name] = code

        return parameters
