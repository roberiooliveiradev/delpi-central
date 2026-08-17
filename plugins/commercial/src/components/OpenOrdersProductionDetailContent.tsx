import {
  ActionButton,
  DataTable,
  StatusBadge,
  ChartCard,
  chartCardBemClasses,
  HintAction,
  SectionHintLabel,
  runTabularExport,
} from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  CommercialDetailFieldGrid,
  CommercialDataRecordCard,
  CommercialInlineMeter,
  CommercialTabularExportButtons,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmStatusBadgeClassNames,
  UI_PREFIX,
} from "../app/commercialUi";
import {
  buildAnalyticsOpportunityDetailHref,
  buildCustomerDetailHref,
  buildOpenOrderOpDetailPath,
  navigateAnalyticsOpportunityDetail,
  navigateCustomerDetail,
  navigateOpenOrderOpDetail,
} from "../app/pluginNavigation";
import { currentReturnNav } from "../app/commercialNavigationReturn";
import {
  accountLinkTitle,
  opPageLinkTitle,
  opportunityLinkTitle,
} from "../content/entityLinkHints";
import { CM_HELP } from "../content/helpTooltips";
import { useOpenOrdersLineDetailExtras } from "../hooks/useOpenOrdersLineDetailExtras";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import type { OpAllocationEntry } from "../types/opForecast";
import {
  formatDaysFromTodayLabel,
  formatDisplayDate,
  resolveOpVsPedidoPrazo,
} from "../utils/dates";
import { formatQuantity } from "../utils/format";
import { displayApiScalar } from "../utils/displayApiScalar";
import { forecastKindBadgeVariant, forecastKindLabel } from "../utils/forecastKindLabel";
import { buildOpenOrdersContextSearch } from "../utils/openOrdersDeepLink";
import { buildOpenOrdersProductionDetailViewModel } from "../utils/openOrdersProductionDetailViewModel";
import type { BadgeTone } from "../utils/statusBadges";
import { OpenOrdersFactoryStatusStrip } from "./OpenOrdersFactoryStatusStrip";
import { OpenOrdersOpProgressBlock } from "./OpenOrdersOpProgressBlock";
import { OpenOrdersProductStructureAccordion } from "./OpenOrdersProductStructureAccordion";

const chartClasses = chartCardBemClasses(UI_PREFIX);
const DETAIL = CM_HELP.openOrders.detail;

type OpenOrdersProductionDetailContentProps = {
  item: OpenOrdersTotvsItem;
  basePath?: string;
  productionOrder?: string;
  search?: string;
  onProductionOrderChange?: (productionOrder: string) => void;
  showOpenProductionOrderAction?: boolean;
  onNavigate?: () => void;
};

function prazoVariant(
  status: ReturnType<typeof resolveOpVsPedidoPrazo>["status"],
): "success" | "danger" | "neutral" {
  if (status === "no_prazo") return "success";
  if (status === "atrasado") return "danger";
  return "neutral";
}

function badgeVariant(
  tone: BadgeTone,
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (tone === "success") return "success";
  if (tone === "warning") return "warning";
  if (tone === "danger") return "danger";
  if (tone === "info") return "info";
  return "neutral";
}

export function OpenOrdersProductionDetailContent({
  item,
  basePath,
  productionOrder,
  search,
  onProductionOrderChange,
  showOpenProductionOrderAction = true,
  onNavigate,
}: OpenOrdersProductionDetailContentProps) {
  const detail = useMemo(
    () => buildOpenOrdersProductionDetailViewModel(item, productionOrder),
    [item, productionOrder],
  );
  const previsao = detail.forecast;
  const [selectedOp, setSelectedOp] = useState(detail.selectedProductionOrder);
  const extras = useOpenOrdersLineDetailExtras(item, true, selectedOp);

  useEffect(() => {
    if (!previsao?.opsUtilizadas.length) {
      setSelectedOp("");
      return;
    }
    setSelectedOp((current) => {
      if (productionOrder?.trim() && detail.selectedProductionOrder) {
        return detail.selectedProductionOrder;
      }
      if (current && previsao.opsUtilizadas.some((op) => op.numero_op.trim() === current)) {
        return current;
      }
      return detail.selectedProductionOrder;
    });
  }, [detail.selectedProductionOrder, previsao, productionOrder]);

  const {
    lineStatus,
    coverage,
    deliveryDays,
    forecastDays,
    coverageChart: coverageStacked,
    deadlineChart: prazoCompare,
  } = detail;
  const metricHints = {
    order_balance: DETAIL.saldo,
    allocated_stock: DETAIL.estoqueAlocado,
    production_balance: DETAIL.saldoProduzir,
    open_value: DETAIL.valorAberto,
    delay: DETAIL.atraso,
    dispatch: DETAIL.despacho,
    remaining_production: DETAIL.coberturaKind,
  };

  const snapshotTone = {
    situacao: lineStatus.tone === "danger" || lineStatus.tone === "warning" ? lineStatus.tone : "neutral",
    cobertura:
      coverage.tone === "success" ? "success" : coverage.tone === "danger" ? "danger" : "neutral",
    entrega: (deliveryDays ?? 0) < 0 ? "danger" : "neutral",
    previsao: (forecastDays ?? 0) < 0 ? "warning" : "neutral",
  } as const;

  const copyPedido = async () => {
    const text = item.pedido?.trim();
    if (!text || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* ignore */
    }
  };

  const accountCode = item.codigo_cadastro?.trim() ?? "";
  const accountStore = item.loja_cadastro?.trim() ?? "";
  const accountName = item.nome_cliente?.trim() || accountCode || "cliente";
  const accountReturnNav = currentReturnNav("Pedidos em aberto");
  const accountHref =
    accountCode && accountStore
      ? buildCustomerDetailHref(accountCode, accountStore, {
          basePath,
          search: "",
          returnNav: accountReturnNav,
        })
      : null;

  const ovNumber = extras.proposalNumber?.trim() || "";
  const ovSearch = (() => {
    if (!ovNumber) return undefined;
    const search = new URLSearchParams();
    if (extras.proposalBranch) search.set("branch", extras.proposalBranch);
    return search.toString() ? `?${search.toString()}` : undefined;
  })();
  const ovHref = ovNumber
    ? buildAnalyticsOpportunityDetailHref(ovNumber, {
        basePath,
        search: ovSearch,
      })
    : null;

  const opContextSearch = buildOpenOrdersContextSearch(search);
  const opHref = selectedOp
    ? buildOpenOrderOpDetailPath(
        basePath,
        item.filial,
        item.pedido,
        item.linha,
        selectedOp,
        opContextSearch,
      )
    : null;

  const openAccount = () => {
    if (!accountCode || !accountStore) return;
    navigateCustomerDetail(accountCode, accountStore, {
      basePath,
      returnNav: accountReturnNav,
    });
    onNavigate?.();
  };

  const openOv = () => {
    if (!ovNumber) return;
    navigateAnalyticsOpportunityDetail(ovNumber, {
      basePath,
      search: ovSearch,
    });
    onNavigate?.();
  };

  const openProductionOrder = () => {
    if (!selectedOp) return;
    navigateOpenOrderOpDetail(
      item.filial,
      item.pedido,
      item.linha,
      selectedOp,
      {
        basePath,
        search: opContextSearch,
      },
    );
    onNavigate?.();
  };

  const selectProductionOrder = (numeroOp: string) => {
    setSelectedOp(numeroOp);
    onProductionOrderChange?.(numeroOp);
  };

  return (
    <div className="cm-open-orders-detail">
      <div className="cm-detail-actions" aria-label="Ações do detalhe">
        {selectedOp && showOpenProductionOrderAction && opHref ? (
          <ActionButton
            variant="primary"
            href={opHref}
            title={opPageLinkTitle(selectedOp)}
            onClick={openProductionOrder}
          >
            Abrir página da OP {selectedOp}
          </ActionButton>
        ) : null}
          <HintAction hint={DETAIL.copyPedido} ariaLabel="Ajuda: copiar pedido" placement="top">
            <ActionButton variant="ghost" onClick={copyPedido}>
              Copiar pedido
            </ActionButton>
          </HintAction>
          {ovNumber && ovHref ? (
            <HintAction hint={DETAIL.openOv} ariaLabel="Ajuda: ver OV" placement="top">
              <ActionButton
                variant="ghost"
                href={ovHref}
                title={opportunityLinkTitle(ovNumber)}
                onClick={openOv}
              >
                Ver OV {ovNumber}
              </ActionButton>
            </HintAction>
          ) : null}
          <HintAction hint={DETAIL.openAccount} ariaLabel="Ajuda: abrir conta" placement="top">
            {accountHref ? (
              <ActionButton
                variant="primary"
                href={accountHref}
                title={accountLinkTitle(accountName)}
                onClick={openAccount}
              >
                Abrir conta
              </ActionButton>
            ) : (
              <ActionButton variant="primary" disabled>
                Abrir conta
              </ActionButton>
            )}
          </HintAction>
      </div>
        <div className="cm-open-orders-detail__snapshot" aria-label="Resumo da linha">
          <div
            className={[
              "cm-open-orders-detail__snapshot-card",
              `cm-open-orders-detail__snapshot-card--${snapshotTone.situacao}`,
            ].join(" ")}
          >
            <SectionHintLabel
              label="Situação"
              hint={DETAIL.snapshotSituacao}
              className="cm-open-orders-detail__snapshot-label"
            />
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={lineStatus.label}
              variant={badgeVariant(lineStatus.tone)}
            />
          </div>
          <div
            className={[
              "cm-open-orders-detail__snapshot-card",
              `cm-open-orders-detail__snapshot-card--${snapshotTone.cobertura}`,
            ].join(" ")}
          >
            <SectionHintLabel
              label="Cobertura"
              hint={DETAIL.snapshotCobertura}
              className="cm-open-orders-detail__snapshot-label"
            />
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={forecastKindLabel(previsao.kind)}
              variant={forecastKindBadgeVariant(previsao.kind)}
            />
            <span className="cm-open-orders-detail__snapshot-meta">{coverage.percentLabel}</span>
          </div>
          <div
            className={[
              "cm-open-orders-detail__snapshot-card",
              `cm-open-orders-detail__snapshot-card--${snapshotTone.entrega}`,
            ].join(" ")}
          >
            <SectionHintLabel
              label="Entrega pedido"
              hint={DETAIL.entregaPedido}
              className="cm-open-orders-detail__snapshot-label"
            />
            <strong className="cm-open-orders-detail__snapshot-value">
              {formatDisplayDate(item.data_entrega)}
            </strong>
            <span
              className={
                (deliveryDays ?? 0) < 0
                  ? "cm-open-orders-detail__snapshot-meta cm-open-orders-detail__snapshot-meta--danger"
                  : "cm-open-orders-detail__snapshot-meta"
              }
            >
              {formatDaysFromTodayLabel(deliveryDays)}
            </span>
          </div>
          <div
            className={[
              "cm-open-orders-detail__snapshot-card",
              `cm-open-orders-detail__snapshot-card--${snapshotTone.previsao}`,
            ].join(" ")}
          >
            <SectionHintLabel
              label="Previsão OP"
              hint={DETAIL.previsaoEntrega}
              className="cm-open-orders-detail__snapshot-label"
            />
            <strong className="cm-open-orders-detail__snapshot-value">{previsao.previsaoLabel}</strong>
            <span
              className={
                (forecastDays ?? 0) < 0
                  ? "cm-open-orders-detail__snapshot-meta cm-open-orders-detail__snapshot-meta--danger"
                  : "cm-open-orders-detail__snapshot-meta"
              }
            >
              {previsao.previsaoData ? formatDaysFromTodayLabel(forecastDays) : "Sem data de OP"}
            </span>
          </div>
        </div>

        <nav className="cm-open-orders-detail__guide" aria-label="Seções do detalhe">
          <ol className="cm-open-orders-detail__guide-list">
            {detail.sections
              .filter((section) => section.guideLabel)
              .map((section) => {
                const hints = {
                  snapshot: DETAIL.guideResumo,
                  factory: DETAIL.guideFabril,
                  metrics: DETAIL.guideIndicadores,
                  coverage_deadline: DETAIL.guideCobertura,
                  production_order: DETAIL.guideProducao,
                  product_structure: DETAIL.guideProducao,
                };
                return (
                  <li key={section.id} className="cm-open-orders-detail__guide-step">
                    <SectionHintLabel
                      label={section.guideLabel ?? section.label}
                      hint={hints[section.id]}
                      className="cm-open-orders-detail__guide-label"
                    />
                  </li>
                );
              })}
          </ol>
        </nav>

        <OpenOrdersFactoryStatusStrip
          loading={extras.loading}
          data={extras.factoryStatus}
          forbidden={extras.factoryForbidden}
          error={extras.factoryError}
        />

        <section className="cm-open-orders-detail__metrics" aria-label="Indicadores da linha">
          <h3 className="cm-open-orders-detail__metrics-title">
            <SectionHintLabel label="Indicadores da linha" hint={DETAIL.metricsTitle} />
          </h3>
          <CommercialDetailFieldGrid
            valueFallback="—"
            wrapLabels
            fields={detail.metrics.map((metric) => ({
              label: metric.label,
              hint: metricHints[metric.id],
              value: metric.value,
            }))}
          />
        </section>

        <div className="cm-open-orders-detail__charts">
          <ChartCard
            classNames={chartClasses}
            title="Cobertura estoque × demanda"
            titleHint={DETAIL.chartCobertura}
            hint={`${coverage.percentLabel} · ${coverage.quantityLabel}`}
            headerActions={
              <CommercialTabularExportButtons
                compact
                disabled={
                  !(
                    coverageStacked[0]?.estoqueQty > 0 ||
                    coverageStacked[0]?.produzirQty > 0
                  )
                }
                onExport={(format) => {
                  runTabularExport({
                    kind: "table",
                    format,
                    payload: {
                      title: "Cobertura estoque × demanda",
                      columns: [
                        { key: "serie", label: "Série" },
                        { key: "qty", label: "Quantidade" },
                        { key: "pct", label: "%" },
                      ],
                      rows: [
                        {
                          serie: "Estoque alocado",
                          qty: coverageStacked[0]?.estoqueQty ?? 0,
                          pct: coverageStacked[0]?.estoque ?? 0,
                        },
                        {
                          serie: "A produzir",
                          qty: coverageStacked[0]?.produzirQty ?? 0,
                          pct: coverageStacked[0]?.produzir ?? 0,
                        },
                      ],
                    },
                  });
                }}
              />
            }
          >
            <div className="cm-open-orders-detail__meter-block">
              <CommercialInlineMeter
                value={coverage.ratio}
                max={1}
                tone={coverage.tone}
                size="md"
                label={coverage.quantityLabel}
                aria-label="Cobertura de estoque"
              />
            </div>
            {coverageStacked[0].estoqueQty > 0 || coverageStacked[0].produzirQty > 0 ? (
              <div className="cm-open-orders-detail__chart-host cm-open-orders-detail__chart-host--compact">
                <ResponsiveContainer width="100%" height={112}>
                  <BarChart
                    data={coverageStacked}
                    layout="vertical"
                    margin={{ top: 8, right: 16, left: 8, bottom: 4 }}
                    barCategoryGap={18}
                    barSize={28}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                      stroke="var(--cm-border)"
                    />
                    <XAxis
                      type="number"
                      domain={[0, 100]}
                      tickFormatter={(v) => `${Math.round(Number(v))}%`}
                      tick={{ fontSize: 11, fill: "var(--cm-text-muted)" }}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={64}
                      tick={{ fontSize: 11, fill: "var(--cm-text-muted)" }}
                    />
                    <Tooltip
                      formatter={(v, name, item) => {
                        const payload = item?.payload as
                          | { estoqueQty?: number; produzirQty?: number }
                          | undefined;
                        const qty =
                          name === "estoque"
                            ? payload?.estoqueQty
                            : payload?.produzirQty;
                        return [
                          `${formatQuantity(Number(qty ?? 0))} (${Math.round(Number(v))}%)`,
                          name === "estoque" ? "Estoque alocado" : "A produzir",
                        ];
                      }}
                      contentStyle={{
                        background: "var(--cm-surface)",
                        border: "1px solid var(--cm-border)",
                        color: "var(--cm-text)",
                      }}
                    />
                    <Legend
                      formatter={(value) =>
                        value === "estoque" ? "Estoque alocado" : "A produzir"
                      }
                    />
                    <Bar dataKey="estoque" stackId="cov" fill="#16a34a" radius={[4, 0, 0, 4]} />
                    <Bar dataKey="produzir" stackId="cov" fill="#d97706" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="cm-open-orders-detail__muted">Sem saldo a cobrir nesta linha.</p>
            )}
          </ChartCard>

          <ChartCard
            classNames={chartClasses}
            title="Prazo vs hoje"
            titleHint={DETAIL.chartPrazo}
            hint="Negativo = já passou · positivo = dias restantes"
            headerActions={
              <CommercialTabularExportButtons
                compact
                disabled={prazoCompare.length === 0}
                onExport={(format) => {
                  runTabularExport({
                    kind: "table",
                    format,
                    payload: {
                      title: "Prazo vs hoje",
                      columns: [
                        { key: "label", label: "Referência" },
                        { key: "days", label: "Dias vs hoje" },
                      ],
                      rows: prazoCompare.map((row) => ({
                        label: row.label,
                        days: row.days,
                      })),
                    },
                  });
                }}
              />
            }
          >
            <div className="cm-open-orders-detail__prazo-cards">
              <div className="cm-open-orders-detail__prazo-card">
                <SectionHintLabel
                  label="Entrega pedido"
                  hint={DETAIL.entregaPedido}
                  className="cm-open-orders-detail__snapshot-label"
                />
                <strong className="cm-open-orders-detail__snapshot-value">
                  {formatDisplayDate(item.data_entrega)}
                </strong>
                <span
                  className={
                    (deliveryDays ?? 0) < 0
                      ? "cm-open-orders-detail__snapshot-meta--danger"
                      : "cm-open-orders-detail__snapshot-meta"
                  }
                >
                  {formatDaysFromTodayLabel(deliveryDays)}
                </span>
              </div>
              <div className="cm-open-orders-detail__prazo-card">
                <SectionHintLabel
                  label="Previsão OP"
                  hint={DETAIL.previsaoEntrega}
                  className="cm-open-orders-detail__snapshot-label"
                />
                <strong className="cm-open-orders-detail__snapshot-value">
                  {previsao.previsaoLabel}
                </strong>
                <span
                  className={
                    (forecastDays ?? 0) < 0
                      ? "cm-open-orders-detail__snapshot-meta--danger"
                      : "cm-open-orders-detail__snapshot-meta"
                  }
                >
                  {formatDaysFromTodayLabel(forecastDays)}
                </span>
              </div>
            </div>
            {prazoCompare.length > 0 ? (
              <div className="cm-open-orders-detail__chart-host cm-open-orders-detail__chart-host--compact">
                <ResponsiveContainer width="100%" height={132}>
                  <BarChart
                    data={prazoCompare}
                    margin={{ top: 12, right: 12, left: 4, bottom: 4 }}
                    barCategoryGap="28%"
                    barSize={40}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--cm-border)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: "var(--cm-text-muted)" }}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "var(--cm-text-muted)" }}
                      tickFormatter={(v) => `${v}d`}
                      width={40}
                    />
                    <ReferenceLine
                      y={0}
                      stroke="var(--cm-accent, #089bdb)"
                      strokeDasharray="4 4"
                      strokeWidth={1.5}
                    />
                    <Tooltip
                      formatter={(v) => [`${Number(v)} dia(s)`, "Relativo a hoje"]}
                      contentStyle={{
                        background: "var(--cm-surface)",
                        border: "1px solid var(--cm-border)",
                        color: "var(--cm-text)",
                      }}
                    />
                    <Bar dataKey="days" radius={[6, 6, 0, 0]}>
                      {prazoCompare.map((row) => (
                        <Cell key={row.id} fill={row.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="cm-open-orders-detail__muted">Sem datas de entrega ou previsão OP.</p>
            )}
          </ChartCard>
        </div>

        <OpenOrdersOpProgressBlock
          ops={previsao.opsUtilizadas}
          selectedOp={selectedOp}
          onSelectOp={selectProductionOrder}
          orderDeliveryDate={item.data_entrega}
          extrasByOp={extras.opsByNumber}
          loadingExtras={extras.loading}
          opsPrefetchTruncated={extras.opsPrefetchTruncated}
        />

        <p className="cm-open-orders-drawer__note">
          <SectionHintLabel label={DETAIL.opsNote} hint={DETAIL.opsTable} />
        </p>

        {previsao.opsUtilizadas.length > 0 ? (
          <>
          <div className="cm-responsive-records__desktop">
            <DataTable
            rows={previsao.opsUtilizadas}
            rowKey={(row) => row.numero_op}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            onRowClick={(row) => selectProductionOrder(row.numero_op)}
            columns={[
              {
                key: "op",
                header: "Número OP",
                headerHint: DETAIL.opNumero,
                render: (row) => (
                  <strong
                    className={
                      row.numero_op === selectedOp
                        ? "cm-open-orders-detail__op-selected"
                        : undefined
                    }
                  >
                    {row.numero_op || "—"}
                  </strong>
                ),
              },
              {
                key: "produzido",
                header: "Produzido",
                headerHint: DETAIL.opProduzido,
                align: "right",
                render: (row) => {
                  const produced =
                    extras.opsByNumber[row.numero_op]?.byOp?.order?.produced_qty ??
                    row.quantidade_produzida;
                  return formatQuantity(produced);
                },
              },
              {
                key: "planejado",
                header: "Planejado",
                headerHint: DETAIL.opPlanejado,
                align: "right",
                render: (row) => {
                  const planned =
                    extras.opsByNumber[row.numero_op]?.byOp?.order?.planned_qty ??
                    row.quantidade_op;
                  return formatQuantity(planned);
                },
              },
              {
                key: "saldo",
                header: "Saldo OP",
                headerHint: DETAIL.opSaldo,
                align: "right",
                render: (row) => formatQuantity(row.saldo_op_total),
              },
              {
                key: "alocado",
                header: "Alocado p/ o pedido",
                headerHint: DETAIL.opAlocado,
                align: "right",
                render: (row) => formatQuantity(row.saldo_alocado),
              },
              {
                key: "fim",
                header: "Fim previsto",
                headerHint: DETAIL.opFim,
                render: (row) =>
                  row.data_fim_prevista_op
                    ? formatDisplayDate(row.data_fim_prevista_op)
                    : "Sem data prevista",
              },
              {
                key: "status",
                header: "Status",
                headerHint: DETAIL.opStatus,
                render: (row) => {
                  const orderStatus = displayApiScalar(
                    extras.opsByNumber[row.numero_op]?.byOp?.order?.order_status,
                    "",
                  );
                  if (orderStatus) {
                    return (
                      <StatusBadge
                        classNames={cmStatusBadgeClassNames}
                        label={orderStatus}
                        variant="neutral"
                      />
                    );
                  }
                  const prazo = resolveOpVsPedidoPrazo(
                    row.data_fim_prevista_op,
                    item.data_entrega,
                  );
                  if (prazo.status === "indeterminado") return "—";
                  return (
                    <StatusBadge
                      classNames={cmStatusBadgeClassNames}
                      label={prazo.label}
                      variant={prazoVariant(prazo.status)}
                    />
                  );
                },
              },
              {
                key: "otd",
                header: "OTD",
                headerHint: DETAIL.opOtd,
                render: (row) => {
                  const otd = extras.opsByNumber[row.numero_op]?.byOp?.order?.otd_status;
                  if (!otd) return "—";
                  const label =
                    otd === "on_time" ? "No prazo" : otd === "late" ? "Atrasado" : otd;
                  return (
                    <StatusBadge
                      classNames={cmStatusBadgeClassNames}
                      label={label}
                      variant={otd === "late" ? "danger" : otd === "on_time" ? "success" : "info"}
                    />
                  );
                },
              },
              {
                key: "obs",
                header: "Observação",
                headerHint: DETAIL.opObs,
                render: (row) => row.observacao_op || "—",
              },
            ]}
            />
          </div>
          <div className="cm-responsive-records__mobile" aria-label="Ordens de produção">
            {previsao.opsUtilizadas.map((row: OpAllocationEntry) => {
              const byOp = extras.opsByNumber[row.numero_op]?.byOp?.order;
              const produced = byOp?.produced_qty ?? row.quantidade_produzida;
              const planned = byOp?.planned_qty ?? row.quantidade_op;
              const otd = byOp?.otd_status;
              return (
                <CommercialDataRecordCard
                  key={row.numero_op}
                  title={`OP ${row.numero_op || "não informada"}`}
                  subtitle={row.descricao_produto || item.produto || "Produto não informado"}
                  status={
                    otd ? (
                      <StatusBadge
                        classNames={cmStatusBadgeClassNames}
                        label={otd === "on_time" ? "No prazo" : otd === "late" ? "Atrasado" : otd}
                        variant={otd === "late" ? "danger" : otd === "on_time" ? "success" : "info"}
                      />
                    ) : undefined
                  }
                  fields={[
                    { id: "produced", label: "Produzido", value: formatQuantity(produced) },
                    { id: "planned", label: "Planejado", value: formatQuantity(planned) },
                    { id: "balance", label: "Saldo OP", value: formatQuantity(row.saldo_op_total) },
                    { id: "allocated", label: "Alocado", value: formatQuantity(row.saldo_alocado) },
                    {
                      id: "end",
                      label: "Fim previsto",
                      value: row.data_fim_prevista_op
                        ? formatDisplayDate(row.data_fim_prevista_op)
                        : "Sem data prevista",
                    },
                    { id: "note", label: "Observação", value: row.observacao_op || "—" },
                  ]}
                  context={
                    <ActionButton variant="ghost" onClick={() => selectProductionOrder(row.numero_op)}>
                      {row.numero_op === selectedOp ? "OP selecionada" : "Selecionar OP"}
                    </ActionButton>
                  }
                />
              );
            })}
          </div>
          </>
        ) : (
          <p className="cm-open-orders-drawer__empty">Nenhuma OP alocada para esta linha.</p>
        )}

        <OpenOrdersProductStructureAccordion
          structure={extras.productStructure}
          error={extras.structureError}
          productCode={item.produto}
          loading={extras.loading}
        />
    </div>
  );
}
