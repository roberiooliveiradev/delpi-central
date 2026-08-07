import {
  ActionButton,
  DataTable,
  StatusBadge,
  ChartCard,
  chartCardBemClasses,
  HintAction,
  SectionHintLabel,
} from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";
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
  CommercialInlineMeter,
  CommercialWorkbenchModal,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmStatusBadgeClassNames,
  UI_PREFIX,
} from "../app/commercialUi";
import {
  navigateAnalyticsOpportunityDetail,
  navigateCustomerDetail,
} from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
import { useOpenOrdersLineDetailExtras } from "../hooks/useOpenOrdersLineDetailExtras";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import {
  formatDaysFromTodayLabel,
  formatDisplayDate,
  getDaysFromToday,
  getDeliveryOverdueDays,
  resolveOpVsPedidoPrazo,
} from "../utils/dates";
import { formatCurrency, formatQuantity } from "../utils/format";
import { displayApiScalar } from "../utils/displayApiScalar";
import { forecastKindBadgeVariant, forecastKindLabel } from "../utils/forecastKindLabel";
import { resolveLineCoverage } from "../utils/openOrdersLineVisual";
import { getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus } from "../utils/statusBadges";
import { OpenOrdersFactoryStatusStrip } from "./OpenOrdersFactoryStatusStrip";
import { OpenOrdersOpProgressBlock } from "./OpenOrdersOpProgressBlock";
import { OpenOrdersProductStructureAccordion } from "./OpenOrdersProductStructureAccordion";

const chartClasses = chartCardBemClasses(UI_PREFIX);
const DETAIL = CM_HELP.openOrders.detail;

type OpenOrdersLineDetailModalProps = {
  item: OpenOrdersTotvsItem | null;
  open: boolean;
  onClose: () => void;
  basePath?: string;
};

function prazoVariant(
  status: ReturnType<typeof resolveOpVsPedidoPrazo>["status"],
): "success" | "danger" | "neutral" {
  if (status === "no_prazo") return "success";
  if (status === "atrasado") return "danger";
  return "neutral";
}

function badgeVariant(
  tone: ReturnType<typeof getLineStatus>["tone"],
): "neutral" | "info" | "success" | "warning" | "danger" {
  if (tone === "success") return "success";
  if (tone === "warning") return "warning";
  if (tone === "danger") return "danger";
  if (tone === "info") return "info";
  return "neutral";
}

export function OpenOrdersLineDetailModal({
  item,
  open,
  onClose,
  basePath,
}: OpenOrdersLineDetailModalProps) {
  const previsao = item ? getLineOpForecast(item) : null;
  const [selectedOp, setSelectedOp] = useState("");
  const extras = useOpenOrdersLineDetailExtras(item, open, selectedOp);

  useEffect(() => {
    if (!previsao?.opsUtilizadas.length) {
      setSelectedOp("");
      return;
    }
    setSelectedOp((current) => {
      if (current && previsao.opsUtilizadas.some((op) => op.numero_op === current)) {
        return current;
      }
      return previsao.opsUtilizadas[0].numero_op;
    });
  }, [previsao]);

  if (!item || !previsao) return null;

  const lineStatus = getLineStatus(item);
  const coverage = resolveLineCoverage(item);
  const overdueDays = getDeliveryOverdueDays(item.data_entrega);
  const deliveryDays = getDaysFromToday(item.data_entrega);
  const forecastDays = getDaysFromToday(previsao.previsaoData);
  const description = `${item.nome_cliente || "Cliente"} · Pedido ${item.pedido || "—"} · Linha ${item.linha || "—"} · Produto ${item.produto || "—"}`;

  const coverageStacked = (() => {
    const estoqueQty = Math.max(0, coverage.allocated);
    const produzirQty = Math.max(0, previsao.saldoNecessarioProducao);
    const total = estoqueQty + produzirQty;
    if (total <= 0) {
      return [
        {
          name: "Demanda",
          estoque: 0,
          produzir: 0,
          estoqueQty: 0,
          produzirQty: 0,
        },
      ];
    }
    return [
      {
        name: "Demanda",
        estoque: (estoqueQty / total) * 100,
        produzir: (produzirQty / total) * 100,
        estoqueQty,
        produzirQty,
      },
    ];
  })();

  const prazoCompare = [
    {
      id: "pedido",
      label: "Entrega",
      days: deliveryDays ?? 0,
      fill: (deliveryDays ?? 0) < 0 ? "#dc2626" : "#089bdb",
    },
    {
      id: "op",
      label: "Prev. OP",
      days: forecastDays ?? 0,
      fill: (forecastDays ?? 0) < 0 ? "#dc2626" : "#16a34a",
    },
  ].filter((row) => {
    if (row.id === "op" && !previsao.previsaoData) return false;
    if (row.id === "pedido" && !item.data_entrega) return false;
    return true;
  });

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

  const openAccount = () => {
    const code = item.codigo_cadastro?.trim();
    const store = item.loja_cadastro?.trim();
    if (!code || !store) return;
    navigateCustomerDetail(code, store, { basePath });
    onClose();
  };

  const openOv = () => {
    const ov = extras.proposalNumber?.trim();
    if (!ov) return;
    const search = new URLSearchParams();
    if (extras.proposalBranch) search.set("branch", extras.proposalBranch);
    navigateAnalyticsOpportunityDetail(ov, {
      basePath,
      search: search.toString() ? `?${search.toString()}` : undefined,
    });
    onClose();
  };

  return (
    <CommercialWorkbenchModal
      open={open}
      onClose={onClose}
      title="Detalhe da linha"
      description={description}
      footer={
        <div className="cm-drawer-footer-actions">
          <HintAction hint={DETAIL.copyPedido} ariaLabel="Ajuda: copiar pedido" placement="top">
            <ActionButton variant="ghost" onClick={copyPedido}>
              Copiar pedido
            </ActionButton>
          </HintAction>
          {extras.proposalNumber ? (
            <HintAction hint={DETAIL.openOv} ariaLabel="Ajuda: ver OV" placement="top">
              <ActionButton variant="ghost" onClick={openOv}>
                Ver OV {extras.proposalNumber}
              </ActionButton>
            </HintAction>
          ) : null}
          <HintAction hint={DETAIL.openAccount} ariaLabel="Ajuda: abrir conta" placement="top">
            <ActionButton
              variant="primary"
              onClick={openAccount}
              disabled={!item.codigo_cadastro?.trim() || !item.loja_cadastro?.trim()}
            >
              Abrir conta
            </ActionButton>
          </HintAction>
        </div>
      }
    >
      <div className="cm-open-orders-detail">
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
            <li className="cm-open-orders-detail__guide-step">
              <SectionHintLabel label="Resumo" hint={DETAIL.guideResumo} />
            </li>
            <li className="cm-open-orders-detail__guide-step">
              <SectionHintLabel label="Fabril" hint={DETAIL.guideFabril} />
            </li>
            <li className="cm-open-orders-detail__guide-step">
              <SectionHintLabel label="Indicadores" hint={DETAIL.guideIndicadores} />
            </li>
            <li className="cm-open-orders-detail__guide-step">
              <SectionHintLabel label="Cobertura / prazo" hint={DETAIL.guideCobertura} />
            </li>
            <li className="cm-open-orders-detail__guide-step">
              <SectionHintLabel label="Produção OP" hint={DETAIL.guideProducao} />
            </li>
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
            fields={[
              {
                label: "Saldo do pedido",
                hint: DETAIL.saldo,
                value: formatQuantity(item.saldo),
              },
              {
                label: "Estoque alocado",
                hint: DETAIL.estoqueAlocado,
                value: formatQuantity(getAllocatedStock(item)),
              },
              {
                label: "Saldo a produzir",
                hint: DETAIL.saldoProduzir,
                value: formatQuantity(previsao.saldoNecessarioProducao),
              },
              {
                label: "Valor aberto",
                hint: DETAIL.valorAberto,
                value: formatCurrency(item.valor_aberto),
              },
              {
                label: "Atraso",
                hint: DETAIL.atraso,
                value:
                  overdueDays != null && item.saldo > 0
                    ? `${overdueDays.toLocaleString("pt-BR")} dia(s)`
                    : "No prazo",
              },
              {
                label: "Despacho",
                hint: DETAIL.despacho,
                value: item.data_despacho
                  ? formatDisplayDate(item.data_despacho)
                  : "Não informado",
              },
              {
                label: "Ainda falta produzir",
                hint: DETAIL.coberturaKind,
                value:
                  previsao.kind === "parcial" && previsao.saldoFaltanteProducao > 0
                    ? formatQuantity(previsao.saldoFaltanteProducao)
                    : previsao.kind === "estoque" || previsao.kind === "coberto"
                      ? "0 (estoque / OP cobre)"
                      : previsao.saldoNecessarioProducao > 0
                        ? formatQuantity(previsao.saldoNecessarioProducao)
                        : "Não aplicável",
              },
            ]}
          />
        </section>

        <div className="cm-open-orders-detail__charts">
          <ChartCard
            classNames={chartClasses}
            title="Cobertura estoque × demanda"
            titleHint={DETAIL.chartCobertura}
            hint={`${coverage.percentLabel} · ${coverage.quantityLabel}`}
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
          onSelectOp={setSelectedOp}
          orderDeliveryDate={item.data_entrega}
          branch={item.filial}
          extrasByOp={extras.opsByNumber}
          loadingExtras={extras.loading}
          opsPrefetchTruncated={extras.opsPrefetchTruncated}
        />

        <p className="cm-open-orders-drawer__note">
          <SectionHintLabel label={DETAIL.opsNote} hint={DETAIL.opsTable} />
        </p>

        {previsao.opsUtilizadas.length > 0 ? (
          <DataTable
            rows={previsao.opsUtilizadas}
            rowKey={(row) => row.numero_op}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            onRowClick={(row) => setSelectedOp(row.numero_op)}
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
    </CommercialWorkbenchModal>
  );
}
