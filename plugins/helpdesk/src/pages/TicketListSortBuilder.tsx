import { Check, Plus, Trash2 } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import {
  type TicketListSortLevel,
} from "../presentation/ticketListViewModel";
import { TICKET_LIST_SORTABLE_COLUMNS } from "../presentation/ticketView";
import { HelpdeskFilterSelect, HelpdeskIconButton } from "../ui/helpdeskUi";

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
                  : key === "id"
                    ? "Chamado"
                    : key,
}));

export function TicketListSortBuilder({
  levels,
  onChange,
  onApply,
}: {
  levels: TicketListSortLevel[];
  onChange: (next: TicketListSortLevel[]) => void;
  onApply: () => void;
}) {
  const help = helpTooltips.sortBuilder;

  function updateLevel(index: number, patch: Partial<TicketListSortLevel>) {
    onChange(levels.map((level, i) => (i === index ? { ...level, ...patch } : level)));
  }

  return (
    <div className="helpdesk-sort-builder" aria-label="Ordenação da lista">
      <p className="helpdesk-sort-builder__hint">{help.panel}</p>
      <ul className="helpdesk-sort-builder__levels">
        {levels.map((level, index) => (
          <li key={`${level.field}-${index}`} className="helpdesk-sort-builder__level">
            <HintAction hint={help.panel} ariaLabel={`Ajuda: nível ${index + 1}`}>
              <span className="helpdesk-sort-builder__ordinal" aria-hidden>
                {index + 1}
              </span>
            </HintAction>
            <HelpdeskFilterSelect
              label={`Nível ${index + 1}`}
              hint={help.field}
              value={level.field}
              onChange={(field) =>
                updateLevel(index, { field: field as TicketListSortLevel["field"] })
              }
              options={SORT_OPTIONS}
            />
            <HelpdeskFilterSelect
              label="Direção"
              hint={help.direction}
              value={level.direction}
              onChange={(direction) =>
                updateLevel(index, { direction: direction === "asc" ? "asc" : "desc" })
              }
              options={[
                { value: "desc", label: "Descendente" },
                { value: "asc", label: "Ascendente" },
              ]}
            />
            {levels.length > 1 ? (
              <span className="helpdesk-sort-builder__remove">
                <HintAction hint={help.removeLevel} ariaLabel={`Ajuda: Remover nível ${index + 1}`}>
                  <HelpdeskIconButton
                    aria-label={`Remover nível ${index + 1}`}
                    onClick={() => onChange(levels.filter((_, i) => i !== index))}
                  >
                    <Trash2 size={14} aria-hidden />
                  </HelpdeskIconButton>
                </HintAction>
              </span>
            ) : null}
          </li>
        ))}
      </ul>
      <div className="helpdesk-sort-builder__actions">
        {levels.length < 3 ? (
          <HintAction hint={help.addLevel} ariaLabel="Ajuda: Outra ordenação">
            <HelpdeskIconButton
              aria-label="Outra ordenação"
              onClick={() =>
                onChange([
                  ...levels,
                  {
                    field: SORT_OPTIONS.find((option) => !levels.some((l) => l.field === option.value))
                      ?.value as TicketListSortLevel["field"],
                    direction: "asc",
                  },
                ])
              }
            >
              <Plus size={16} aria-hidden />
            </HelpdeskIconButton>
          </HintAction>
        ) : null}
        <HintAction hint={help.apply} ariaLabel="Ajuda: Aplicar ordenação">
          <HelpdeskIconButton
            tone="primary"
            aria-label="Aplicar ordenação"
            onClick={() => {
              onChange(levels);
              onApply();
            }}
          >
            <Check size={16} aria-hidden />
          </HelpdeskIconButton>
        </HintAction>
      </div>
    </div>
  );
}
