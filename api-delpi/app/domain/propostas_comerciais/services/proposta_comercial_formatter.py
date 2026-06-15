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
    def format_inscricao_estadual(value: Any) -> str | None:
        raw = _as_str(value)
        return raw or None

    @staticmethod
    def format_icms_rate(value: Any) -> str | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            raw = _as_str(value)
            return raw or None
        if math.isnan(number):
            return None
        if float(number).is_integer():
            return f"{int(number)}%"
        return f"{number:g}%"

    @staticmethod
    def format_frete(value: Any) -> str:
        code = _as_str(value).upper()
        labels = {
            "C": "CIF — frete por conta do vendedor",
            "F": "FOB — frete por conta do comprador",
        }
        return labels.get(code, code or "—")

    @staticmethod
    def format_embalagem(value: Any) -> str:
        code = _as_str(value)
        if code == "1":
            return "Embalagem padrão DELPI"
        return code or "—"

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

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        return number

    FONTE_VALOR_LIQUIDO = "calculo_formacao_preco_icms_efetivo_pis_cofins"
    CODIGO_PLANILHA_REDUCAO_ICMS = "000007"
    PERCENTUAL_REDUCAO_ICMS = 90.0
    FATOR_ICMS_APOS_REDUCAO = 0.10

    @classmethod
    def _aplica_reducao_icms_planilha(cls, codigo_planilha_formacao: Any) -> bool:
        return cls.trim(codigo_planilha_formacao) == cls.CODIGO_PLANILHA_REDUCAO_ICMS

    @classmethod
    def _resolve_aliquota_icms_efetiva(
        cls,
        *,
        aliquota_icms_original: float | None,
        codigo_planilha_formacao: Any,
    ) -> float:
        original = aliquota_icms_original if aliquota_icms_original is not None else 0.0
        if cls._aplica_reducao_icms_planilha(codigo_planilha_formacao):
            return original * cls.FATOR_ICMS_APOS_REDUCAO
        return original

    @classmethod
    def _resolve_status_calculo_valor_liquido(
        cls,
        *,
        id_formacao_preco: str | None,
        aliquota_icms: float | None,
        aliquota_icms_raw: Any,
        aliquota_pis_cofins: float | None,
        aliquota_pis_cofins_raw: Any,
    ) -> str:
        if not id_formacao_preco:
            return "SEM_FORMACAO_PRECO"
        if aliquota_icms_raw in (None, "") or aliquota_icms is None:
            return "SEM_ICMS"
        if aliquota_pis_cofins_raw in (None, "") or aliquota_pis_cofins is None:
            return "SEM_PIS_COFINS"
        return "OK"

    @classmethod
    def _compute_valor_liquido_comercial(
        cls,
        *,
        valor_bruto_r_mil: float | None,
        id_formacao_preco: str | None,
        aliquota_icms_raw: Any,
        aliquota_pis_cofins_raw: Any,
        codigo_planilha_formacao: Any = None,
        aliquota_icms_efetiva_raw: Any = None,
        valor_apos_icms_raw: Any = None,
        valor_liquido_raw: Any = None,
    ) -> dict[str, Any]:
        id_formacao = cls.trim(id_formacao_preco) or None
        aliquota_icms_original = cls._optional_float(
            aliquota_icms_raw if aliquota_icms_raw not in (None, "") else None
        )
        aliquota_pis_cofins = cls._optional_float(aliquota_pis_cofins_raw)
        codigo_planilha = cls.trim(codigo_planilha_formacao) or None
        aplica_reducao = cls._aplica_reducao_icms_planilha(codigo_planilha)
        percentual_reducao = cls.PERCENTUAL_REDUCAO_ICMS if aplica_reducao else 0.0
        status = cls._resolve_status_calculo_valor_liquido(
            id_formacao_preco=id_formacao,
            aliquota_icms=aliquota_icms_original,
            aliquota_icms_raw=aliquota_icms_raw,
            aliquota_pis_cofins=aliquota_pis_cofins,
            aliquota_pis_cofins_raw=aliquota_pis_cofins_raw,
        )

        if valor_bruto_r_mil is None or status == "SEM_FORMACAO_PRECO":
            return {
                "codigo_planilha_formacao": codigo_planilha,
                "aliquota_icms_original": aliquota_icms_original,
                "aliquota_icms": aliquota_icms_original,
                "aplica_reducao_icms": aplica_reducao,
                "percentual_reducao_icms": percentual_reducao,
                "aliquota_icms_efetiva": None,
                "aliquota_pis_cofins": aliquota_pis_cofins,
                "valor_apos_icms_r_mil": None,
                "valor_apos_icms_r_mil_formatado": None,
                "valor_liquido_r_mil": None,
                "valor_liquido_r_mil_formatado": None,
                "status_calculo_valor_liquido": status,
                "fonte_valor_liquido": None,
            }

        aliquota_icms_efetiva = cls._optional_float(aliquota_icms_efetiva_raw)
        if aliquota_icms_efetiva is None:
            aliquota_icms_efetiva = cls._resolve_aliquota_icms_efetiva(
                aliquota_icms_original=aliquota_icms_original,
                codigo_planilha_formacao=codigo_planilha,
            )

        valor_apos_icms = cls._optional_float(valor_apos_icms_raw)
        if valor_apos_icms is None:
            valor_apos_icms = valor_bruto_r_mil * (1 - aliquota_icms_efetiva / 100.0)

        pis_cofins_rate = aliquota_pis_cofins if aliquota_pis_cofins is not None else 0.0
        valor_liquido = cls._optional_float(valor_liquido_raw)
        if valor_liquido is None:
            valor_liquido = valor_apos_icms * (1 - pis_cofins_rate / 100.0)

        return {
            "codigo_planilha_formacao": codigo_planilha,
            "aliquota_icms_original": aliquota_icms_original,
            "aliquota_icms": aliquota_icms_original,
            "aplica_reducao_icms": aplica_reducao,
            "percentual_reducao_icms": percentual_reducao,
            "aliquota_icms_efetiva": aliquota_icms_efetiva,
            "aliquota_pis_cofins": aliquota_pis_cofins,
            "valor_apos_icms_r_mil": valor_apos_icms,
            "valor_apos_icms_r_mil_formatado": cls.format_currency(valor_apos_icms),
            "valor_liquido_r_mil": valor_liquido,
            "valor_liquido_r_mil_formatado": cls.format_currency(valor_liquido),
            "status_calculo_valor_liquido": status,
            "fonte_valor_liquido": cls.FONTE_VALOR_LIQUIDO,
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
        formatted_items = [cls.format_item(item) for item in items]
        liquido_values = [
            item["valor_liquido_r_mil"]
            for item in formatted_items
            if item.get("valor_liquido_r_mil") is not None
        ]
        total_liquido_r_mil = sum(liquido_values) if liquido_values else None
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
                "total_liquido_r_mil": total_liquido_r_mil,
                "total_liquido_r_mil_formatado": cls.format_currency(total_liquido_r_mil),
            },
            "empresa": {
                "nome": cls.trim(header.get("empresa_nome")),
                "cnpj": cls.format_cnpj(header.get("empresa_cnpj")),
                "inscricao_estadual": cls.format_inscricao_estadual(
                    header.get("empresa_inscricao_estadual")
                ),
                "endereco": cls.trim(header.get("empresa_endereco")),
                "bairro": cls.trim(header.get("empresa_bairro")),
                "cidade": cls.trim(header.get("empresa_cidade")),
                "uf": cls.trim(header.get("empresa_uf")),
                "cep": cls.format_cep(header.get("empresa_cep")),
                "telefone": cls.format_phone(header.get("empresa_telefone")),
                "site": empresa_site,
            },
            "cliente": cls._format_cliente(header),
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
                "icms": cls.format_icms_rate(header.get("icms")),
                "ipi": cls.trim(header.get("ipi")),
                "frete": cls.format_frete(header.get("frete")),
                "embalagem": cls.format_embalagem(header.get("embalagem")),
            },
            "vendedor": {
                "codigo": cls.trim(header.get("vendedor_codigo")),
                "nome": cls.trim(header.get("vendedor_nome")),
                "email": cls.trim(header.get("vendedor_email")),
                "telefone": cls.format_phone(header.get("vendedor_telefone")),
                "cargo": cls.trim(header.get("vendedor_cargo")),
            },
            "observacoes": cls.trim(header.get("observacoes")),
            "itens": formatted_items,
        }

    @classmethod
    def _format_cliente(cls, header: dict) -> dict:
        tipo_cadastro = cls.trim(header.get("cliente_tipo_cadastro")) or None
        is_prospect = tipo_cadastro == "prospect"
        return {
            "codigo": cls.trim(header.get("cliente_codigo")),
            "loja": cls.trim(header.get("cliente_loja")),
            "nome": cls.trim(header.get("cliente_nome")),
            "nome_fantasia": cls.trim(header.get("cliente_nome_fantasia")) or None,
            "cnpj": cls.format_cnpj(header.get("cliente_cnpj")),
            "ie": cls.format_inscricao_estadual(header.get("cliente_ie")),
            "endereco": cls.trim(header.get("cliente_endereco")),
            "bairro": cls.trim(header.get("cliente_bairro")),
            "cidade": cls.trim(header.get("cliente_cidade")),
            "uf": cls.trim(header.get("cliente_uf")),
            "cep": cls.format_cep(header.get("cliente_cep")),
            "telefone": cls.format_phone(header.get("cliente_telefone")),
            "email": cls.trim(header.get("cliente_email")) or None,
            "tipo_cadastro": tipo_cadastro,
            "is_prospect": is_prospect,
        }

    @classmethod
    def format_item(cls, row: dict) -> dict:
        valor_bruto_r_mil = cls._optional_float(
            row.get("valor_bruto_r_mil", row.get("preco_unitario"))
        )
        liquido = cls._compute_valor_liquido_comercial(
            valor_bruto_r_mil=valor_bruto_r_mil,
            id_formacao_preco=row.get("id_formacao_preco"),
            aliquota_icms_raw=row.get("aliquota_icms_original", row.get("aliquota_icms")),
            aliquota_pis_cofins_raw=row.get("aliquota_pis_cofins"),
            codigo_planilha_formacao=row.get("codigo_planilha_formacao"),
            aliquota_icms_efetiva_raw=row.get("aliquota_icms_efetiva"),
            valor_apos_icms_raw=row.get("valor_apos_icms_r_mil"),
            valor_liquido_raw=row.get("valor_liquido_r_mil"),
        )
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
            "valor_bruto_r_mil": valor_bruto_r_mil,
            "valor_bruto_r_mil_formatado": cls.format_currency(valor_bruto_r_mil),
            "codigo_planilha_formacao": liquido["codigo_planilha_formacao"],
            "aliquota_icms_original": liquido["aliquota_icms_original"],
            "aliquota_icms": liquido["aliquota_icms"],
            "aplica_reducao_icms": liquido["aplica_reducao_icms"],
            "percentual_reducao_icms": liquido["percentual_reducao_icms"],
            "aliquota_icms_efetiva": liquido["aliquota_icms_efetiva"],
            "aliquota_pis_cofins": liquido["aliquota_pis_cofins"],
            "valor_apos_icms_r_mil": liquido["valor_apos_icms_r_mil"],
            "valor_apos_icms_r_mil_formatado": liquido["valor_apos_icms_r_mil_formatado"],
            "valor_liquido_r_mil": liquido["valor_liquido_r_mil"],
            "valor_liquido_r_mil_formatado": liquido["valor_liquido_r_mil_formatado"],
            "id_formacao_preco": cls.trim(row.get("id_formacao_preco")) or None,
            "status_calculo_valor_liquido": liquido["status_calculo_valor_liquido"],
            "fonte_valor_liquido": liquido["fonte_valor_liquido"],
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
