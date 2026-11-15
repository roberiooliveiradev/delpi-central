import { createDashboardSortLevelsBuilder } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import { type TicketListSortLevel } from "../presentation/ticketListViewModel";
import { TICKET_LIST_SORTABLE_COLUMNS } from "../presentation/ticketView";

const SORT_OPTIONS = TICKET_LIST_SORTABLE_COLUMNS.map((key) => ({
  value: key,
  label:
    key === "updated_at"
      ? "Última atualização"
      : key === "created_at"
        ? "Aberto"
        : key === "solved_at"
          ? "Resolvido"
          : key === "closed_at"
            ? "Fechado"
            : key === "title"
            ? "Título"
            : key === "status"
              ? "Status"
              : key === "category"
                ? "Categoria"
                : key === "urgency"
                  ? "Urgência"
                  : key === "assigned"
                    ? "Técnico"
                    : key === "requester"
                      ? "Requerente"
                      : key === "id"
                        ? "Chamado"
                        : key,
}));

const help = helpTooltips.sortBuilder;

/** Ordenação multinível — mecânica do kit; catálogo/labels do domínio. */
const SortLevelsBuilder = createDashboardSortLevelsBuilder({
  prefix: "helpdesk",
  portalScopeClassName: "dashboard-helpdesk",
  labels: {
    ariaLabel: "Ordenação da lista",
    fieldHint: help.field,
    directionLabel: "Direção",
    directionHint: help.direction,
    levelHint: help.panel,
    levelAriaLabel: (level) => `Nível ${level}`,
    removeLevelHint: help.removeLevel,
    removeLevelAriaLabel: (level) => `Remover nível ${level}`,
    addLevelHint: help.addLevel,
    addLevelLabel: "Outro nível",
    addLevelAriaLabel: "Outra ordenação",
    applyHint: help.apply,
    applyLabel: "Aplicar",
    applyAriaLabel: "Aplicar ordenação",
    directionAscLabel: "Ascendente",
    directionDescLabel: "Descendente",
  },
});

export function TicketListSortBuilder({
  levels,
  onChange,
  onApply,
}: {
  levels: TicketListSortLevel[];
  onChange: (next: TicketListSortLevel[]) => void;
  onApply: () => void;
}) {
  return (
    <SortLevelsBuilder
      levels={levels}
      options={SORT_OPTIONS}
      onChange={(next) =>
        onChange(next.map((level) => ({
          field: level.field as TicketListSortLevel["field"],
          direction: level.direction,
        })))
      }
      onApply={onApply}
    />
  );
}
