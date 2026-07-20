from __future__ import annotations

from typing import Any

from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_query_parts import (
    is_protheus_product_blocked,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    PRIMARY_WAREHOUSE,
    WORK_IN_PROCESS_WAREHOUSES,
    build_consumption_analysis_where_clauses,
    build_where_clauses,
    consumption_analysis_rows_sql,
    consumption_last_date_sql,
    consumption_monthly_series_sql,
    linked_suppliers_sql,
    materials_base_cte,
    open_commitments_sql,
    open_purchase_orders_sql,
    product_detail_sql,
    resolve_order_by,
    stock_agg_cte,
)


class SafetyStockQueryRepository(BaseRepository, SafetyStockQueryRepositoryPort):
  def fetch_filter_options(
      self,
      *,
      branch: str,
      include_blocked: bool,
  ) -> dict[str, list[str]]:
      blocked_clause = ""
      if not include_blocked:
          blocked_clause = f"AND {self._blocked_sql('SB1')}"

      sql = f"""
      SELECT DISTINCT
          RTRIM(SB1.B1_GRUPO) AS product_group,
          RTRIM(SB1.B1_UM) AS unit
      FROM SB1010 SB1 WITH (NOLOCK)
      LEFT JOIN SBZ010 SBZ WITH (NOLOCK)
          ON SBZ.BZ_COD = SB1.B1_COD
         AND SBZ.D_E_L_E_T_ = ''
         AND RTRIM(SBZ.BZ_FILIAL) = ?
         AND RTRIM(SBZ.BZ_FILIAL) <> ''
      WHERE SB1.D_E_L_E_T_ = ''
        AND SB1.B1_TIPO = 'MP'
        {blocked_clause}
      ORDER BY product_group, unit
      """

      with self as repo:
          rows = repo.execute_query(sql, [branch])

      groups = sorted({str(r.get("product_group") or "").strip() for r in rows if r.get("product_group")})
      units = sorted({str(r.get("unit") or "").strip() for r in rows if r.get("unit")})
      return {"product_groups": groups, "units": units}

  def fetch_summary(
      self,
      *,
      branch: str,
      include_blocked: bool,
      product_group: str | None,
      unit: str | None,
      search: str | None,
      status: str | None,
      include_without_safety_stock: bool,
  ) -> dict[str, Any]:
      where_sql, params = build_where_clauses(
          include_blocked=include_blocked,
          product_group=product_group,
          unit=unit,
          search=search,
          status=status,
          include_without_safety_stock=include_without_safety_stock,
      )
      where_prefix = f"WHERE {where_sql}" if where_sql else ""

      sql = f"""
      WITH
      {stock_agg_cte()}
      , {materials_base_cte()}
      SELECT
          COUNT(*) AS total_materials,
          SUM(CASE WHEN safety_stock > 0 THEN 1 ELSE 0 END) AS with_safety_stock,
          SUM(CASE WHEN safety_stock <= 0 THEN 1 ELSE 0 END) AS without_safety_stock,
          SUM(CASE WHEN status = 'below_safety_stock' THEN 1 ELSE 0 END) AS below_safety_stock,
          SUM(CASE WHEN status = 'at_safety_stock' THEN 1 ELSE 0 END) AS at_safety_stock,
          SUM(CASE WHEN status = 'above_safety_stock' THEN 1 ELSE 0 END) AS above_safety_stock,
          SUM(CASE WHEN primary_stock > 0 THEN 1 ELSE 0 END) AS with_primary_stock,
          SUM(CASE WHEN primary_stock <= 0 THEN 1 ELSE 0 END) AS without_primary_stock,
          SUM(CASE WHEN work_in_process_stock > 0 THEN 1 ELSE 0 END) AS with_work_in_process_stock
      FROM materials_base
      {where_prefix}
      """

      deficit_sql = f"""
      WITH
      {stock_agg_cte()}
      , {materials_base_cte()}
      SELECT
          RTRIM(unit) AS unit,
          COUNT(*) AS material_count,
          SUM(deficit_quantity) AS deficit_quantity
      FROM materials_base
      {where_prefix}
        {"AND" if where_prefix else "WHERE"} deficit_quantity > 0
      GROUP BY RTRIM(unit)
      ORDER BY RTRIM(unit)
      """

      with self as repo:
          summary_row = repo.execute_one(sql, [branch, branch] + params) or {}
          deficit_rows = repo.execute_query(deficit_sql, [branch, branch] + params)

      return {
          "total_materials": int(summary_row.get("total_materials") or 0),
          "with_safety_stock": int(summary_row.get("with_safety_stock") or 0),
          "without_safety_stock": int(summary_row.get("without_safety_stock") or 0),
          "below_safety_stock": int(summary_row.get("below_safety_stock") or 0),
          "at_safety_stock": int(summary_row.get("at_safety_stock") or 0),
          "above_safety_stock": int(summary_row.get("above_safety_stock") or 0),
          "with_primary_stock": int(summary_row.get("with_primary_stock") or 0),
          "without_primary_stock": int(summary_row.get("without_primary_stock") or 0),
          "with_work_in_process_stock": int(
              summary_row.get("with_work_in_process_stock") or 0
          ),
          "deficit_by_unit": [
              {
                  "unit": str(row.get("unit") or "").strip(),
                  "material_count": int(row.get("material_count") or 0),
                  "deficit_quantity": float(row.get("deficit_quantity") or 0),
              }
              for row in deficit_rows
              if row.get("unit")
          ],
      }

  def count_items(
      self,
      *,
      branch: str,
      include_blocked: bool,
      product_group: str | None,
      unit: str | None,
      search: str | None,
      status: str | None,
      include_without_safety_stock: bool,
  ) -> int:
      where_sql, params = build_where_clauses(
          include_blocked=include_blocked,
          product_group=product_group,
          unit=unit,
          search=search,
          status=status,
          include_without_safety_stock=include_without_safety_stock,
      )
      where_prefix = f"WHERE {where_sql}" if where_sql else ""

      sql = f"""
      WITH
      {stock_agg_cte()}
      , {materials_base_cte()}
      SELECT COUNT(*) AS total
      FROM materials_base
      {where_prefix}
      """

      with self as repo:
          row = repo.execute_one(sql, [branch, branch] + params)
      return int((row or {}).get("total") or 0)

  def fetch_items(
      self,
      *,
      branch: str,
      include_blocked: bool,
      product_group: str | None,
      unit: str | None,
      search: str | None,
      status: str | None,
      include_without_safety_stock: bool,
      sort_by: str,
      sort_direction: str,
      offset: int,
      page_size: int,
  ) -> list[dict[str, Any]]:
      where_sql, params = build_where_clauses(
          include_blocked=include_blocked,
          product_group=product_group,
          unit=unit,
          search=search,
          status=status,
          include_without_safety_stock=include_without_safety_stock,
      )
      where_prefix = f"WHERE {where_sql}" if where_sql else ""
      order_by = resolve_order_by(sort_by, sort_direction)

      sql = f"""
      WITH
      {stock_agg_cte()}
      , {materials_base_cte()}
      SELECT
          product_code,
          product_description,
          product_type,
          unit,
          product_group,
          blocked_raw,
          safety_stock,
          primary_stock,
          work_in_process_stock,
          warehouse_50_stock,
          warehouse_98_stock,
          warehouse_99_stock,
          work_in_process_committed,
          work_in_process_available,
          deficit_quantity,
          status
      FROM materials_base
      {where_prefix}
      ORDER BY {order_by}
      OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
      """

      query_params = [branch, branch] + params + [offset, page_size]

      with self as repo:
          rows = repo.execute_query(sql, query_params)

      return [self._map_item_row(row, branch) for row in rows]

  def fetch_item_detail(
      self,
      *,
      branch: str,
      product_code: str,
  ) -> dict[str, Any] | None:
      code = product_code.strip()
      sql = product_detail_sql()
      with self as repo:
          row = repo.execute_one(sql, [branch, branch, code])
      if not row:
          return None

      mapped = self._map_item_row(row, branch)
      mapped["available_stock"] = float(row.get("available_stock") or 0)
      mapped["secondary_unit"] = str(row.get("secondary_unit") or "").strip()
      mapped["conversion_factor"] = float(row.get("conversion_factor") or 0) or None
      mapped["conversion_type"] = str(row.get("conversion_type") or "").strip()
      return mapped

  def fetch_open_purchase_orders(
      self,
      *,
      branch: str,
      product_code: str,
  ) -> list[dict[str, Any]]:
      code = product_code.strip()
      sql = open_purchase_orders_sql()
      with self as repo:
          rows = repo.execute_query(sql, [branch, code])
      return [self._map_open_purchase_order(row) for row in rows]

  def fetch_open_commitments(
      self,
      *,
      branch: str,
      product_code: str,
  ) -> list[dict[str, Any]]:
      code = product_code.strip()
      sql = open_commitments_sql()
      with self as repo:
          rows = repo.execute_query(sql, [branch, code])
      return [self._map_open_commitment(row) for row in rows]

  def fetch_linked_suppliers(
      self,
      *,
      branch: str,
      product_code: str,
  ) -> list[dict[str, Any]]:
      code = product_code.strip()
      sql = linked_suppliers_sql()
      # Ordem dos placeholders em linked_suppliers_sql.
      params = [branch, code, branch, code, branch]
      with self as repo:
          rows = repo.execute_query(sql, params)
      return [self._map_linked_supplier(row) for row in rows]

  def fetch_consumption_analysis_rows(
      self,
      *,
      branch: str,
      period_start: str,
      include_blocked: bool,
      product_group: str | None,
      unit: str | None,
      search: str | None,
      product_code: str | None = None,
  ) -> list[dict[str, Any]]:
      where_sql, filter_params = build_consumption_analysis_where_clauses(
          include_blocked=include_blocked,
          product_group=product_group,
          unit=unit,
          search=search,
          product_code=product_code,
      )
      sql = consumption_analysis_rows_sql().format(where_sql=where_sql)
      # stock_agg, materials_base, consumption_agg: branch, branch, branch, start
      params = [branch, branch, branch, period_start] + filter_params
      with self as repo:
          rows = repo.execute_query(sql, params)
      return [self._map_consumption_analysis_row(row, branch) for row in rows]

  def fetch_consumption_monthly_series(
      self,
      *,
      branch: str,
      product_code: str,
      period_start: str,
  ) -> list[dict[str, Any]]:
      code = product_code.strip()
      sql = consumption_monthly_series_sql()
      with self as repo:
          rows = repo.execute_query(sql, [branch, code, period_start])
      return [self._map_monthly_series_row(row) for row in rows]

  def fetch_last_consumption_date(
      self,
      *,
      branch: str,
      product_code: str,
  ) -> str | None:
      code = product_code.strip()
      sql = consumption_last_date_sql()
      with self as repo:
          row = repo.execute_one(sql, [branch, code])
      if not row:
          return None
      return self._format_protheus_date(row.get("last_consumption_date"))

  @staticmethod
  def _format_protheus_date(value: Any) -> str | None:
      raw = str(value or "").strip()
      if not raw:
          return None
      if len(raw) == 8 and raw.isdigit():
          return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
      return raw

  @classmethod
  def _map_open_purchase_order(cls, row: dict[str, Any]) -> dict[str, Any]:
      return {
          "branch": str(row.get("branch") or "").strip(),
          "order_number": str(row.get("order_number") or "").strip(),
          "order_item": str(row.get("order_item") or "").strip(),
          "product_code": str(row.get("product_code") or "").strip(),
          "product_description": str(row.get("product_description") or "").strip(),
          "warehouse": str(row.get("warehouse") or "").strip(),
          "unit": str(row.get("unit") or "").strip(),
          "ordered_quantity": float(row.get("ordered_quantity") or 0),
          "delivered_quantity": float(row.get("delivered_quantity") or 0),
          "open_quantity": float(row.get("open_quantity") or 0),
          "pre_invoice_quantity": float(row.get("pre_invoice_quantity") or 0),
          "issue_date": cls._format_protheus_date(row.get("issue_date")),
          "expected_delivery_date": cls._format_protheus_date(
              row.get("expected_delivery_date")
          ),
          "supplier_code": str(row.get("supplier_code") or "").strip(),
          "supplier_store": str(row.get("supplier_store") or "").strip(),
          "supplier_name": str(row.get("supplier_name") or "").strip(),
          "unit_price": float(row.get("unit_price") or 0),
          "open_value": float(row.get("open_value") or 0),
      }

  @classmethod
  def _map_open_commitment(cls, row: dict[str, Any]) -> dict[str, Any]:
      original = float(row.get("original_quantity") or 0)
      open_qty = float(row.get("open_quantity") or 0)
      consumed = float(row.get("consumed_quantity") or 0)
      if consumed <= 0 and original > open_qty:
          consumed = original - open_qty
      return {
          "branch": str(row.get("branch") or "").strip(),
          "product_code": str(row.get("product_code") or "").strip(),
          "product_description": str(row.get("product_description") or "").strip(),
          "warehouse": str(row.get("warehouse") or "").strip(),
          "production_order": str(row.get("production_order") or "").strip(),
          "origin_production_order": str(
              row.get("origin_production_order") or ""
          ).strip(),
          "commitment_date": cls._format_protheus_date(row.get("commitment_date")),
          "unit": str(row.get("unit") or "").strip(),
          "original_quantity": original,
          "open_quantity": open_qty,
          "consumed_quantity": consumed,
          "lot": str(row.get("lot") or "").strip(),
          "commitment_sequence": str(row.get("commitment_sequence") or "").strip(),
          "preserved_balance": float(row.get("preserved_balance") or 0),
      }

  @classmethod
  def _map_linked_supplier(cls, row: dict[str, Any]) -> dict[str, Any]:
      has_purchase = int(row.get("has_last_purchase") or 0) == 1
      last_purchase_date = (
          cls._format_protheus_date(row.get("last_purchase_date"))
          if has_purchase
          else None
      )
      return {
          "product_code": str(row.get("product_code") or "").strip(),
          "supplier_code": str(row.get("supplier_code") or "").strip(),
          "supplier_store": str(row.get("supplier_store") or "").strip(),
          "supplier_part_number": str(row.get("supplier_part_number") or "").strip(),
          "trade_name": str(row.get("trade_name") or "").strip(),
          "legal_name": str(row.get("legal_name") or "").strip(),
          "document": str(row.get("document") or "").strip(),
          "has_last_purchase": has_purchase,
          "last_purchase_date": last_purchase_date,
          "last_unit_price": float(row.get("last_unit_price") or 0) if has_purchase else None,
          "last_quantity": float(row.get("last_quantity") or 0) if has_purchase else None,
          "last_total_value": (
              float(row.get("last_total_value") or 0) if has_purchase else None
          ),
          "last_invoice_number": (
              str(row.get("last_invoice_number") or "").strip() if has_purchase else None
          ),
          "last_invoice_series": (
              str(row.get("last_invoice_series") or "").strip() if has_purchase else None
          ),
      }

  @staticmethod
  def _blocked_sql(alias: str = "SB1") -> str:
      return (
          f"(RTRIM(LTRIM({alias}.B1_MSBLQL)) NOT IN ('1', 'SIM') "
          f"OR {alias}.B1_MSBLQL IS NULL OR RTRIM(LTRIM({alias}.B1_MSBLQL)) = '')"
      )

  @staticmethod
  def _map_item_row(row: dict[str, Any], branch: str) -> dict[str, Any]:
      blocked_raw = row.get("blocked_raw")
      return {
          "product_code": str(row.get("product_code") or "").strip(),
          "product_description": str(row.get("product_description") or "").strip(),
          "product_type": str(row.get("product_type") or "").strip(),
          "unit": str(row.get("unit") or "").strip(),
          "product_group": str(row.get("product_group") or "").strip(),
          "branch": branch,
          "blocked": is_protheus_product_blocked(blocked_raw),
          "safety_stock": float(row.get("safety_stock") or 0),
          "primary_stock": float(row.get("primary_stock") or 0),
          "work_in_process_stock": float(row.get("work_in_process_stock") or 0),
          "warehouse_50_stock": float(row.get("warehouse_50_stock") or 0),
          "warehouse_98_stock": float(row.get("warehouse_98_stock") or 0),
          "warehouse_99_stock": float(row.get("warehouse_99_stock") or 0),
          "work_in_process_committed": float(row.get("work_in_process_committed") or 0),
          "work_in_process_available": float(row.get("work_in_process_available") or 0),
          "deficit_quantity": float(row.get("deficit_quantity") or 0),
          "status": str(row.get("status") or "").strip(),
      }

  @classmethod
  def _map_consumption_analysis_row(
      cls,
      row: dict[str, Any],
      branch: str,
  ) -> dict[str, Any]:
      mapped = cls._map_item_row(row, branch)
      mapped.update(
          {
              "lead_time_days": float(row.get("lead_time_days") or 0),
              "available_stock": float(row.get("available_stock") or 0),
              "period_consumption": float(row.get("period_consumption") or 0),
              "movement_count": int(row.get("movement_count") or 0),
              "first_movement_date": cls._format_protheus_date(
                  row.get("first_movement_date")
              ),
              "last_movement_date": cls._format_protheus_date(
                  row.get("last_movement_date")
              ),
          }
      )
      return mapped

  @classmethod
  def _map_monthly_series_row(cls, row: dict[str, Any]) -> dict[str, Any]:
      year_month = str(row.get("year_month") or "").strip()
      label = year_month
      if len(year_month) == 6 and year_month.isdigit():
          label = f"{year_month[0:4]}-{year_month[4:6]}"
      return {
          "year_month": year_month,
          "year_month_label": label,
          "consumption_quantity": float(row.get("consumption_quantity") or 0),
          "movement_count": int(row.get("movement_count") or 0),
      }

  @staticmethod
  def warehouse_metadata() -> dict[str, object]:
      return {
          "primary_warehouse": PRIMARY_WAREHOUSE,
          "work_in_process_warehouses": list(WORK_IN_PROCESS_WAREHOUSES),
      }
