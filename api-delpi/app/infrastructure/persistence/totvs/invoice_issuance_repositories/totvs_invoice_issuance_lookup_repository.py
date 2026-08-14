"""Lookups TOTVS para solicitação de emissão de NF (SA1/SA2/SB1/SB2/SA4)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.invoice_issuance.carrier_contact import (
    format_carrier_address,
    format_carrier_phone,
)
from app.domain.totvs.protheus_warehouses import WAREHOUSE_ALMOXARIFADO
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_CARRIER_SELECT = """
                RTRIM(SA4.A4_COD) AS carrier_code,
                RTRIM(SA4.A4_NREDUZ) AS carrier_short_name,
                RTRIM(SA4.A4_NOME) AS legal_name,
                RTRIM(SA4.A4_CGC) AS tax_id,
                RTRIM(SA4.A4_END) AS address_street,
                RTRIM(SA4.A4_BAIRRO) AS address_district,
                RTRIM(SA4.A4_MUN) AS address_city,
                RTRIM(SA4.A4_EST) AS address_state,
                RTRIM(SA4.A4_CEP) AS address_zip,
                RTRIM(SA4.A4_DDD) AS phone_area,
                RTRIM(SA4.A4_TEL) AS phone
"""


class TotvsInvoiceIssuanceLookupRepository(BaseRepository):
    def search_customers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        limit = max(1, min(int(limit), 50))
        digits = re.sub(r"\D", "", q)
        params: list[Any] = []
        or_parts = [
            "SA1.A1_COD LIKE ?",
            "SA1.A1_NOME COLLATE Latin1_General_CI_AI LIKE ?",
            "SA1.A1_NREDUZ COLLATE Latin1_General_CI_AI LIKE ?",
        ]
        params.extend([f"{q}%", f"%{q}%", f"%{q}%"])
        if digits:
            or_parts.append("SA1.A1_CGC LIKE ?")
            params.append(f"%{digits}%")
        parts = re.split(r"[\s\-/]+", q)
        if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
            or_parts.append("(SA1.A1_COD LIKE ? AND SA1.A1_LOJA LIKE ?)")
            params.extend([f"{parts[0].strip()}%", f"{parts[1].strip()}%"])
        sql = f"""
            SELECT TOP ({limit})
                RTRIM(SA1.A1_COD) AS party_code,
                RTRIM(SA1.A1_LOJA) AS party_store,
                RTRIM(SA1.A1_NOME) AS party_name,
                RTRIM(SA1.A1_CGC) AS tax_id,
                RTRIM(SA1.A1_MSBLQL) AS msblql
            FROM SA1010 SA1 WITH (NOLOCK)
            WHERE SA1.D_E_L_E_T_ = ''
              AND ({" OR ".join(or_parts)})
            ORDER BY SA1.A1_NOME, SA1.A1_COD, SA1.A1_LOJA
        """
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        return [_map_party_row(row, "customer") for row in rows]

    def get_customer(self, *, party_code: str, party_store: str) -> dict[str, Any] | None:
        code = (party_code or "").strip()
        store = (party_store or "").strip()
        if not code or not store:
            return None
        sql = """
            SELECT TOP 1
                RTRIM(SA1.A1_COD) AS party_code,
                RTRIM(SA1.A1_LOJA) AS party_store,
                RTRIM(SA1.A1_NOME) AS party_name,
                RTRIM(SA1.A1_CGC) AS tax_id,
                RTRIM(SA1.A1_MSBLQL) AS msblql
            FROM SA1010 SA1 WITH (NOLOCK)
            WHERE SA1.D_E_L_E_T_ = ''
              AND RTRIM(SA1.A1_COD) = ?
              AND RTRIM(SA1.A1_LOJA) = ?
            ORDER BY SA1.R_E_C_N_O_
        """
        with self as repo:
            row = repo.execute_one(sql, (code, store))
        return _map_party_row(row, "customer") if row else None

    def search_products(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        limit = max(1, min(int(limit), 50))
        sql = f"""
            SELECT TOP ({limit})
                RTRIM(SB1.B1_COD) AS code,
                RTRIM(SB1.B1_DESC) AS description,
                RTRIM(SB1.B1_UM) AS unit,
                RTRIM(SB1.B1_MSBLQL) AS msblql
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE SB1.D_E_L_E_T_ = ''
              AND (
                    SB1.B1_COD LIKE ?
                 OR SB1.B1_DESC COLLATE Latin1_General_CI_AI LIKE ?
              )
            ORDER BY SB1.B1_COD
        """
        with self as repo:
            rows = repo.execute_query(sql, (f"{q}%", f"%{q}%"))
        return [
            {
                "code": str(row.get("code") or "").strip(),
                "description": str(row.get("description") or "").strip(),
                "unit": str(row.get("unit") or "").strip() or None,
                "blocked": str(row.get("msblql") or "").strip() == "1",
            }
            for row in rows
        ]

    def get_product(self, *, code: str) -> dict[str, Any] | None:
        product_code = (code or "").strip()
        if not product_code:
            return None
        sql = """
            SELECT TOP 1
                RTRIM(SB1.B1_COD) AS code,
                RTRIM(SB1.B1_DESC) AS description,
                RTRIM(SB1.B1_UM) AS unit,
                RTRIM(SB1.B1_MSBLQL) AS msblql
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE SB1.D_E_L_E_T_ = ''
              AND RTRIM(SB1.B1_COD) = ?
            ORDER BY SB1.R_E_C_N_O_
        """
        with self as repo:
            row = repo.execute_one(sql, (product_code,))
        if not row:
            return None
        return {
            "code": str(row.get("code") or "").strip(),
            "description": str(row.get("description") or "").strip(),
            "unit": str(row.get("unit") or "").strip() or None,
            "blocked": str(row.get("msblql") or "").strip() == "1",
        }

    def get_warehouse_01_balance(self, *, product_code: str, branch_code: str) -> dict[str, Any]:
        code = (product_code or "").strip()
        branch = (branch_code or "").strip()
        sql = """
            SELECT TOP 1
                CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) AS quantity
            FROM SB2010 SB2 WITH (NOLOCK)
            WHERE SB2.D_E_L_E_T_ = ''
              AND RTRIM(SB2.B2_COD) = ?
              AND RTRIM(SB2.B2_FILIAL) = ?
              AND LTRIM(RTRIM(SB2.B2_LOCAL)) = ?
            ORDER BY SB2.R_E_C_N_O_
        """
        with self as repo:
            row = repo.execute_one(sql, (code, branch, WAREHOUSE_ALMOXARIFADO))
        quantity = float(row.get("quantity") or 0) if row else 0.0
        return {
            "product_code": code,
            "branch_code": branch,
            "warehouse": WAREHOUSE_ALMOXARIFADO,
            "quantity": quantity,
        }

    def search_carriers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        limit = max(1, min(int(limit), 50))
        digits = re.sub(r"\D", "", q)
        or_parts = [
            "SA4.A4_COD LIKE ?",
            "SA4.A4_NREDUZ COLLATE Latin1_General_CI_AI LIKE ?",
            "SA4.A4_NOME COLLATE Latin1_General_CI_AI LIKE ?",
        ]
        params: list[Any] = [f"{q}%", f"%{q}%", f"%{q}%"]
        if digits:
            or_parts.append("SA4.A4_CGC LIKE ?")
            params.append(f"%{digits}%")
        sql = f"""
            SELECT TOP ({limit})
                {_CARRIER_SELECT}
            FROM SA4010 SA4 WITH (NOLOCK)
            WHERE SA4.D_E_L_E_T_ = ''
              AND ({" OR ".join(or_parts)})
            ORDER BY SA4.A4_NREDUZ, SA4.A4_COD
        """
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        return [_map_carrier_row(row) for row in rows]

    def get_carrier(self, *, carrier_code: str) -> dict[str, Any] | None:
        code = (carrier_code or "").strip()
        if not code:
            return None
        sql = f"""
            SELECT TOP 1
                {_CARRIER_SELECT}
            FROM SA4010 SA4 WITH (NOLOCK)
            WHERE SA4.D_E_L_E_T_ = ''
              AND RTRIM(SA4.A4_COD) = ?
            ORDER BY SA4.R_E_C_N_O_
        """
        with self as repo:
            row = repo.execute_one(sql, (code,))
        return _map_carrier_row(row) if row else None


def _map_party_row(row: dict[str, Any], party_type: str) -> dict[str, Any]:
    tax_id = re.sub(r"\D", "", str(row.get("tax_id") or ""))
    return {
        "party_type": party_type,
        "party_code": str(row.get("party_code") or "").strip(),
        "party_store": str(row.get("party_store") or "").strip(),
        "party_name": str(row.get("party_name") or "").strip(),
        "tax_id": tax_id or None,
        "blocked": str(row.get("msblql") or "").strip() == "1",
    }


def _map_carrier_row(row: dict[str, Any]) -> dict[str, Any]:
    legal_name = str(row.get("legal_name") or "").strip()
    short_name = str(row.get("carrier_short_name") or "").strip()
    tax_id = re.sub(r"\D", "", str(row.get("tax_id") or ""))
    return {
        "carrier_code": str(row.get("carrier_code") or "").strip(),
        "carrier_name": short_name or legal_name,
        "legal_name": legal_name or None,
        "tax_id": tax_id or None,
        "address": format_carrier_address(
            street=str(row.get("address_street") or ""),
            district=str(row.get("address_district") or ""),
            city=str(row.get("address_city") or ""),
            state=str(row.get("address_state") or ""),
            zip_code=str(row.get("address_zip") or ""),
        ),
        "phone": format_carrier_phone(
            ddd=str(row.get("phone_area") or ""),
            phone=str(row.get("phone") or ""),
        ),
        "blocked": False,
    }
