/**
 * Ranking crescimento/queda de faturamento (Minha Carteira).
 * Cliente: qualquer leitor da carteira; vendedor: só team/manage.
 */
import { useEffect, useMemo, useState } from "react";
import { runTabularExport } from "@delpi/plugin-ui/index";

import { getPortfolioBillingRanking } from "../../../api/analyticsApi";
import {
  CommercialAvatar,
  CommercialCompareSparkline,
  CommercialDataCellValue,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialExcelExportButton,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTableColumnVisibilityMenu,
  CommercialTableFontSizeControls,
  CommercialTrendDelta,
  cmDataTableClassNames,
  type DataTableColumn,
} from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  appendBillingNatureContext,
  billingNatureShortLabel,
} from "../../../content/billingNature";
import type { PortfolioBillingRankingItem } from "../../../types/analytics";
import { formatCurrency } from "../../../utils/format";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
} from "../../../hooks/useCustomerAvatarPresence";
import { OtdCustomerIdentityCell } from "../../analytics/components/OtdCustomerIdentityCell";
import { usePortfolioBillingTablePreferences } from "../hooks/usePortfolioBillingTablePreferences";
import {
  PORTFOLIO_RANKING_COLUMN_CATALOG,
  PORTFOLIO_RANKING_COLUMNS_STORAGE_KEY,
  PORTFOLIO_RANKING_FONT_STORAGE_KEY,
} from "../utils/portfolioBillingTableColumns";
import {
  BILLING_SERIES_PRESET_OPTIONS,
  DEFAULT_BILLING_SERIES_PRESET,
  periodRangeFromBillingPreset,
  type BillingSeriesPeriodPreset,
} from "../utils/billingSeriesPeriod";

type PortfolioBillingRankingTableProps = {
  sellerId?: string | null;
  /** Quando false, não dispara fetch (painel oculto). Default true. */
  active?: boolean;
  billingNature?: "gross" | "net";
};

type RankingOrder = "growth" | "decline";

const RANKING_LIMIT_OPTIONS = [10, 15, 20, 50] as const;
type RankingLimit = (typeof RANKING_LIMIT_OPTIONS)[number];

const RANKING_PERIOD_OPTIONS = BILLING_SERIES_PRESET_OPTIONS.filter(
  (option): option is { id: Exclude<BillingSeriesPeriodPreset, "custom">; label: string } =>
    option.id !== "custom",
);

export function PortfolioBillingRankingTable({
  sellerId,
  active = true,
  billingNature = "gross",
}: PortfolioBillingRankingTableProps) {
  const { canUseTeamScope } = usePortfolioScope();
  const [groupBy, setGroupBy] = useState<"customer" | "seller">("customer");
  const [order, setOrder] = useState<RankingOrder>("growth");
  const [limit, setLimit] = useState<RankingLimit>(20);
  const [periodPreset, setPeriodPreset] =
    useState<Exclude<BillingSeriesPeriodPreset, "custom">>(DEFAULT_BILLING_SERIES_PRESET);
  const [items, setItems] = useState<PortfolioBillingRankingItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    visibility,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    resetColumns,
    filterColumns,
    tableStyle,
    fontSize,
    increaseFont,
    decreaseFont,
    resetFont,
    canIncreaseFont,
    canDecreaseFont,
    isDefaultFont,
  } = usePortfolioBillingTablePreferences({
    columnsStorageKey: PORTFOLIO_RANKING_COLUMNS_STORAGE_KEY,
    fontSizeStorageKey: PORTFOLIO_RANKING_FONT_STORAGE_KEY,
    columns: PORTFOLIO_RANKING_COLUMN_CATALOG,
    emptyFallbackKeys: ["rank", "customer", "seller"],
  });

  const effectiveGroupBy =
    groupBy === "seller" && canUseTeamScope ? "seller" : "customer";

  const periodRange = useMemo(
    () => periodRangeFromBillingPreset(periodPreset),
    [periodPreset],
  );

  const periodLabel =
    RANKING_PERIOD_OPTIONS.find((option) => option.id === periodPreset)?.label ??
    periodPreset;
  const focusLabel = order === "decline" ? "Maiores quedas" : "Maiores altas";
  const natureLabel = billingNatureShortLabel(billingNature);
  const amountHeader = appendBillingNatureContext("Faturamento", billingNature);
  const cardSubtitle = `Top ${limit} · ${periodLabel} · ${focusLabel} · ${natureLabel}`;

  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getPortfolioBillingRanking(
      {
        start_date: periodRange.startDate,
        end_date: periodRange.endDate,
        seller_id: sellerId?.trim() || undefined,
        group_by: effectiveGroupBy,
        limit,
        order,
        nature: billingNature,
      },
      controller.signal,
    )
      .then((payload) => {
        if (controller.signal.aborted) return;
        setItems(payload.items ?? []);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setError(err instanceof Error ? err.message : "Erro ao carregar ranking.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    active,
    effectiveGroupBy,
    limit,
    order,
    periodRange.endDate,
    periodRange.startDate,
    sellerId,
    billingNature,
  ]);

  const avatarPairs = useMemo(
    () =>
      items
        .filter((item) => (item.customerCode || "").trim())
        .map((item) => ({
          customer_code: (item.customerCode || "").trim(),
          customer_store: (item.customerStore || "01").trim() || "01",
        })),
    [items],
  );
  const avatarPresence = useCustomerAvatarPresence(avatarPairs);

  const columns = useMemo((): DataTableColumn<PortfolioBillingRankingItem>[] => {
    const base: DataTableColumn<PortfolioBillingRankingItem>[] = [
      {
        key: "rank",
        header: "#",
        render: (row) => String(row.rank),
      },
    ];
    if (effectiveGroupBy === "seller") {
      base.push({
        key: "seller",
        header: "Vendedor",
        render: (row) => {
          const name = (row.sellerName || "").trim() || "—";
          return (
            <div className="cm-open-orders-client">
              <CommercialAvatar name={name} colorKey={name} size="sm" previewable={false} />
              <div className="cm-open-orders-client__text">
                <strong className="cm-open-orders-client__name">{name}</strong>
              </div>
            </div>
          );
        },
      });
    } else {
      base.push({
        key: "customer",
        header: "Cliente",
        interactive: true,
        rowClick: "stop",
        render: (row) => {
          const code = (row.customerCode || "").trim();
          const store = (row.customerStore || "01").trim() || "01";
          return (
            <OtdCustomerIdentityCell
              customer={{
                code,
                store,
                name: row.customerName,
                hasAvatar: code
                  ? avatarPresence.get(customerAvatarKey(code, store))
                  : false,
              }}
              size="sm"
              returnLabel="Minha Carteira"
            />
          );
        },
      });
    }
    base.push(
      {
        key: "trend",
        header: "Tendência",
        align: "right",
        render: (row) => (
          <CommercialCompareSparkline prior={row.priorRol} current={row.currentRol} />
        ),
      },
      {
        key: "current",
        header: `${amountHeader} atual`,
        align: "right",
        className: cmDataTableClassNames.colNumeric,
        render: (row) => (
          <CommercialDataCellValue value={formatCurrency(row.currentRol)} />
        ),
      },
      {
        key: "prior",
        header: `${amountHeader} ano ant.`,
        align: "right",
        className: cmDataTableClassNames.colNumeric,
        render: (row) => (
          <CommercialDataCellValue value={formatCurrency(row.priorRol)} />
        ),
      },
      {
        key: "deltaPct",
        header: "Delta %",
        align: "right",
        className: cmDataTableClassNames.colNumeric,
        render: (row) => <CommercialTrendDelta value={row.deltaPct} />,
      },
    );
    return base;
  }, [amountHeader, avatarPresence, effectiveGroupBy]);

  const visibleColumns = useMemo(() => {
    return filterColumns(columns).filter((column) => {
      if (effectiveGroupBy === "seller" && column.key === "customer") return false;
      if (effectiveGroupBy === "customer" && column.key === "seller") return false;
      return true;
    });
  }, [columns, effectiveGroupBy, filterColumns]);

  return (
    <CommercialSectionCard
      title="Ranking crescimento/queda"
      subtitle={cardSubtitle}
      hint={CM_HELP.customers.billingRanking}
      actions={
        <div className="cm-customers-page__filter-actions">
          {canUseTeamScope ? (
            <CommercialSegmentToggle
              ariaLabel="Agrupar ranking"
              idPrefix="customers-ranking-group"
              value={effectiveGroupBy}
              onChange={(value) =>
                setGroupBy(value === "seller" ? "seller" : "customer")
              }
              options={[
                { value: "customer", label: "Cliente" },
                { value: "seller", label: "Vendedor" },
              ]}
            />
          ) : null}
          <CommercialSegmentToggle
            ariaLabel="Foco do ranking"
            idPrefix="customers-ranking-order"
            value={order}
            onChange={(value) =>
              setOrder(value === "decline" ? "decline" : "growth")
            }
            options={[
              { value: "growth", label: "Maiores altas" },
              { value: "decline", label: "Maiores quedas" },
            ]}
          />
          <CommercialSelectField
            label="Período"
            value={periodPreset}
            onChange={(value) => {
              const next = RANKING_PERIOD_OPTIONS.find((option) => option.id === value);
              if (next) setPeriodPreset(next.id);
            }}
            options={RANKING_PERIOD_OPTIONS.map((option) => ({
              value: option.id,
              label: option.label,
            }))}
          />
          <CommercialSelectField
            label="Top N"
            value={String(limit)}
            onChange={(value) => {
              const parsed = Number(value);
              if (
                RANKING_LIMIT_OPTIONS.includes(parsed as RankingLimit)
              ) {
                setLimit(parsed as RankingLimit);
              }
            }}
            options={RANKING_LIMIT_OPTIONS.map((n) => ({
              value: String(n),
              label: String(n),
            }))}
          />
        </div>
      }
    >
      <CommercialDataListToolbar
        style={tableStyle}
        hint={
          <span className="delpi-ui-section-hint-label">
            {visibleColumnCount} coluna(s) · {items.length.toLocaleString("pt-BR")} linha(s)
          </span>
        }
        actions={
          <>
            <CommercialExcelExportButton
              disabled={loading || items.length === 0}
              onExport={() => {
                runTabularExport({
                  kind: "table",
                  format: "xlsx",
                  payload: {
                    title: `ranking-faturamento-${effectiveGroupBy}-${order}-top${limit}`,
                    columns:
                      effectiveGroupBy === "seller"
                        ? [
                            { key: "rank", label: "Rank" },
                            { key: "sellerName", label: "Vendedor" },
                            { key: "currentRol", label: `${amountHeader} atual` },
                            { key: "priorRol", label: `${amountHeader} ano ant.` },
                            { key: "delta", label: "Delta" },
                            { key: "deltaPct", label: "Delta %" },
                          ]
                        : [
                            { key: "rank", label: "Rank" },
                            { key: "customerName", label: "Cliente" },
                            { key: "customerCode", label: "Código" },
                            { key: "customerStore", label: "Loja" },
                            { key: "currentRol", label: `${amountHeader} atual` },
                            { key: "priorRol", label: `${amountHeader} ano ant.` },
                            { key: "delta", label: "Delta" },
                            { key: "deltaPct", label: "Delta %" },
                          ],
                    rows: items as unknown as Record<string, unknown>[],
                  },
                });
              }}
            />
            <CommercialTableFontSizeControls
              fontSize={fontSize}
              onIncrease={increaseFont}
              onDecrease={decreaseFont}
              onReset={resetFont}
              canIncrease={canIncreaseFont}
              canDecrease={canDecreaseFont}
              isDefault={isDefaultFont}
            />
            <CommercialTableColumnVisibilityMenu
              columns={orderedColumns}
              visibility={visibility}
              onToggleColumn={setColumnVisible}
              onReorderColumns={reorderColumns}
              onReset={resetColumns}
              labels={{
                trigger: "Colunas",
                panelTitle: "Colunas do ranking",
                reset: "Restaurar padrão",
                hint: CM_HELP.customers.billingRanking,
                columnAriaLabel: (label) => `Exibir coluna ${label}`,
                reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
              }}
            />
          </>
        }
      />
      {loading ? (
        <CommercialLoadingCard title="Carregando ranking…" variant="panel" />
      ) : null}
      {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
      {!loading && !error ? (
        <div style={tableStyle}>
          <CommercialDataTable
            rows={items}
            columns={visibleColumns}
            rowKey={(row) => `${row.rank}-${row.customerCode ?? row.sellerName ?? ""}`}
            layout="section"
            emptyMessage="Sem dados de ranking no período."
            enableColumnReorder
            onColumnOrderChange={applyVisibleOrder}
          />
        </div>
      ) : null}
    </CommercialSectionCard>
  );
}
