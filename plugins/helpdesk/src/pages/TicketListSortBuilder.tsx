import { Plus, Trash2 } from "lucide-react";

import {
  formatTicketSortLevels,
  type TicketListSortLevel,
} from "../presentation/ticketListViewModel";
import { TICKET_LIST_SORTABLE_COLUMNS } from "../presentation/ticketView";
import { HelpdeskFilterSelect, HelpdeskFormActions, HelpdeskIconButton } from "../ui/helpdeskUi";
import { ActionButton } from "@delpi/plugin-ui/index";

const SORT_OPTIONS = TICKET_LIST_SORTABLE_COLUMNS.map((key) => ({
  value: key,
  label:
    key === "updated_at"
      ? "Última atualização"
      : key === "created_at"
        ? "Aberto"
        : key === "solved_at"
          ? "Resolvido"
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
  function updateLevel(index: number, patch: Partial<TicketListSortLevel>) {
    onChange(levels.map((level, i) => (i === index ? { ...level, ...patch } : level)));
  }

  return (
    <div className="helpdesk-sort-builder" aria-label="Ordenação da lista">
      <p className="helpdesk-sort-builder__hint">Até três níveis. O primeiro decide a grade; os demais vão no sort da URL.</p>
      <ul className="helpdesk-sort-builder__levels">
        {levels.map((level, index) => (
          <li key={`${level.field}-${index}`} className="helpdesk-sort-builder__level">
            <span className="helpdesk-sort-builder__ordinal" aria-hidden>
              {index + 1}
            </span>
            <HelpdeskFilterSelect
              label={`Nível ${index + 1}`}
              value={level.field}
              onChange={(field) =>
                updateLevel(index, { field: field as TicketListSortLevel["field"] })
              }
              options={SORT_OPTIONS}
            />
            <HelpdeskFilterSelect
              label="Direção"
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
              <HelpdeskIconButton
                aria-label={`Remover nível ${index + 1}`}
                onClick={() => onChange(levels.filter((_, i) => i !== index))}
              >
                <Trash2 size={14} aria-hidden />
              </HelpdeskIconButton>
            ) : null}
          </li>
        ))}
      </ul>
      <HelpdeskFormActions>
        {levels.length < 3 ? (
          <ActionButton
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
            <Plus size={14} aria-hidden /> Outra ordenação
          </ActionButton>
        ) : null}
        <ActionButton
          variant="primary"
          onClick={() => {
            onChange(levels);
            onApply();
          }}
        >
          Aplicar ({formatTicketSortLevels(levels)})
        </ActionButton>
      </HelpdeskFormActions>
    </div>
  );
}
