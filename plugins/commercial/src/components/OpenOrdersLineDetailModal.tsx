import { ActionButton, DataTable, StatusBadge, ChartCard, chartCardBemClasses, HelpTooltip } from "@delpi/plugin-ui/index";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
import { navigateCustomerDetail } from "../app/pluginNavigation";
import { CM_HELP } from "../content/helpTooltips";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatDisplayDate, getDeliveryOverdueDays, resolveOpVsPedidoPrazo } from "../utils/dates";
import { formatCurrency, formatQuantity } from "../utils/format";
import { resolveLineCoverage } from "../utils/openOrdersLineVisual";
import { getLineOpForecast } from "../utils/opAllocation";
import { getAllocatedStock } from "../utils/stockAllocation";
import { getLineStatus } from "../utils/statusBadges";

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

const TONE_COLOR: Record<string, string> = {
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
  neutral: "#64748b",
};

export function OpenOrdersLineDetailModal({
  item,
  open,
  onClose,
  basePath,
}: OpenOrdersLineDetailModalProps) {
  if (!item) return null;

  const previsao = getLineOpForecast(item);
  const lineStatus = getLineStatus(item);
  const coverage = resolveLineCoverage(item);
  const overdueDays = getDeliveryOverdueDays(item.data_entrega);
  const description = `${item.nome_cliente || "Cliente"} · Pedido ${item.pedido || "—"} · Linha ${item.linha || "—"} · Produto ${item.produto || "—"}`;

  const coverageChart = [
    { id: "alocado", label: "Alocado", value: coverage.allocated, tone: "success" },
    {
      id: "produzir",
      label: "A produzir",
      value: Math.max(0, previsao.saldoNecessarioProducao),
      tone: "warning",
    },
  ].filter((row) => row.value > 0);

  const prazoChart = [
    {
      id: "pedido",
      label: "Entrega pedido",
      days: item.data_entrega
        ? Math.round(
            (new Date(item.data_entrega.slice(0, 10) + "T12:00:00").getTime() - Date.now()) /
              86_400_000,
          )
        : 0,
    },
    {
      id: "op",
      label: "Previsão OP",
      days: previsao.previsaoData
        ? Math.round(
            (new Date(previsao.previsaoData.slice(0, 10) + "T12:00:00").getTime() - Date.now()) /
              86_400_000,
          )
        : 0,
    },
  ];

  const opBars = previsao.opsUtilizadas.map((op) => ({
    name: op.numero_op || "OP",
    alocado: op.saldo_alocado,
    saldo: op.saldo_op_total,
  }));

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

  return (
    <CommercialWorkbenchModal
      open={open}
      onClose={onClose}
      title="Detalhe da linha"
      description={description}
      footer={
        <div className="cm-drawer-footer-actions">
          <div className="cm-open-orders-detail__footer-action">
            <ActionButton variant="ghost" onClick={copyPedido}>
              Copiar pedido
            </ActionButton>
            <HelpTooltip
              content={DETAIL.copyPedido}
              ariaLabel="Ajuda: copiar pedido"
              placement="top"
            />
          </div>
          <div className="cm-open-orders-detail__footer-action">
            <ActionButton
              variant="primary"
              onClick={openAccount}
              disabled={!item.codigo_cadastro?.trim() || !item.loja_cadastro?.trim()}
            >
              Abrir conta
            </ActionButton>
            <HelpTooltip
              content={DETAIL.openAccount}
              ariaLabel="Ajuda: abrir conta"
              placement="top"
            />
          </div>
        </div>
      }
    >
      <div className="cm-open-orders-detail">
        <div className="cm-open-orders-detail__intro">
          <HelpTooltip content={DETAIL.modal} ariaLabel="Ajuda: detalhe da linha" placement="bottom" />
          <span className="cm-open-orders-detail__intro-text">
            Indicadores e previsão OP desta linha
          </span>
        </div>

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
                  : "—",
            },
            {
              label: "Status",
              hint: DETAIL.status,
              value: (
                <StatusBadge
                  classNames={cmStatusBadgeClassNames}
                  label={lineStatus.label}
                  variant={badgeVariant(lineStatus.tone)}
                />
              ),
            },
            {
              label: "Entrega pedido",
              hint: DETAIL.entregaPedido,
              value: formatDisplayDate(item.data_entrega),
            },
            {
              label: "Previsão de entrega",
              hint: DETAIL.previsaoEntrega,
              value: previsao.previsaoLabel,
            },
          ]}
        />

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
            {coverageChart.length > 0 ? (
              <div className="cm-open-orders-detail__chart-host">
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={coverageChart} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="label" width={88} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => formatQuantity(Number(v))} />
                    <Bar dataKey="value" radius={4}>
                      {coverageChart.map((row) => (
                        <Cell key={row.id} fill={TONE_COLOR[row.tone] || TONE_COLOR.neutral} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : null}
          </ChartCard>

          <ChartCard
            classNames={chartClasses}
            title="Prazo (dias até a data)"
            titleHint={DETAIL.chartPrazo}
            hint={DETAIL.chartPrazoCaption}
          >
            <div className="cm-open-orders-detail__chart-host">
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={prazoChart} margin={{ left: 8, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="days" fill="#089bdb" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>

        {opBars.length > 0 ? (
          <ChartCard
            classNames={chartClasses}
            title="Alocação por OP"
            titleHint={DETAIL.chartOps}
            hint={DETAIL.chartOpsCaption}
          >
            <div className="cm-open-orders-detail__chart-host">
              <ResponsiveContainer width="100%" height={Math.max(140, opBars.length * 40)}>
                <BarChart data={opBars} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => formatQuantity(Number(v))} />
                  <Bar dataKey="alocado" name="Alocado" fill="#16a34a" radius={4} />
                  <Bar dataKey="saldo" name="Saldo OP" fill="#64748b" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        ) : null}

        <p className="cm-open-orders-drawer__note">
          <span>{DETAIL.opsNote}</span>
          <HelpTooltip
            content={DETAIL.opsTable}
            ariaLabel="Ajuda: tabela de OPs"
            placement="top"
          />
        </p>

        {previsao.opsUtilizadas.length > 0 ? (
          <DataTable
            rows={previsao.opsUtilizadas}
            rowKey={(row) => row.numero_op}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            columns={[
              {
                key: "op",
                header: "Número OP",
                headerHint: DETAIL.opNumero,
                render: (row) => row.numero_op || "—",
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
      </div>
    </CommercialWorkbenchModal>
  );
}
