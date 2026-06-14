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


class PropostaComercialPdfExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observacoes: str | None = None
    contato: PropostaComercialPdfContatoOverrides | None = None
    condicoes: PropostaComercialPdfCondicoesOverrides | None = None
    vendedor: PropostaComercialPdfVendedorOverrides | None = None

    def to_overrides_dict(self) -> dict:
        payload = self.model_dump(exclude_none=True)
        for key in ("contato", "condicoes", "vendedor"):
            nested = payload.get(key)
            if isinstance(nested, dict) and not nested:
                payload.pop(key, None)
        return payload
