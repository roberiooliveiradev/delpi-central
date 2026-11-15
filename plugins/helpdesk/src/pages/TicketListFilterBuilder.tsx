import { Eraser } from "lucide-react";
import {
  createDashboardFilterRulesBuilder,
  type DashboardFilterFieldDescriptor,
  type DashboardFilterRule,
} from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import {
  TICKET_LIST_BUILDER_FIELDS,
  type ListFilterOperator,
  type TicketListFilterFieldKey,
  type TicketListFilterGroup,
  type TicketListFilterRule,
} from "../presentation/ticketListViewModel";
import { TICKET_STATUS_FILTERS } from "../presentation/ticketView";

type CatalogOption = { id: number; name: string };

const help = helpTooltips.filterBuilder;

/** Builder de critérios AND — mecânica do kit; catálogo/labels do domínio. */
const FilterRulesBuilder = createDashboardFilterRulesBuilder({
  prefix: "helpdesk",
  portalScopeClassName: "dashboard-helpdesk",
  labels: {
    ariaLabel: "Construtor de filtros",
    fieldLabel: "Campo",
    fieldHint: help.field,
    operatorHint: help.operator,
    valueLabel: "Valor",
    valueHint: help.value,
    removeRuleHint: help.removeRule,
    removeRuleAriaLabel: "Remover regra",
    addRuleHint: help.addRule,
    addRuleLabel: "Adicionar critério",
    addRuleAriaLabel: "Adicionar critério",
    clearHint: help.clear,
    clearLabel: (
      <>
        <Eraser size={16} aria-hidden />
        Limpar
      </>
    ),
    clearAriaLabel: "Limpar",
    applyHint: help.apply,
    applyLabel: "Aplicar filtros",
    applyAriaLabel: "Aplicar filtros",
  },
});

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
  assignees,
  requesters,
}: {
  group: TicketListFilterGroup;
  onChange: (next: TicketListFilterGroup) => void;
  onApply: () => void;
  onClear: () => void;
  urgencies: CatalogOption[];
  categories: CatalogOption[];
  assignees: CatalogOption[];
  requesters: CatalogOption[];
}) {
  const fields: DashboardFilterFieldDescriptor[] = TICKET_LIST_BUILDER_FIELDS.map(
    (meta) => {
      const base = {
        key: meta.key,
        label: meta.label,
        operator: meta.operator,
      };
      if (meta.input === "status") {
        return {
          ...base,
          input: "select" as const,
          searchable: true,
          options: [...TICKET_STATUS_FILTERS],
        };
      }
      if (meta.input === "urgency") {
        return {
          ...base,
          input: "select" as const,
          searchable: true,
          placeholderOption: "Todas",
          options: urgencies.map((item) => ({
            value: String(item.id),
            label: item.name,
          })),
        };
      }
      if (meta.input === "category") {
        return {
          ...base,
          input: "select" as const,
          searchable: true,
          placeholderOption: "Todas",
          options: categories.map((item) => ({
            value: String(item.id),
            label: item.name,
          })),
        };
      }
      if (meta.input === "assignee") {
        return {
          ...base,
          input: "select" as const,
          searchable: true,
          placeholderOption: "Todos",
          options: assignees.map((item) => ({
            value: String(item.id),
            label: item.name,
          })),
        };
      }
      if (meta.input === "requester") {
        return {
          ...base,
          input: "select" as const,
          searchable: true,
          placeholderOption: "Todos",
          options: requesters.map((item) => ({
            value: String(item.id),
            label: item.name,
          })),
        };
      }
      if (meta.input === "mine") {
        return {
          ...base,
          input: "select" as const,
          defaultValue: "1",
          options: [
            { value: "1", label: "Somente os meus" },
            { value: "0", label: "Todos os visíveis" },
          ],
        };
      }
      if (meta.input === "date") {
        return { ...base, input: "date" as const };
      }
      return { ...base, input: "text" as const };
    },
  );

  /* O critério "mine" guarda "1"/"" no modelo e exibe "1"/"0" no select. */
  const toUiRules = (): DashboardFilterRule[] =>
    group.rules.map((rule) => {
      const meta = TICKET_LIST_BUILDER_FIELDS.find(
        (item) => item.key === rule.field,
      );
      if (meta?.input === "mine") {
        return { ...rule, value: rule.value === "1" ? "1" : "0" };
      }
      return rule;
    });

  const handleChange = (next: DashboardFilterRule[]) =>
    onChange({
      ...group,
      rules: next.map((rule): TicketListFilterRule => {
        const typed: TicketListFilterRule = {
          ...rule,
          field: rule.field as TicketListFilterFieldKey,
          operator: rule.operator as ListFilterOperator,
        };
        const meta = TICKET_LIST_BUILDER_FIELDS.find(
          (item) => item.key === rule.field,
        );
        if (meta?.input === "mine") {
          return { ...typed, value: rule.value === "1" ? "1" : "" };
        }
        return typed;
      }),
    });

  return (
    <FilterRulesBuilder
      rules={toUiRules()}
      fields={fields}
      onChange={handleChange}
      onApply={onApply}
      onClear={onClear}
    />
  );
}
