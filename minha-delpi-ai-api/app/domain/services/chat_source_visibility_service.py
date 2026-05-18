def should_hide_source_from_client(source: dict | None) -> bool:
    if not source:
        return True

    scope = str(source.get("scope") or "").strip().lower()

    if scope == "global":
        return True

    if scope in {"agent_source", "project_source", "session_source"}:
        return False

    if any(source.get(key) for key in ("agentKey", "projectId", "sessionId", "attachmentId")):
        return False

    source_type = str(source.get("sourceType") or "").strip().lower()

    if source_type == "global":
        return True

    if source_type in {
        "admin_upload",
        "admin_preview_upload",
        "diretriz",
        "guideline",
        "admin_guideline",
    }:
        return True

    source_ref = str(source.get("sourceRef") or "").strip().lower()

    if source_ref.startswith("global:"):
        return True

    if not scope:
        return True

    return False


def filter_client_visible_sources(sources: list[dict] | None) -> list[dict]:
    if not sources:
        return []

    return [source for source in sources if not should_hide_source_from_client(source)]
