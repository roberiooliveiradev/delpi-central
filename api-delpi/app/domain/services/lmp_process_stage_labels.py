LMP_PROCESS_LABELS: dict[str, str] = {
    "000001": "Abertura",
    "000002": "Oportunidade",
    "000003": "Engenharia",
}

LMP_STAGE_LABELS: dict[str, str] = {
    "000001": "Abertura",
    "000002": "Oportunidade",
    "000003": "Engenharia",
    "000008": "Amostra engenharia",
    "000012": "Lançamento / homologação",
    "000013": "Acompanhamento",
}


def label_for_process(code: str | None) -> str | None:
    normalized = str(code or "").strip()
    if not normalized:
        return None
    return LMP_PROCESS_LABELS.get(normalized, normalized)


def label_for_stage(code: str | None) -> str | None:
    normalized = str(code or "").strip()
    if not normalized:
        return None
    return LMP_STAGE_LABELS.get(normalized, normalized)
