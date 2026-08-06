import type { OpsAbertaDetalhe, OpsAbertasData } from "../types/opsAbertas";
import type { LineOpPrevisao, OpAllocationEntry } from "../types/opPrevisao";
import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { compareDeliveryDates, formatDisplayDate } from "./dates";
import {
  isNegligibleQuantity,
  isQuantityNeedSatisfied,
  roundQuantity,
} from "./quantityMath";
import {
  buildLineKey,
  buildStockGroupKey,
  getAllocatedStock,
} from "./stockAllocation";

export type {
  LineOpPrevisao,
  LineOpPrevisaoKind,
  OpAllocationEntry,
} from "../types/opPrevisao";

export type OpsProductGroup = {
  detalhes: OpsAbertaDetalhe[];
};

export type OpsProductIndex = Map<string, OpsProductGroup>;

type OpPoolEntry = {
  op: OpsAbertaDetalhe;
  remaining: number;
};

export function buildOpsProductKey(filial: string, produto: string): string {
  return `${filial.trim()}::${produto.trim()}`;
}

export function buildOpsProductIndex(data: OpsAbertasData | null | undefined): OpsProductIndex {
  const index: OpsProductIndex = new Map();

  if (!data) {
    return index;
  }

  for (const detalhe of data.items) {
    const key = buildOpsProductKey(detalhe.filial, detalhe.produto);
    const current = index.get(key) ?? { detalhes: [] };
    current.detalhes.push(detalhe);
    index.set(key, current);
  }

  for (const group of index.values()) {
    group.detalhes.sort((left, right) =>
      compareOpsByForecastDate(left.data_fim_prevista_op, right.data_fim_prevista_op),
    );
  }

  return index;
}

function compareOpsByForecastDate(left: string | null, right: string | null): number {
  if (!left && !right) return 0;
  if (!left) return 1;
  if (!right) return -1;
  return compareDeliveryDates(left, right);
}

function compareLinesForAllocation(
  a: PedidosVendaAbertosItem,
  b: PedidosVendaAbertosItem,
): number {
  const byDelivery = compareDeliveryDates(a.data_entrega, b.data_entrega);
  if (byDelivery !== 0) return byDelivery;

  const byPedido = (a.pedido ?? "").localeCompare(b.pedido ?? "", "pt-BR");
  if (byPedido !== 0) return byPedido;

  return (a.linha ?? "").localeCompare(b.linha ?? "", "pt-BR", { numeric: true });
}

function buildOpPool(detalhes: OpsAbertaDetalhe[]): OpPoolEntry[] {
  return [...detalhes]
    .sort((left, right) =>
      compareOpsByForecastDate(left.data_fim_prevista_op, right.data_fim_prevista_op),
    )
    .map((op) => ({
      op,
      remaining: roundQuantity(Math.max(0, op.saldo_op ?? 0)),
    }));
}

function buildEstoquePrevisao(saldoNecessarioProducao: number): LineOpPrevisao {
  return {
    kind: "estoque",
    saldoNecessarioProducao,
    saldoCobertoPorOp: 0,
    saldoFaltanteProducao: 0,
    previsaoData: null,
    previsaoLabel: "—",
    opsUtilizadas: [],
  };
}

function allocateLineFromPool(
  need: number,
  pool: OpPoolEntry[],
): { previsao: LineOpPrevisao; remainingNeed: number } {
  const opsUtilizadas: OpAllocationEntry[] = [];
  let remainingNeed = roundQuantity(need);
  let previsaoData: string | null = null;
  let completingOpHadDate = true;

  for (const entry of pool) {
    if (isQuantityNeedSatisfied(remainingNeed)) {
      remainingNeed = 0;
      break;
    }

    entry.remaining = roundQuantity(entry.remaining);
    if (entry.remaining <= 0) continue;

    const allocated = roundQuantity(Math.min(entry.remaining, remainingNeed));
    if (isNegligibleQuantity(allocated)) continue;

    entry.remaining = roundQuantity(entry.remaining - allocated);
    remainingNeed = roundQuantity(remainingNeed - allocated);

    opsUtilizadas.push({
      numero_op: entry.op.numero_op?.trim() || "—",
      saldo_op_total: roundQuantity(entry.op.saldo_op ?? 0),
      saldo_alocado: allocated,
      data_fim_prevista_op: entry.op.data_fim_prevista_op,
      observacao_op: entry.op.observacao_op?.trim() ?? "",
    });

    if (isQuantityNeedSatisfied(remainingNeed)) {
      remainingNeed = 0;
      previsaoData = entry.op.data_fim_prevista_op;
      completingOpHadDate = Boolean(entry.op.data_fim_prevista_op);
      break;
    }
  }

  const saldoCobertoPorOp = roundQuantity(need - remainingNeed);

  if (opsUtilizadas.length === 0) {
    return {
      remainingNeed,
      previsao: {
        kind: "sem_op",
        saldoNecessarioProducao: need,
        saldoCobertoPorOp: 0,
        saldoFaltanteProducao: need,
        previsaoData: null,
        previsaoLabel: "Sem OP aberta",
        opsUtilizadas: [],
      },
    };
  }

  if (!isQuantityNeedSatisfied(remainingNeed)) {
    return {
      remainingNeed: roundQuantity(remainingNeed),
      previsao: {
        kind: "parcial",
        saldoNecessarioProducao: need,
        saldoCobertoPorOp,
        saldoFaltanteProducao: roundQuantity(remainingNeed),
        previsaoData: null,
        previsaoLabel: "Produção insuficiente",
        opsUtilizadas,
      },
    };
  }

  if (!previsaoData || !completingOpHadDate) {
    return {
      remainingNeed: 0,
      previsao: {
        kind: "sem_data",
        saldoNecessarioProducao: need,
        saldoCobertoPorOp,
        saldoFaltanteProducao: 0,
        previsaoData: null,
        previsaoLabel: "OP sem data prevista",
        opsUtilizadas,
      },
    };
  }

  return {
    remainingNeed: 0,
    previsao: {
      kind: "coberto",
      saldoNecessarioProducao: need,
      saldoCobertoPorOp,
      saldoFaltanteProducao: 0,
      previsaoData,
      previsaoLabel: formatDisplayDate(previsaoData),
      opsUtilizadas,
    },
  };
}

/**
 * Aloca saldo de OPs abertas por produto/filial entre linhas de pedido (FIFO por data de entrega),
 * após a alocação de estoque. A previsão é a data da OP que completa o saldo faltante da linha.
 */
export function allocateOpsToOrders(
  items: PedidosVendaAbertosItem[],
  opsIndex: OpsProductIndex,
): PedidosVendaAbertosItem[] {
  if (items.length === 0) return [];

  const groups = new Map<string, PedidosVendaAbertosItem[]>();
  for (const item of items) {
    const key = buildStockGroupKey(item);
    const bucket = groups.get(key);
    if (bucket) bucket.push(item);
    else groups.set(key, [item]);
  }

  const previsaoByLine = new Map<string, LineOpPrevisao>();

  for (const [groupKey, groupItems] of groups) {
    const pool = buildOpPool(opsIndex.get(groupKey)?.detalhes ?? []);
    const sorted = [...groupItems].sort(compareLinesForAllocation);

    for (const item of sorted) {
      const saldo = roundQuantity(Math.max(0, item.saldo ?? 0));
      const estoqueAlocado = roundQuantity(getAllocatedStock(item));
      const need = roundQuantity(Math.max(0, saldo - estoqueAlocado));

      if (need <= 0) {
        previsaoByLine.set(buildLineKey(item), buildEstoquePrevisao(0));
        continue;
      }

      const { previsao } = allocateLineFromPool(need, pool);
      previsaoByLine.set(buildLineKey(item), previsao);
    }
  }

  return items.map((item) => ({
    ...item,
    previsao_op: previsaoByLine.get(buildLineKey(item)) ?? buildEstoquePrevisao(0),
  }));
}

export function getLineOpPrevisao(item: PedidosVendaAbertosItem): LineOpPrevisao {
  return (
    item.previsao_op ?? {
      kind: "estoque",
      saldoNecessarioProducao: 0,
      saldoCobertoPorOp: 0,
      saldoFaltanteProducao: 0,
      previsaoData: null,
      previsaoLabel: "—",
      opsUtilizadas: [],
    }
  );
}

export function canOpenOpPrevisaoModal(item: PedidosVendaAbertosItem): boolean {
  const previsao = getLineOpPrevisao(item);
  return previsao.opsUtilizadas.length > 0;
}
