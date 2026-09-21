import { Plus, Trash2 } from "lucide-react";

import {
  newFilterRuleId,
  TICKET_LIST_BUILDER_FIELDS,
  type TicketListFilterGroup,
  type TicketListFilterRule,
} from "../presentation/ticketListViewModel";
import { TICKET_STATUS_FILTERS } from "../presentation/ticketView";
import {
  HelpdeskFilterInput,
  HelpdeskFilterSelect,
  HelpdeskFormActions,
  HelpdeskIconButton,
} from "../ui/helpdeskUi";
import { ActionButton } from "@delpi/plugin-ui/index";

type CatalogOption = { id: number; name: string };

/**
 * Visual AND builder for solicitante filters.
 * Nested OR groups are typed in the model but not serialized to the flat BFF query yet.
 */
export function TicketListFilterBuilder({
  group,
  onChange,
  onApply,
  onClear,
  urgencies,
  categories,
}: {
  group: TicketListFilterGroup;
  onChange: (next: TicketListFilterGroup) => void;
  onApply: () => void;
  onClear: () => void;
  urgencies: CatalogOption[];
  categories: CatalogOption[];
}) {
  function updateRule(ruleId: string, patch: Partial<TicketListFilterRule>) {
    onChange({
      ...group,
      rules: group.rules.map((rule) => (rule.id === ruleId ? { ...rule, ...patch } : rule)),
    });
  }

  function removeRule(ruleId: string) {
    onChange({ ...group, rules: group.rules.filter((rule) => rule.id !== ruleId) });
  }

  function addRule() {
    const field = TICKET_LIST_BUILDER_FIELDS[0];
    onChange({
      ...group,
      rules: [
        ...group.rules,
        {
          id: newFilterRuleId(),
          field: field.key,
          operator: field.operator,
          value: "",
        },
      ],
    });
  }

  return (
    <div className="helpdesk-filter-builder" aria-label="Construtor de filtros">
      <p className="helpdesk-filter-builder__hint">
        Regras com E (AND). O recorte vai para a URL e sobrevive ao F5. Grupos OU ficam para uma
        evolução do contrato.
      </p>
      <ul className="helpdesk-filter-builder__rules">
        {group.rules.map((rule) => {
          const meta =
            TICKET_LIST_BUILDER_FIELDS.find((item) => item.key === rule.field) ??
            TICKET_LIST_BUILDER_FIELDS[0];
          return (
            <li key={rule.id} className="helpdesk-filter-builder__rule" data-kind={meta.input}>
              <HelpdeskFilterSelect
                label="Campo"
                value={rule.field}
                onChange={(field) => {
                  const nextMeta =
                    TICKET_LIST_BUILDER_FIELDS.find((item) => item.key === field) ?? meta;
                  updateRule(rule.id, {
                    field: nextMeta.key,
                    operator: nextMeta.operator,
                    value: "",
                  });
                }}
                options={TICKET_LIST_BUILDER_FIELDS.map((item) => ({
                  value: item.key,
                  label: item.label,
                }))}
              />
              <span className="helpdesk-filter-builder__op" aria-hidden>
                {meta.operator === "contains" ? "contém" : meta.operator === "gte" ? "de" : meta.operator === "lte" ? "até" : "é"}
              </span>
              {meta.input === "status" ? (
                <HelpdeskFilterSelect
                  label="Valor"
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                  options={[...TICKET_STATUS_FILTERS]}
                />
              ) : null}
              {meta.input === "urgency" ? (
                <HelpdeskFilterSelect
                  label="Valor"
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                  options={[
                    { value: "", label: "Todas" },
                    ...urgencies.map((item) => ({ value: String(item.id), label: item.name })),
                  ]}
                />
              ) : null}
              {meta.input === "category" ? (
                <HelpdeskFilterSelect
                  label="Valor"
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                  options={[
                    { value: "", label: "Todas" },
                    ...categories.map((item) => ({ value: String(item.id), label: item.name })),
                  ]}
                />
              ) : null}
              {meta.input === "text" || meta.input === "date" ? (
                <HelpdeskFilterInput
                  label="Valor"
                  type={meta.input === "date" ? "date" : "search"}
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                />
              ) : null}
              <HelpdeskIconButton
                aria-label="Remover regra"
                onClick={() => removeRule(rule.id)}
              >
                <Trash2 size={14} aria-hidden />
              </HelpdeskIconButton>
            </li>
          );
        })}
      </ul>
      <HelpdeskFormActions>
        <ActionButton onClick={addRule}>
          <Plus size={14} aria-hidden /> Regra
        </ActionButton>
        <ActionButton onClick={onClear}>Limpar</ActionButton>
        <ActionButton variant="primary" onClick={onApply}>
          Aplicar
        </ActionButton>
      </HelpdeskFormActions>
    </div>
  );
}
