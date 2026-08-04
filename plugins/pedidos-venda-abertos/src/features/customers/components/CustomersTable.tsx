import { MoreHorizontal } from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { PVA_TABLE } from "../../../ui/tableChrome";
import { navigateCustomerDetail } from "../../../app/pluginNavigation";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
  CustomerSummary,
} from "../types/customerSummary";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import { BILLING_TREND_HELP } from "../utils/billingTrendPresentation";
import { BillingTrendCell } from "./BillingTrendCell";
import { CustomerAvatar } from "./CustomerAvatar";

type CustomersTableProps = {
  customers: CustomerSummary[];
  sortKey: CustomerListSortKey;
  sortDirection: CustomerListSortDirection;
  onSort: (key: Exclude<CustomerListSortKey, "attention">) => void;
  basePath: string;
};

type SortableKey = Exclude<CustomerListSortKey, "attention">;

export function CustomersTable({
  customers,
  sortKey,
  sortDirection,
  onSort,
  basePath,
}: CustomersTableProps) {
  const renderSortHeader = (column: SortableKey, label: string) => {
    const active = sortKey === column;
    return (
      <button
        type="button"
        className="pva-sort-btn"
        aria-sort={
          active ? (sortDirection === "asc" ? "ascending" : "descending") : "none"
        }
        onClick={() => onSort(column)}
      >
        <span>{label}</span>
        <span aria-hidden="true">{active ? (sortDirection === "asc" ? "↑" : "↓") : ""}</span>
      </button>
    );
  };

  return (
    <section className="pva-customers-table-wrap" aria-label="Lista de clientes">
      <table
        className={`pva-customers-table ${PVA_TABLE.sortableTable} ${PVA_TABLE.compactTable}`}
      >
        <thead>
          <tr>
            <th scope="col">{renderSortHeader("nome", "Cliente")}</th>
            <th scope="col">{renderSortHeader("sellerName", "Vendedor")}</th>
            <th scope="col">{renderSortHeader("city", "Cidade / UF")}</th>
            <th scope="col">{renderSortHeader("lastPurchaseDate", "Última venda")}</th>
            <th scope="col" className="pva-col-numeric">
              {renderSortHeader("billed12m", "Fat. 12 meses")}
            </th>
            <th scope="col" className="pva-customers-table__th-with-help">
              <span className="pva-customers-table__th-label-row">
                {renderSortHeader("billingTrend", "Tendência")}
                <HelpTooltip
                  content={BILLING_TREND_HELP}
                  ariaLabel="Como a tendência é calculada"
                  placement="bottom"
                />
              </span>
            </th>
            <th scope="col" className="pva-customers-table__th-static">
              Status
            </th>
            <th scope="col" className="pva-col-numeric">
              {renderSortHeader("valorTotalAberto", "Em aberto")}
            </th>
            <th scope="col" className="pva-customers-table__th-actions">
              <span className="visually-hidden">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => {
            const codeStore =
              formatEntityCodeStore(customer.codigo, customer.loja) ??
              `${customer.codigo}-${customer.loja}`;
            const openLabel = `Abrir cliente ${customer.nome || codeStore}`;
            const status = customer.status ?? resolveCustomerStatus(customer);
            const cityUf =
              customer.city || customer.state
                ? [customer.city, customer.state].filter(Boolean).join(" / ")
                : "—";
            return (
              <tr key={customer.key}>
                <td data-label="Cliente">
                  <div className="pva-customers-table__client pva-customers-table__client--row">
                    <CustomerAvatar
                      code={customer.codigo}
                      store={customer.loja}
                      name={customer.nome}
                      hasAvatar={Boolean(customer.hasAvatar)}
                      size="sm"
                    />
                    <div className="pva-customers-table__client-text">
                      <span
                        className="pva-customers-table__client-name"
                        role="link"
                        tabIndex={0}
                        aria-label={openLabel}
                        onClick={() =>
                          navigateCustomerDetail(customer.codigo, customer.loja, {
                            basePath,
                          })
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            navigateCustomerDetail(customer.codigo, customer.loja, {
                              basePath,
                            });
                          }
                        }}
                      >
                        {customer.nome || "—"}
                      </span>
                      <span className="pva-customers-table__client-id">
                        {customer.codigo} · Loja {customer.loja}
                      </span>
                    </div>
                  </div>
                </td>
                <td data-label="Vendedor" className="pva-customers-table__muted">
                  {customer.sellerName?.trim() || "—"}
                </td>
                <td data-label="Cidade / UF">{cityUf}</td>
                <td data-label="Última venda" className="pva-customers-table__muted">
                  {formatDisplayDate(customer.lastPurchaseDate ?? null)}
                </td>
                <td data-label="Faturamento 12 meses" className="pva-col-numeric">
                  {formatCurrency(customer.billed12m ?? 0)}
                </td>
                <td data-label="Tendência">
                  <BillingTrendCell
                    trend={customer.billingTrend}
                    pct={customer.billingTrendPct}
                  />
                </td>
                <td data-label="Status">
                  <span
                    className={`pva-status-pill pva-status-pill--${status}`}
                  >
                    <span className="pva-status-pill__dot" aria-hidden="true" />
                    {statusLabel(status)}
                  </span>
                </td>
                <td data-label="Valor em aberto" className="pva-col-numeric">
                  {formatCurrency(customer.valorTotalAberto)}
                </td>
                <td data-label="Ações" className="pva-customers-table__td-actions">
                  <button
                    type="button"
                    className="pva-customers-table__menu"
                    aria-label={openLabel}
                    onClick={() =>
                      navigateCustomerDetail(customer.codigo, customer.loja, { basePath })
                    }
                  >
                    <MoreHorizontal size={16} aria-hidden="true" />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
