/** Filtros avançados do catálogo de produtos — painel ancorado no
 * padrão do kit (AnchoredPanelPortal, mesmo mecanismo do Helpdesk) com
 * critérios FIELD + OPERATOR + VALUE definidos em
 * `../productFilterRules`. O painel é um editor alternativo do MESMO
 * estado canônico da URL (quick filters incluídos) — draft local até
 * "Aplicar filtros" commitar atomicamente em `ProductsListUrlState`.
 * Nenhum critério filtra só a página carregada; tudo vai ao backend. */

import { useRef, useState } from "react";
import { ListFilter, Plus, X } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";

import {
  EngineeringActionButton,
  EngineeringFilterInput,
  EngineeringFilterSelect,
  EngineeringMultiSelectField,
} from "../../../ui/engineeringUi";
import type { ProductsListUrlState } from "../productRoutes";
import {
  FIELD_META,
  FIELD_ORDER,
  firstAvailableField,
  isValidRule,
  rulesFromListState,
  type ProductFilterField,
  type ProductFilterRule,
  type SelectOption,
} from "../productFilterRules";

export function ProductAdvancedFilters({
  applied,
  activeCount = 0,
  groupOptions,
  typeOptions,
  disabled = false,
  onApply,
}: {
  applied: ProductsListUrlState;
  /** Critérios efetivamente aplicados — indicador discreto no gatilho
   * (doc 67 §2.4: "indicador mostra filtros ativos"). */
  activeCount?: number;
  groupOptions: SelectOption[];
  typeOptions: SelectOption[];
  disabled?: boolean;
  onApply: (rules: ProductFilterRule[]) => void;
}) {
  const [open, setOpen] = useState(false);
  /* Draft separado do estado aplicado — editar critérios nunca dispara
   * consulta; só "Aplicar filtros" commita. Recebido do estado aplicado
   * ao abrir; fechar sem aplicar descarta o draft. */
  const [rules, setRules] = useState<ProductFilterRule[]>([]);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const toggleOpen = () => {
    if (!open) {
      setRules(rulesFromListState(applied));
    }
    setOpen((current) => !current);
  };

  const updateRule = (index: number, rule: ProductFilterRule) => {
    setRules((current) =>
      current.map((item, i) => (i === index ? rule : item)),
    );
  };

  const removeRule = (index: number) => {
    setRules((current) => current.filter((_, i) => i !== index));
  };

  const setRuleField = (index: number, field: ProductFilterField) => {
    updateRule(index, { field, text: "", values: [] });
  };

  const addRule = () => {
    setRules((current) => [
      ...current,
      { field: firstAvailableField(current), text: "", values: [] },
    ]);
  };

  const applyRules = () => {
    /* Critérios válidos: texto preenchido ou ao menos um valor. */
    onApply(rules.filter(isValidRule));
    setOpen(false);
  };

  const usedFields = new Set(rules.map((rule) => rule.field));
  const fieldOptions = (rule: ProductFilterRule) =>
    FIELD_ORDER.filter(
      (field) => field === rule.field || !usedFields.has(field),
    ).map((field) => ({ value: field, label: FIELD_META[field].label }));

  return (
    <div className="engineering-products__adv-filters" ref={wrapperRef}>
      <button
        type="button"
        className="engineering-products__adv-filters-trigger delpi-ui-table-toolbar-action"
        aria-label="Filtros avançados"
        aria-expanded={open}
        disabled={disabled}
        onClick={toggleOpen}
      >
        <ListFilter size={16} aria-hidden />
        Filtros
        {activeCount > 0 ? (
          <span
            className="engineering-products__adv-filters-count"
            aria-label={`${activeCount} filtro(s) aplicado(s)`}
          >
            {activeCount}
          </span>
        ) : null}
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="engineering-products__adv-panel delpi-ui-popover-surface"
        variant="bare"
        role="dialog"
        aria-label="Filtros avançados"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="engineering-products"
        onDismiss={() => setOpen(false)}
        density="compact"
      >
        <div className="engineering-products__adv-panel-header">
          <strong className="engineering-products__adv-panel-title">
            Filtros avançados
          </strong>
          <p className="engineering-products__adv-panel-hint">
            Refine os produtos combinando um ou mais critérios.
          </p>
        </div>
        <div className="engineering-products__adv-panel-body">
          {rules.length === 0 ? (
            <p className="engineering-products__adv-empty">
              Nenhum critério definido — adicione um critério para refinar
              a consulta oficial.
            </p>
          ) : null}
          <ul className="engineering-products__adv-rules">
            {rules.map((rule, index) => {
              const meta = FIELD_META[rule.field];
              return (
                <li
                  key={`${rule.field}-${index}`}
                  className="engineering-products__adv-rule"
                >
                  <div className="engineering-products__adv-rule-fields">
                    <EngineeringFilterSelect
                      label="Campo"
                      value={rule.field}
                      onChange={(value) =>
                        setRuleField(index, value as ProductFilterField)
                      }
                      options={fieldOptions(rule)}
                    />
                    <span
                      className="engineering-products__adv-operator"
                      aria-label={`Operador: ${meta.operator}`}
                    >
                      {meta.operator}
                    </span>
                    {meta.kind === "multi" ? (
                      <EngineeringMultiSelectField
                        label="Valores"
                        options={
                          rule.field === "groups"
                            ? groupOptions
                            : typeOptions
                        }
                        selectedValues={rule.values}
                        onChange={(values) =>
                          updateRule(index, { ...rule, values })
                        }
                        searchable
                        emptyLabel="Selecionar"
                      />
                    ) : (
                      <EngineeringFilterInput
                        label="Valor"
                        type="text"
                        value={rule.text}
                        onChange={(text) =>
                          updateRule(index, { ...rule, text })
                        }
                        placeholder={meta.placeholder}
                      />
                    )}
                  </div>
                  <button
                    type="button"
                    className="engineering-products__adv-rule-remove"
                    aria-label={`Remover critério ${meta.label}`}
                    onClick={() => removeRule(index)}
                  >
                    <X size={14} aria-hidden />
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="engineering-products__adv-actions">
            <EngineeringActionButton
              variant="ghost"
              onClick={addRule}
              disabled={rules.length >= FIELD_ORDER.length}
            >
              <Plus size={14} aria-hidden /> Adicionar critério
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              onClick={() => setRules([])}
              disabled={rules.length === 0}
            >
              Limpar
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="primary"
              onClick={applyRules}
            >
              Aplicar filtros
            </EngineeringActionButton>
          </div>
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
