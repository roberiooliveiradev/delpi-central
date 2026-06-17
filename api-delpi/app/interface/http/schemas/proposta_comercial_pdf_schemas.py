from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PropostaComercialPdfContatoOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = None
    departamento: str | None = None
    email: str | None = None
    telefone: str | None = None


class PropostaComercialPdfCondicoesOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str | None = None
    icms: str | None = None
    ipi: str | None = None
    frete: str | None = None
    embalagem: str | None = None


class PropostaComercialPdfVendedorOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = None
    cargo: str | None = None
    email: str | None = None
    telefone: str | None = None


class PropostaComercialPdfItemOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: str
    descricao: str | None = None
    referencia_cliente: str | None = None
    ncm: str | None = None


class PropostaComercialPdfColunasItensRotulos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: str | None = None
    produto: str | None = None
    descricao: str | None = None
    referencia_cliente: str | None = None
    ncm: str | None = None
    quantidade: str | None = None
    valor_bruto: str | None = None
    valor_liquido: str | None = None
    total: str | None = None
    prazo: str | None = None
    lote_minimo: str | None = None


class PropostaComercialPdfResumoRotulos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero_ov: str | None = None
    data: str | None = None
    versao: str | None = None
    total_r_mil: str | None = None
    empresa: str | None = None
    cliente: str | None = None


class PropostaComercialPdfRotulosOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    colunas_itens: PropostaComercialPdfColunasItensRotulos | None = None
    resumo: PropostaComercialPdfResumoRotulos | None = None
    total_proposta: str | None = None


class PropostaComercialPdfExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observacoes: str | None = None
    contato: PropostaComercialPdfContatoOverrides | None = None
    condicoes: PropostaComercialPdfCondicoesOverrides | None = None
    vendedor: PropostaComercialPdfVendedorOverrides | None = None
    itens: list[PropostaComercialPdfItemOverrides] | None = None
    rotulos: PropostaComercialPdfRotulosOverrides | None = None

    def to_overrides_dict(self) -> dict:
        payload = self.model_dump(exclude_none=True)
        for key in ("contato", "condicoes", "vendedor"):
            nested = payload.get(key)
            if isinstance(nested, dict) and not nested:
                payload.pop(key, None)
        itens = payload.get("itens")
        if isinstance(itens, list):
            sanitized_items: list[dict] = []
            for item in itens:
                if not isinstance(item, dict):
                    continue
                item_key = str(item.get("item") or "").strip()
                if not item_key:
                    continue
                sanitized = {"item": item_key}
                for field in ("descricao", "referencia_cliente", "ncm"):
                    value = item.get(field)
                    if value is not None:
                        sanitized[field] = value
                if len(sanitized) > 1:
                    sanitized_items.append(sanitized)
            if sanitized_items:
                payload["itens"] = sanitized_items
            else:
                payload.pop("itens", None)
        rotulos = payload.get("rotulos")
        if isinstance(rotulos, dict):
            sanitized_rotulos: dict = {}
            for section in ("colunas_itens", "resumo"):
                nested = rotulos.get(section)
                if isinstance(nested, dict) and nested:
                    sanitized_rotulos[section] = nested
            total_proposta = rotulos.get("total_proposta")
            if isinstance(total_proposta, str) and total_proposta.strip():
                sanitized_rotulos["total_proposta"] = total_proposta.strip()
            if sanitized_rotulos:
                payload["rotulos"] = sanitized_rotulos
            else:
                payload.pop("rotulos", None)
        return payload
