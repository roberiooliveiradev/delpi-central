from __future__ import annotations

import math
import re
from typing import Any

from app.shared.utils.spreadsheet_date import format_date_ddmmyyyy


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _digits_only(value: Any) -> str:
    return re.sub(r"\D", "", _as_str(value))


class PropostaComercialFormatter:
    """Formatação canônica de campos exibidos nas propostas comerciais."""

    @staticmethod
    def trim(value: Any) -> str:
        return _as_str(value)

    @staticmethod
    def format_cnpj(value: Any) -> str | None:
        digits = _digits_only(value)
        if len(digits) != 14:
            return _as_str(value) or None
        return (
            f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/"
            f"{digits[8:12]}-{digits[12:14]}"
        )

    @staticmethod
    def format_cep(value: Any) -> str | None:
        digits = _digits_only(value)
        if len(digits) != 8:
            return _as_str(value) or None
        return f"{digits[0:5]}-{digits[5:8]}"

    @staticmethod
    def format_phone(value: Any) -> str | None:
        raw = _as_str(value)
        if not raw:
            return None

        digits = _digits_only(raw)
        if not digits:
            return raw

        if raw.startswith("(") and ")" in raw:
            return raw

        if len(digits) == 11:
            return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"
        if len(digits) == 10:
            return f"({digits[0:2]}) {digits[2:6]}-{digits[6:10]}"
        if len(digits) == 8:
            return f"{digits[0:4]}-{digits[4:8]}"
        return raw

    @staticmethod
    def format_ncm(value: Any) -> str | None:
        digits = _digits_only(value)
        if len(digits) != 8:
            return _as_str(value) or None
        return f"{digits[0:4]}.{digits[4:6]}.{digits[6:8]}"

    @staticmethod
    def format_currency(value: Any) -> str | None:
        if value is None or value == "":
            return None
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return None
        formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"

    @staticmethod
    def format_date(value: Any) -> str | None:
        return format_date_ddmmyyyy(value)

    @staticmethod
    def format_integer_days(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        return int(number)

    @staticmethod
    def format_minimum_lot(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        if not float(number).is_integer():
            return int(number)
        return int(number)

    @staticmethod
    def format_numero_ov(oportunidade: Any) -> str:
        code = _as_str(oportunidade)
        if not code:
            return ""
        return f"OV{code}"

    @classmethod
    def format_list_item(cls, row: dict) -> dict:
        return {
            "proposta_interna": cls.trim(row.get("proposta_interna")),
            "numero_ov": cls.format_numero_ov(row.get("oportunidade")),
            "oportunidade": cls.trim(row.get("oportunidade")),
            "versao": cls.trim(row.get("versao")),
            "data": cls.format_date(row.get("data_proposta")),
            "cliente": cls.trim(row.get("cliente_nome")),
            "filial": cls.trim(row.get("filial")),
            "quantidade_itens": cls.format_integer_days(row.get("quantidade_itens")) or 0,
        }

    @classmethod
    def format_detail(
        cls,
        header: dict,
        items: list[dict],
        *,
        empresa_site: str,
    ) -> dict:
        soma_valores_r_mil = header.get("soma_valores_r_mil")
        return {
            "cabecalho": {
                "proposta_interna": cls.trim(header.get("proposta_interna")),
                "numero_ov": cls.format_numero_ov(header.get("oportunidade")),
                "oportunidade": cls.trim(header.get("oportunidade")),
                "versao": cls.trim(header.get("versao")),
                "revisao_oportunidade": cls.trim(header.get("revisao_oportunidade")),
                "data": cls.format_date(header.get("data_proposta")),
                "validade_dias": cls.format_integer_days(header.get("validade_dias")),
                "filial": cls.trim(header.get("filial")),
                "status": cls.trim(header.get("status")),
                "soma_valores_r_mil": cls.format_currency(soma_valores_r_mil),
                "soma_valores_r_mil_numerico": (
                    float(soma_valores_r_mil) if soma_valores_r_mil not in (None, "") else None
                ),
            },
            "empresa": {
                "nome": cls.trim(header.get("empresa_nome")),
                "cnpj": cls.format_cnpj(header.get("empresa_cnpj")),
                "endereco": cls.trim(header.get("empresa_endereco")),
                "bairro": cls.trim(header.get("empresa_bairro")),
                "cidade": cls.trim(header.get("empresa_cidade")),
                "uf": cls.trim(header.get("empresa_uf")),
                "cep": cls.format_cep(header.get("empresa_cep")),
                "telefone": cls.format_phone(header.get("empresa_telefone")),
                "site": empresa_site,
            },
            "cliente": {
                "codigo": cls.trim(header.get("cliente_codigo")),
                "loja": cls.trim(header.get("cliente_loja")),
                "nome": cls.trim(header.get("cliente_nome")),
                "cnpj": cls.format_cnpj(header.get("cliente_cnpj")),
                "endereco": cls.trim(header.get("cliente_endereco")),
                "bairro": cls.trim(header.get("cliente_bairro")),
                "cidade": cls.trim(header.get("cliente_cidade")),
                "uf": cls.trim(header.get("cliente_uf")),
                "cep": cls.format_cep(header.get("cliente_cep")),
                "telefone": cls.format_phone(header.get("cliente_telefone")),
            },
            "contato": {
                "codigo": cls.trim(header.get("contato_codigo")),
                "nome": cls.trim(header.get("contato_nome")),
                "email": cls.trim(header.get("contato_email")),
                "telefone": cls.format_phone(header.get("contato_telefone")),
                "departamento": cls.trim(header.get("contato_departamento")),
            },
            "condicoes": {
                "codigo": cls.trim(header.get("condicao_codigo")),
                "descricao": cls.trim(header.get("condicao_descricao")),
            },
            "vendedor": {
                "codigo": cls.trim(header.get("vendedor_codigo")),
                "nome": cls.trim(header.get("vendedor_nome")),
                "email": cls.trim(header.get("vendedor_email")),
                "telefone": cls.format_phone(header.get("vendedor_telefone")),
                "cargo": cls.trim(header.get("vendedor_cargo")),
            },
            "observacoes": cls.trim(header.get("observacoes")),
            "itens": [cls.format_item(item) for item in items],
        }

    @classmethod
    def format_item(cls, row: dict) -> dict:
        return {
            "item": cls.trim(row.get("item")),
            "produto": cls.trim(row.get("produto")),
            "descricao": cls.trim(row.get("descricao")),
            "referencia_cliente": cls.trim(row.get("referencia_cliente")),
            "ncm": cls.format_ncm(row.get("ncm")),
            "quantidade": float(row.get("quantidade") or 0),
            "unidade": cls.trim(row.get("unidade")),
            "preco_unitario": cls.format_currency(row.get("preco_unitario")),
            "preco_unitario_numerico": float(row.get("preco_unitario") or 0),
            "valor_total": cls.format_currency(row.get("valor_total")),
            "valor_total_numerico": float(row.get("valor_total") or 0),
            "prazo_dias": cls.format_integer_days(row.get("prazo_dias")),
            "lote_minimo": cls.format_minimum_lot(row.get("lote_minimo")),
        }

    @staticmethod
    def normalize_observacoes(value: Any) -> str:
        text = _as_str(value)
        if not text:
            return ""
        return text.replace("\r\n", "\n").replace("\r", "\n")
