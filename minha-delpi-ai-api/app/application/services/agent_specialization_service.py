from copy import deepcopy


SPECIALIZATION_PRESETS: dict[str, dict] = {
    "rh": {
        "label": "Recursos Humanos",
        "domain": "recursos-humanos",
        "knowledgeDomains": ["recursos-humanos"],
        "knowledgeNamespaces": ["global:rh"],
        "knowledgeCategories": ["rh"],
        "knowledgeTags": ["rh", "ferias", "beneficios"],
        "guidelineCategories": ["rh", "behavior"],
        "allowedTools": ["get_current_user", "search_knowledge_base"],
        "includeGlobalKnowledge": True,
    },
    "ti": {
        "label": "Tecnologia da Informação",
        "domain": "ti",
        "knowledgeDomains": ["ti"],
        "knowledgeNamespaces": ["global:ti"],
        "knowledgeCategories": ["ti"],
        "knowledgeTags": ["ti", "suporte", "acesso"],
        "guidelineCategories": ["ti", "behavior"],
        "allowedTools": [
            "get_current_user",
            "get_allowed_apps",
            "get_allowed_routes",
            "search_knowledge_base",
        ],
        "includeGlobalKnowledge": True,
    },
    "financeiro": {
        "label": "Financeiro",
        "domain": "financeiro",
        "knowledgeDomains": ["financeiro"],
        "knowledgeNamespaces": ["global:financeiro"],
        "knowledgeCategories": ["financeiro"],
        "knowledgeTags": ["financeiro", "orcamento"],
        "guidelineCategories": ["financeiro", "behavior"],
        "allowedTools": ["get_current_user", "search_knowledge_base"],
        "includeGlobalKnowledge": True,
    },
    "comercial": {
        "label": "Comercial",
        "domain": "comercial",
        "knowledgeDomains": ["comercial"],
        "knowledgeNamespaces": ["global:comercial"],
        "knowledgeCategories": ["comercial"],
        "knowledgeTags": ["comercial", "vendas"],
        "guidelineCategories": ["comercial", "behavior"],
        "allowedTools": ["get_current_user", "search_knowledge_base"],
        "includeGlobalKnowledge": True,
    },
    "juridico": {
        "label": "Jurídico",
        "domain": "juridico",
        "knowledgeDomains": ["juridico"],
        "knowledgeNamespaces": ["global:juridico"],
        "knowledgeCategories": ["juridico", "politica"],
        "knowledgeTags": ["juridico", "compliance"],
        "guidelineCategories": ["juridico", "behavior", "politica"],
        "allowedTools": ["get_current_user", "search_knowledge_base"],
        "includeGlobalKnowledge": True,
    },
}


class AgentSpecializationService:
    def list_presets(self) -> list[dict]:
        return [
            {
                "key": key,
                **value,
            }
            for key, value in SPECIALIZATION_PRESETS.items()
        ]

    def get_preset(self, preset_key: str | None) -> dict | None:
        normalized = str(preset_key or "").strip().lower()

        if not normalized:
            return None

        preset = SPECIALIZATION_PRESETS.get(normalized)

        if not preset:
            return None

        return deepcopy({"presetKey": normalized, **preset})

    def parse(self, raw) -> dict | None:
        if not isinstance(raw, dict):
            return None

        if not raw.get("enabled", True):
            return None

        preset = self.get_preset(raw.get("presetKey"))

        merged = deepcopy(preset) if preset else {}

        for field in (
            "label",
            "domain",
            "knowledgeDomains",
            "knowledgeNamespaces",
            "knowledgeCategories",
            "knowledgeTags",
            "guidelineCategories",
            "allowedTools",
        ):
            if raw.get(field) is not None:
                merged[field] = self._normalize_list_field(raw.get(field))

        if "includeGlobalKnowledge" in raw:
            merged["includeGlobalKnowledge"] = bool(raw.get("includeGlobalKnowledge"))

        if raw.get("presetKey"):
            merged["presetKey"] = str(raw.get("presetKey")).strip().lower()

        merged["enabled"] = True

        if not merged.get("domain") and not merged.get("knowledgeDomains"):
            return None

        return merged

    def normalize_payload(self, payload: dict | None) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("specialization payload must be an object")

        enabled = bool(payload.get("enabled", True))

        if not enabled:
            return {"enabled": False}

        preset_key = str(payload.get("presetKey") or "").strip().lower() or None
        preset = self.get_preset(preset_key) if preset_key else None

        normalized = {
            "enabled": True,
            "presetKey": preset_key,
            "label": str(payload.get("label") or (preset or {}).get("label") or "").strip(),
            "domain": str(payload.get("domain") or (preset or {}).get("domain") or "").strip(),
            "knowledgeDomains": self._normalize_list_field(
                payload.get("knowledgeDomains") or (preset or {}).get("knowledgeDomains"),
            ),
            "knowledgeNamespaces": self._normalize_list_field(
                payload.get("knowledgeNamespaces") or (preset or {}).get("knowledgeNamespaces"),
            ),
            "knowledgeCategories": self._normalize_list_field(
                payload.get("knowledgeCategories") or (preset or {}).get("knowledgeCategories"),
            ),
            "knowledgeTags": self._normalize_list_field(
                payload.get("knowledgeTags") or (preset or {}).get("knowledgeTags"),
            ),
            "guidelineCategories": self._normalize_list_field(
                payload.get("guidelineCategories") or (preset or {}).get("guidelineCategories"),
            ),
            "allowedTools": self._normalize_list_field(
                payload.get("allowedTools") or (preset or {}).get("allowedTools"),
            ),
            "includeGlobalKnowledge": bool(
                payload.get(
                    "includeGlobalKnowledge",
                    (preset or {}).get("includeGlobalKnowledge", True),
                )
            ),
        }

        if not normalized["domain"] and not normalized["knowledgeDomains"]:
            raise ValueError("domain or knowledgeDomains is required when specialization is enabled")

        return normalized

    def build_rag_filters(self, specialization: dict | None, base_filters: dict) -> dict:
        filters = dict(base_filters or {})

        if not specialization:
            return filters

        if not specialization.get("includeGlobalKnowledge", True):
            filters["include_global"] = False

        curatorial = dict(filters.get("curatorial") or {})

        if specialization.get("domain"):
            curatorial.setdefault("domains", [])
            if specialization["domain"] not in curatorial["domains"]:
                curatorial["domains"].append(specialization["domain"])

        for key in ("knowledgeDomains", "knowledgeNamespaces", "knowledgeCategories", "knowledgeTags"):
            target_key = {
                "knowledgeDomains": "domains",
                "knowledgeNamespaces": "namespaces",
                "knowledgeCategories": "categories",
                "knowledgeTags": "tags",
            }[key]

            values = specialization.get(key) or []

            if values:
                curatorial[target_key] = list(
                    dict.fromkeys((curatorial.get(target_key) or []) + values),
                )

        if curatorial:
            filters["curatorial"] = curatorial

        return filters

    def _normalize_list_field(self, value) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            items = value
        else:
            items = str(value).split(",")

        normalized = []

        for item in items:
            cleaned = str(item).strip().lower()

            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)

        return normalized
