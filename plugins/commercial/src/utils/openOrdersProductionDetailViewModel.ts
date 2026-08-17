import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import {
  formatDisplayDate,
  getDaysFromToday,
  getDeliveryOverdueDays,
} from "./dates";
import { formatCurrency, formatQuantity } from "./format";
import { resolveLineCoverage } from "./openOrdersLineVisual";
import { getLineOpForecast } from "./opAllocation";
import { getAllocatedStock } from "./stockAllocation";
import { getLineStatus } from "./statusBadges";

export type OpenOrdersProductionDetailSectionId =
  | "snapshot"
  | "factory"
  | "metrics"
  | "coverage_deadline"
  | "production_order"
  | "product_structure";

export type OpenOrdersProductionDetailSection = {
  id: OpenOrdersProductionDetailSectionId;
  label: string;
  guideLabel?: string;
  data: unknown;
};

export type OpenOrdersProductionDetailViewModel = ReturnType<
  typeof buildOpenOrdersProductionDetailViewModel
>;

function resolveSelectedProductionOrder(
  item: OpenOrdersTotvsItem,
  requestedProductionOrder?: string,
): string {
  const ops = getLineOpForecast(item).opsUtilizadas;
  const requested = requestedProductionOrder?.trim();
  if (requested) {
    const match = ops.find((op) => op.numero_op.trim() === requested);
    if (match) return match.numero_op.trim();
  }
  return ops[0]?.numero_op.trim() ?? "";
}

export function buildOpenOrdersProductionDetailViewModel(
  item: OpenOrdersTotvsItem,
  requestedProductionOrder?: string,
) {
  const forecast = getLineOpForecast(item);
  const lineStatus = getLineStatus(item);
  const coverage = resolveLineCoverage(item);
  const deliveryDays = getDaysFromToday(item.data_entrega);
  const forecastDays = getDaysFromToday(forecast.previsaoData);
  const overdueDays = getDeliveryOverdueDays(item.data_entrega);
  const selectedProductionOrder = resolveSelectedProductionOrder(
    item,
    requestedProductionOrder,
  );
  const stockQuantity = Math.max(0, coverage.allocated);
  const productionQuantity = Math.max(0, forecast.saldoNecessarioProducao);
  const coverageTotal = stockQuantity + productionQuantity;
  const coverageChart = [
    {
      name: "Demanda",
      estoque: coverageTotal > 0 ? (stockQuantity / coverageTotal) * 100 : 0,
      produzir: coverageTotal > 0 ? (productionQuantity / coverageTotal) * 100 : 0,
      estoqueQty: stockQuantity,
      produzirQty: productionQuantity,
    },
  ];
  const deadlineChart = [
    {
      id: "pedido",
      label: "Entrega",
      days: deliveryDays ?? 0,
      fill: (deliveryDays ?? 0) < 0 ? "#dc2626" : "#089bdb",
      available: Boolean(item.data_entrega),
    },
    {
      id: "op",
      label: "Prev. OP",
      days: forecastDays ?? 0,
      fill: (forecastDays ?? 0) < 0 ? "#dc2626" : "#16a34a",
      available: Boolean(forecast.previsaoData),
    },
  ].filter((row) => row.available);
  const metrics = [
    { id: "order_balance", label: "Saldo do pedido", value: formatQuantity(item.saldo) },
    {
      id: "allocated_stock",
      label: "Estoque alocado",
      value: formatQuantity(getAllocatedStock(item)),
    },
    {
      id: "production_balance",
      label: "Saldo a produzir",
      value: formatQuantity(forecast.saldoNecessarioProducao),
    },
    { id: "open_value", label: "Valor aberto", value: formatCurrency(item.valor_aberto) },
    {
      id: "delay",
      label: "Atraso",
      value:
        overdueDays != null && item.saldo > 0
          ? `${overdueDays.toLocaleString("pt-BR")} dia(s)`
          : "No prazo",
    },
    {
      id: "dispatch",
      label: "Despacho",
      value: item.data_despacho ? formatDisplayDate(item.data_despacho) : "Não informado",
    },
    {
      id: "remaining_production",
      label: "Ainda falta produzir",
      value:
        forecast.kind === "parcial" && forecast.saldoFaltanteProducao > 0
          ? formatQuantity(forecast.saldoFaltanteProducao)
          : forecast.kind === "estoque" || forecast.kind === "coberto"
            ? "0 (estoque / OP cobre)"
            : forecast.saldoNecessarioProducao > 0
              ? formatQuantity(forecast.saldoNecessarioProducao)
              : "Não aplicável",
    },
  ] as const;
  const sections: OpenOrdersProductionDetailSection[] = [
    {
      id: "snapshot",
      label: "Resumo da linha",
      guideLabel: "Resumo",
      data: {
        lineStatus,
        coverageKind: forecast.kind,
        coveragePercent: coverage.percentLabel,
        deliveryDate: formatDisplayDate(item.data_entrega),
        forecastLabel: forecast.previsaoLabel,
      },
    },
    {
      id: "factory",
      label: "Situação fabril",
      guideLabel: "Fabril",
      data: {
        branch: item.filial,
        product: item.produto,
        productionOrder: selectedProductionOrder,
      },
    },
    {
      id: "metrics",
      label: "Indicadores da linha",
      guideLabel: "Indicadores",
      data: metrics,
    },
    {
      id: "coverage_deadline",
      label: "Cobertura e prazo",
      guideLabel: "Cobertura / prazo",
      data: { coverage, coverageChart, deadlineChart },
    },
    {
      id: "production_order",
      label: "Produção OP",
      guideLabel: "Produção OP",
      data: {
        selectedProductionOrder,
        operations: forecast.opsUtilizadas,
      },
    },
    {
      id: "product_structure",
      label: "Estrutura do produto",
      data: { productCode: item.produto },
    },
  ];

  return {
    selectedProductionOrder,
    forecast,
    lineStatus,
    coverage,
    deliveryDays,
    forecastDays,
    overdueDays,
    coverageChart,
    deadlineChart,
    metrics,
    sections,
  };
}
