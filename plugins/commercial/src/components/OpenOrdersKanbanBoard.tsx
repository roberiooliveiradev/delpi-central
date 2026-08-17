import { useEffect } from "react";

import {
  CommercialEmptyState,
  CommercialInteractiveDataCard,
  CommercialKanbanBoard,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import { customerAvatarKey } from "../hooks/useOpenOrdersCustomerAvatars";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { formatCurrency } from "../utils/format";
import { formatDisplayDate } from "../utils/dates";
import { OpenOrdersLineCard } from "./OpenOrdersLineCard";
import type { TableColumnKey } from "../utils/tableColumns";

export type OpenOrderKanbanStageId =
  | "upcoming"
  | "in_progress"
  | "ready_to_invoice"
  | "completed";

const OPEN_STAGES: OpenOrderKanbanStageId[] = [
  "upcoming",
  "in_progress",
  "ready_to_invoice",
];

const STAGE_TITLE: Record<OpenOrderKanbanStageId, string> = {
  upcoming: "Próximos",
  in_progress: "Em andamento",
  ready_to_invoice: "Pronto para faturar",
  completed: "Concluídos",
};

const STAGE_HELP: Record<OpenOrderKanbanStageId, string> = {
  upcoming: CM_HELP.openOrders.kanbanUpcoming,
  in_progress: CM_HELP.openOrders.kanbanInProgress,
  ready_to_invoice: CM_HELP.openOrders.kanbanReadyToInvoice,
  completed: CM_HELP.openOrders.kanbanCompleted,
};

export function resolveItemKanbanStage(item: OpenOrdersTotvsItem): OpenOrderKanbanStageId {
  const raw = item.kanbanStage;
  if (raw === "upcoming" || raw === "in_progress" || raw === "ready_to_invoice") {
    return raw;
  }
  return "upcoming";
}

type OpenOrdersKanbanBoardProps = {
  rows: OpenOrdersTotvsItem[];
  /** Completed column cards (recently closed via BFF). */
  completedRows?: OpenOrdersTotvsItem[];
  visibleColumns: ReadonlyArray<{ key: TableColumnKey; label: string }>;
  customerAvatarKeys?: ReadonlySet<string>;
  basePath?: string;
  onOpenDetail: (item: OpenOrdersTotvsItem) => void;
  /** Optional focus column id (deep link). */
  focusStage?: OpenOrderKanbanStageId | null;
};

function hasAvatarForItem(
  item: OpenOrdersTotvsItem,
  customerAvatarKeys?: ReadonlySet<string>,
): boolean {
  const code = item.codigo_cadastro?.trim() ?? "";
  const store = item.loja_cadastro?.trim() ?? "";
  if (!code || !store || !customerAvatarKeys) return false;
  return customerAvatarKeys.has(customerAvatarKey(code, store));
}

/**
 * Read-only Kanban for open orders — groups by BFF ``kanbanStage``.
 */
export function OpenOrdersKanbanBoardView({
  rows,
  completedRows = [],
  visibleColumns,
  customerAvatarKeys,
  basePath,
  onOpenDetail,
  focusStage = null,
}: OpenOrdersKanbanBoardProps) {
  useEffect(() => {
    if (!focusStage || typeof document === "undefined") return;
    const el = document.querySelector(`[data-kanban-column="${focusStage}"]`);
    if (el instanceof HTMLElement) {
      el.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [focusStage, rows.length, completedRows.length]);
  const byStage = new Map<OpenOrderKanbanStageId, OpenOrdersTotvsItem[]>();
  for (const stage of OPEN_STAGES) byStage.set(stage, []);
  for (const row of rows) {
    const stage = resolveItemKanbanStage(row);
    byStage.get(stage)?.push(row);
  }

  const columns = [
    ...OPEN_STAGES.map((stage) => {
      const items = byStage.get(stage) ?? [];
      const openValue = items.reduce((sum, item) => sum + (item.valor_aberto || 0), 0);
      return {
        id: stage,
        title: STAGE_TITLE[stage],
        count: items.length,
        summary: formatCurrency(openValue),
        empty: (
          <CommercialEmptyState
            title={STAGE_TITLE[stage]}
            message={STAGE_HELP[stage]}
          />
        ),
        children:
          items.length > 0
            ? items.map((item) => (
                <OpenOrdersLineCard
                  key={`${item.filial}-${item.pedido}-${item.linha}`}
                  item={item}
                  visibleColumns={visibleColumns}
                  hasAvatar={hasAvatarForItem(item, customerAvatarKeys)}
                  basePath={basePath}
                  onOpenDetail={onOpenDetail}
                />
              ))
            : undefined,
      };
    }),
    {
      id: "completed" as const,
      title: STAGE_TITLE.completed,
      count: completedRows.length,
      summary:
        completedRows.length > 0
          ? formatCurrency(
              completedRows.reduce((sum, item) => sum + (item.valor_aberto || 0), 0),
            )
          : undefined,
      empty: (
        <CommercialEmptyState
          title={STAGE_TITLE.completed}
          message={STAGE_HELP.completed}
        />
      ),
      children:
        completedRows.length > 0
          ? completedRows.map((item) => (
              <CommercialInteractiveDataCard
                key={`done-${item.filial}-${item.pedido}-${item.linha}`}
                ariaLabel={`Pedido ${item.pedido} linha ${item.linha}`}
                onActivate={() => onOpenDetail(item)}
                fields={[
                  {
                    id: "cliente",
                    label: "Cliente",
                    value: item.nome_cliente || "—",
                    valueTone: "title",
                  },
                  {
                    id: "pedido",
                    label: "Pedido",
                    value: `${item.pedido} / ${item.linha}`,
                    valueTone: "meta",
                  },
                  {
                    id: "entrega",
                    label: "Entrega",
                    value: formatDisplayDate(item.data_entrega),
                    valueTone: "meta",
                  },
                  {
                    id: "valor",
                    label: "Valor",
                    value: formatCurrency(item.valor_aberto),
                    valueTone: "value",
                  },
                ]}
              />
            ))
          : undefined,
    },
  ];

  return (
    <div
      data-kanban-focus={focusStage ?? undefined}
      title={CM_HELP.openOrders.kanbanBoard}
    >
      <CommercialKanbanBoard
        ariaLabel="Pedidos por etapa"
        columns={columns}
      />
    </div>
  );
}
