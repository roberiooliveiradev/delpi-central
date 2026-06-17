"""Avaliação de confiabilidade de fontes — Playbook pesquisa web, Fase 3."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from app.domain.services.web_search_query_service import USELESS_RESULT_SOURCES


@dataclass(frozen=True)
class WebSourceEvaluation:
    source_type: str
    quality_score: float
    is_official: bool
    hostname: str


class ChatWebSearchSourceEvaluationService:
    _QUALITY_BY_TYPE: dict[str, float] = {
        "official": 0.93,
        "government": 0.95,
        "manufacturer": 0.95,
        "recognized_distributor": 0.8,
        "technical_article": 0.7,
        "news": 0.65,
        "forum": 0.4,
        "unknown": 0.2,
    }

    _GOVERNMENT_SUFFIXES = (".gov.br", ".gov", ".leg.br", ".jus.br")

    _MANUFACTURER_DOMAINS: frozenset[str] = frozenset(
        {
            "weg.net",
            "siemens.com",
            "se.com",
            "abb.com",
            "rockwellautomation.com",
            "omron.com",
            "festo.com",
            "te.com",
            "schneider-electric.com",
        }
    )

    _OFFICIAL_STANDARDS_HOSTS: frozenset[str] = frozenset(
        {
            "abnt.org.br",
            "iso.org",
            "iec.ch",
            "inmetro.gov.br",
        }
    )

    _MANUFACTURER_DOMAIN_SUFFIXES: tuple[str, ...] = (
        ".weg.net",
        ".siemens.com",
        ".abb.com",
        ".omron.com",
        ".festo.com",
        ".rockwellautomation.com",
        ".schneider-electric.com",
    )

    _DISTRIBUTOR_MARKERS = (
        "digikey",
        "mouser",
        "rs-online",
        "rsdelivers",
        "distribuidor",
        "distributor",
        "element14",
        "farnell",
        "arrow.com",
    )

    _FORUM_MARKERS = (
        "reddit.com",
        "stackoverflow.com",
        "quora.com",
        "forum",
        "answers.yahoo",
        "stackexchange",
    )

    _NEWS_MARKERS = (
        "g1.globo",
        "valor.globo",
        "reuters.com",
        "bbc.com",
        "cnn.com",
        "estadao",
        "folha.uol",
        "infomoney",
    )

    _TECHNICAL_MARKERS = (
        "wikipedia.org",
        "wikimedia",
        "ieee.org",
        "researchgate",
        "sciencedirect",
    )

    @classmethod
    def evaluate_url(cls, url: str, *, title: str = "") -> WebSourceEvaluation:
        hostname = cls._hostname(url)
        haystack = f"{hostname} {title}".lower()
        source_type = cls._classify(hostname, haystack)
        score = cls._QUALITY_BY_TYPE.get(source_type, 0.2)
        is_official = source_type in {"official", "government", "manufacturer"}

        if source_type == "official":
            score = max(score, 0.92)

        return WebSourceEvaluation(
            source_type=source_type,
            quality_score=score,
            is_official=is_official,
            hostname=hostname,
        )

    @classmethod
    def enrich_payload(cls, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return payload

        if str(payload.get("searchStatus") or "") != "success":
            return payload

        results = payload.get("results")

        if not isinstance(results, list):
            return payload

        prefer_official = payload.get("preferOfficial") is True
        enriched: list[dict] = []
        excluded_sources: list[dict] = []
        types_seen: set[str] = set()
        has_trusted = False

        for item in results:
            if not isinstance(item, dict):
                continue

            if str(item.get("source") or "") in USELESS_RESULT_SOURCES:
                continue

            url = str(item.get("url") or "").strip()

            if not url:
                continue

            title = str(item.get("title") or "").strip()
            evaluation = cls.evaluate_url(url, title=title)
            types_seen.add(evaluation.source_type)

            if evaluation.is_official:
                has_trusted = True

            if prefer_official and evaluation.quality_score < 0.4:
                excluded_sources.append(
                    {
                        "hostname": evaluation.hostname,
                        "url": url,
                        "reason": "fonte de baixa confiabilidade para consulta oficial",
                    }
                )
                continue

            enriched.append(
                {
                    **item,
                    "sourceType": evaluation.source_type,
                    "qualityScore": evaluation.quality_score,
                    "isOfficial": evaluation.is_official,
                }
            )

        enriched.sort(
            key=lambda row: float(row.get("qualityScore") or 0),
            reverse=True,
        )

        payload = {**payload, "results": enriched}
        payload["sourceEvaluation"] = cls._build_summary(
            types_seen=types_seen,
            has_trusted=has_trusted,
            prefer_official=prefer_official,
            excluded_sources=excluded_sources,
            source_count=len(enriched),
        )

        return payload

    @classmethod
    def format_warnings_block(cls, payload: dict | None) -> str | None:
        if not isinstance(payload, dict):
            return None

        evaluation = payload.get("sourceEvaluation")

        if not isinstance(evaluation, dict):
            return None

        warnings = [
            str(item).strip()
            for item in (evaluation.get("warnings") or [])
            if str(item).strip()
        ]

        if not warnings:
            return None

        lines = ["", "## Observação sobre as fontes", ""]

        lines.extend(f"- {warning}" for warning in warnings)

        return "\n".join(lines)

    @classmethod
    def _build_summary(
        cls,
        *,
        types_seen: set[str],
        has_trusted: bool,
        prefer_official: bool,
        excluded_sources: list[dict],
        source_count: int,
    ) -> dict:
        confidence = cls._resolve_confidence(
            has_trusted=has_trusted,
            types_seen=types_seen,
            source_count=source_count,
        )
        warnings: list[str] = []

        if prefer_official and not has_trusted:
            warnings.append(
                "Não encontramos página oficial ou de fabricante entre os resultados; "
                "valide em um site do fabricante antes de decisões críticas."
            )

        if "forum" in types_seen and confidence != "high":
            warnings.append(
                "Parte dos resultados veio de fóruns ou comunidades — use como apoio, não como fonte única."
            )

        if excluded_sources:
            warnings.append(
                f"{len(excluded_sources)} fonte(s) de baixa confiabilidade foram omitidas da lista principal."
            )

        if confidence == "low":
            warnings.append(
                "A confiança geral das fontes é baixa; considere ampliar a busca ou restringir a sites oficiais."
            )

        return {
            "confidence": confidence,
            "sourceTypes": sorted(types_seen),
            "warnings": warnings,
            "excludedSources": excluded_sources,
        }

    @classmethod
    def _resolve_confidence(
        cls,
        *,
        has_trusted: bool,
        types_seen: set[str],
        source_count: int,
    ) -> str:
        if source_count == 0:
            return "low"

        if has_trusted:
            return "high"

        if types_seen <= {"forum", "unknown"} or types_seen == {"unknown"}:
            return "low"

        if "recognized_distributor" in types_seen or "technical_article" in types_seen:
            return "medium"

        return "medium"

    @classmethod
    def _is_government_host(cls, host: str) -> bool:
        normalized = host.lower()

        if normalized in {"gov.br", "leg.br", "jus.br"}:
            return True

        return any(normalized.endswith(suffix) for suffix in cls._GOVERNMENT_SUFFIXES)

    @classmethod
    def _classify(cls, hostname: str, haystack: str) -> str:
        host = hostname.lower()

        if host in cls._OFFICIAL_STANDARDS_HOSTS:
            return "official"

        if cls._is_government_host(host):
            return "government"

        if host in cls._MANUFACTURER_DOMAINS or any(
            host.endswith(suffix) for suffix in cls._MANUFACTURER_DOMAIN_SUFFIXES
        ):
            return "manufacturer"

        if ".pdf" in haystack:
            if any(marker in host for marker in cls._MANUFACTURER_DOMAINS) or any(
                host.endswith(suffix) for suffix in cls._MANUFACTURER_DOMAIN_SUFFIXES
            ):
                return "official"

            if any(host.endswith(suffix) for suffix in cls._GOVERNMENT_SUFFIXES):
                return "official"

        if any(marker in haystack for marker in cls._FORUM_MARKERS):
            return "forum"

        if any(marker in haystack for marker in cls._DISTRIBUTOR_MARKERS):
            return "recognized_distributor"

        if any(marker in haystack for marker in cls._TECHNICAL_MARKERS):
            return "technical_article"

        if any(marker in haystack for marker in cls._NEWS_MARKERS):
            return "news"

        if host.endswith(".edu") or host.endswith(".edu.br"):
            return "technical_article"

        if "blog" in host or "medium.com" in host:
            return "news"

        return "unknown"

    @staticmethod
    def _hostname(url: str) -> str:
        hostname = urlparse(str(url or "").strip()).hostname or str(url or "").strip()

        if hostname.startswith("www."):
            return hostname[4:]

        return hostname or "fonte"
