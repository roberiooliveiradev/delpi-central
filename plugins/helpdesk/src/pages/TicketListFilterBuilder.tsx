import { Check, Eraser, Plus, Trash2 } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
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
  const help = helpTooltips.filterBuilder;

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
      <p className="helpdesk-filter-builder__hint">{help.panel}</p>
      <ul className="helpdesk-filter-builder__rules">
        {group.rules.map((rule) => {
          const meta =
            TICKET_LIST_BUILDER_FIELDS.find((item) => item.key === rule.field) ??
            TICKET_LIST_BUILDER_FIELDS[0];
          const operatorLabel =
            meta.operator === "contains"
              ? "contém"
              : meta.operator === "gte"
                ? "de"
                : meta.operator === "lte"
                  ? "até"
                  : "é";
          return (
            <li key={rule.id} className="helpdesk-filter-builder__rule" data-kind={meta.input}>
              <HelpdeskFilterSelect
                label="Campo"
                hint={help.field}
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
              <HintAction hint={help.operator} ariaLabel="Ajuda: operador">
                <span className="helpdesk-filter-builder__op">{operatorLabel}</span>
              </HintAction>
              {meta.input === "status" ? (
                <HelpdeskFilterSelect
                  label="Valor"
                  hint={help.value}
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                  options={[...TICKET_STATUS_FILTERS]}
                />
              ) : null}
              {meta.input === "urgency" ? (
                <HelpdeskFilterSelect
                  label="Valor"
                  hint={help.value}
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
                  hint={help.value}
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
                  hint={help.value}
                  type={meta.input === "date" ? "date" : "search"}
                  value={rule.value}
                  onChange={(value) => updateRule(rule.id, { value })}
                />
              ) : null}
              <span className="helpdesk-filter-builder__remove">
                <HintAction hint={help.removeRule} ariaLabel="Ajuda: Remover regra">
                  <HelpdeskIconButton aria-label="Remover regra" onClick={() => removeRule(rule.id)}>
                    <Trash2 size={14} aria-hidden />
                  </HelpdeskIconButton>
                </HintAction>
              </span>
            </li>
          );
        })}
      </ul>
      <HelpdeskFormActions>
        <HintAction hint={help.addRule} ariaLabel="Ajuda: Adicionar regra">
          <HelpdeskIconButton aria-label="Adicionar regra" onClick={addRule}>
            <Plus size={16} aria-hidden />
          </HelpdeskIconButton>
        </HintAction>
        <HintAction hint={help.clear} ariaLabel="Ajuda: Limpar regras">
          <HelpdeskIconButton aria-label="Limpar regras" onClick={onClear}>
            <Eraser size={16} aria-hidden />
          </HelpdeskIconButton>
        </HintAction>
        <HintAction hint={help.apply} ariaLabel="Ajuda: Aplicar filtros">
          <HelpdeskIconButton tone="primary" aria-label="Aplicar filtros" onClick={onApply}>
            <Check size={16} aria-hidden />
          </HelpdeskIconButton>
        </HintAction>
      </HelpdeskFormActions>
    </div>
  );
}
