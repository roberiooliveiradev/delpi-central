/**
 * Ferramentas de listagem — mecânicas visuais neutras compartilhadas
 * entre MFEs (extraídas do padrão Helpdesk):
 *
 * - `createDashboardToolbarPopover`: gatilho + painel ancorado via
 *   `AnchoredPanelPortal` (portal no body, flip/clamp, Escape, clique
 *   externo, escopo de tema). O corpo é render-prop que recebe `close`.
 * - `createDashboardSortLevelsBuilder`: editor de ordenação multinível
 *   (até `maxLevels` níveis, campo único por nível, direção, remover,
 *   adicionar, aplicar). Não executa sort — devolve níveis tipados.
 * - `createDashboardFilterRulesBuilder`: editor de critérios AND —
 *   catálogo de campos tipados (select/text/date), operador por campo,
 *   valor, remover, adicionar, aplicar e limpar.
 *
 * Os componentes não conhecem entidades de domínio (ticket, request,
 * GLPI, APIs): o MFE injeta catálogos e serializa para seu contrato.
 *
 * CSS: `styles/dashboard-list-tools.css` (`delpi-ui-list-tools-*`,
 * `delpi-ui-sort-builder*`, `delpi-ui-filter-builder*`).
 */

import { Check, Plus, Trash2 } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";
import { IconButton } from "../actions/IconButton";
import { HintAction } from "../help/HintAction";
import {
  FilterInputField,
  FilterSelectField,
  filtersRowBemClasses,
} from "../layout/FiltersRow";
import {
  selectControlBemClasses,
  type SelectControlClassNames,
} from "../forms/SelectField";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

/* ------------------------------------------------------------------ */
/* Tipos públicos                                                      */
/* ------------------------------------------------------------------ */

export type DashboardSortDirection = "asc" | "desc";

export type DashboardSortLevel = {
  field: string;
  direction: DashboardSortDirection;
};

export type DashboardSortFieldOption = {
  value: string;
  label: string;
};

export type DashboardFilterRule = {
  id: string;
  field: string;
  operator: string;
  value: string;
};

/** Entrada do valor do critério. `select` usa `options`; `text`/`date`
 * usam input nativo. Operadores adicionais ficam no contrato do MFE. */
export type DashboardFilterFieldDescriptor = {
  key: string;
  label: string;
  /** Operador semântico serializado no critério (ex.: eq, contains). */
  operator: string;
  /** Rótulo do operador exibido (sobrescreve `operatorLabels`). */
  operatorLabel?: string;
  input: "select" | "text" | "date";
  /** Opções do valor quando `input === "select"`. */
  options?: readonly { value: string; label: string }[];
  /** Rótulo da opção vazia (ex.: "Todos"); habilita limpar a seleção. */
  placeholderOption?: string;
  searchable?: boolean;
  /** Valor inicial ao adicionar um critério deste campo. */
  defaultValue?: string;
};

/* ------------------------------------------------------------------ */
/* Popover ancorado de toolbar                                         */
/* ------------------------------------------------------------------ */

export type DashboardToolbarPopoverLabels = {
  /** aria-label padrão do painel quando `panelAriaLabel` não vier. */
  panelAriaLabel?: string;
};

export type DashboardToolbarPopoverProps = {
  /** Texto visível do gatilho (ex.: "Filtros", "Ordenar"). */
  label: ReactNode;
  /** Ícone do gatilho (Lucide, aria-hidden). */
  icon?: ReactNode;
  /** aria-label do gatilho (sobrescreve `label` quando diverge). */
  ariaLabel?: string;
  panelAriaLabel?: string;
  panelTitle?: string;
  panelHint?: string;
  /** Painel largo (builder de critérios) vs. padrão compacto. */
  wide?: boolean;
  /** Corpo do painel — recebe `close()` para fechar após aplicar. */
  children: (close: () => void) => ReactNode;
};

export function createDashboardToolbarPopover(config: {
  prefix: string;
  portalScopeClassName?: string;
}) {
  const portalScope = config.portalScopeClassName;
  void config.prefix;

  function DashboardToolbarPopover({
    label,
    icon,
    ariaLabel,
    panelAriaLabel,
    panelTitle,
    panelHint,
    wide = false,
    children,
  }: DashboardToolbarPopoverProps) {
    const [open, setOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);
    const close = () => setOpen(false);

    return (
      <div
        className={`delpi-ui-list-tools-popover${wide ? " delpi-ui-list-tools-popover--wide" : ""}`}
        ref={wrapperRef}
      >
        <button
          type="button"
          className="delpi-ui-list-tools-popover__trigger delpi-ui-table-toolbar-action"
          aria-label={ariaLabel ?? (typeof label === "string" ? label : undefined)}
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
        >
          {icon}
          {label}
        </button>
        <AnchoredPanelPortal
          open={open}
          anchorRef={wrapperRef}
          panelRef={panelRef}
          className={`delpi-ui-list-tools-popover__panel${wide ? " delpi-ui-list-tools-popover__panel--wide" : ""}`}
          variant="bare"
          role="dialog"
          aria-label={panelAriaLabel ?? panelTitle ?? ariaLabel}
          preferredPlacement="bottom"
          horizontalAlign="end"
          gap={6}
          portalScopeClassName={portalScope}
          onDismiss={close}
        >
          {panelTitle || panelHint ? (
            <div className="delpi-ui-list-tools-popover__header">
              {panelTitle ? (
                <strong className="delpi-ui-list-tools-popover__title">
                  {panelTitle}
                </strong>
              ) : null}
              {panelHint ? (
                <p className="delpi-ui-list-tools-popover__hint">{panelHint}</p>
              ) : null}
            </div>
          ) : null}
          <div className="delpi-ui-list-tools-popover__body">
            {children(close)}
          </div>
        </AnchoredPanelPortal>
      </div>
    );
  }

  return DashboardToolbarPopover;
}

/* ------------------------------------------------------------------ */
/* Builder de ordenação multinível                                     */
/* ------------------------------------------------------------------ */

export type DashboardSortLevelsBuilderLabels = {
  ariaLabel: string;
  fieldHint: string;
  directionLabel: string;
  directionHint: string;
  levelHint: string;
  levelAriaLabel: (level: number) => string;
  removeLevelHint: string;
  removeLevelAriaLabel: (level: number) => string;
  addLevelHint: string;
  addLevelLabel: ReactNode;
  addLevelAriaLabel: string;
  applyHint: string;
  applyLabel: ReactNode;
  applyAriaLabel: string;
  directionAscLabel: string;
  directionDescLabel: string;
};

export type DashboardSortLevelsBuilderProps = {
  levels: DashboardSortLevel[];
  options: readonly DashboardSortFieldOption[];
  onChange: (next: DashboardSortLevel[]) => void;
  onApply: () => void;
  /** Teto de níveis (padrão 3 — paridade Helpdesk). */
  maxLevels?: number;
};

export function createDashboardSortLevelsBuilder(config: {
  prefix: string;
  labels: DashboardSortLevelsBuilderLabels;
  portalScopeClassName?: string;
}) {
  const prefix = config.prefix;
  const labels = config.labels;
  const classNames = filtersRowBemClasses(prefix);
  const selectClassNames: SelectControlClassNames =
    selectControlBemClasses(prefix);
  const portalScope = config.portalScopeClassName;

  function SortLevelsSelect(props: {
    label: string;
    hint: string;
    value: string;
    options: readonly { value: string; label: string }[];
    onChange: (value: string) => void;
    searchable?: boolean;
  }) {
    return (
      <FilterSelectField
        label={props.label}
        hint={props.hint}
        value={props.value}
        onChange={props.onChange}
        options={props.options as { value: string; label: string }[]}
        searchable={props.searchable}
        classNames={classNames}
        selectClassNames={selectClassNames}
        portalScopeClassName={portalScope}
      />
    );
  }

  function DashboardSortLevelsBuilder({
    levels,
    options,
    onChange,
    onApply,
    maxLevels = 3,
  }: DashboardSortLevelsBuilderProps) {
    function updateLevel(index: number, patch: Partial<DashboardSortLevel>) {
      onChange(
        levels.map((level, i) => (i === index ? { ...level, ...patch } : level)),
      );
    }

    return (
      <div className="delpi-ui-sort-builder" aria-label={labels.ariaLabel}>
        <ul className="delpi-ui-sort-builder__levels">
          {levels.map((level, index) => (
            <li
              key={`${level.field}-${index}`}
              className="delpi-ui-sort-builder__level"
            >
              <HintAction
                hint={labels.levelHint}
                ariaLabel={labels.levelAriaLabel(index + 1)}
              >
                <span
                  className="delpi-ui-sort-builder__ordinal"
                  aria-hidden
                >
                  {index + 1}
                </span>
              </HintAction>
              <SortLevelsSelect
                label={labels.levelAriaLabel(index + 1)}
                hint={labels.fieldHint}
                value={level.field}
                searchable
                onChange={(field) => updateLevel(index, { field })}
                options={options}
              />
              <SortLevelsSelect
                label={labels.directionLabel}
                hint={labels.directionHint}
                value={level.direction}
                onChange={(direction) =>
                  updateLevel(index, {
                    direction: direction === "asc" ? "asc" : "desc",
                  })
                }
                options={[
                  { value: "desc", label: labels.directionDescLabel },
                  { value: "asc", label: labels.directionAscLabel },
                ]}
              />
              {levels.length > 1 ? (
                <span className="delpi-ui-sort-builder__remove">
                  <HintAction
                    hint={labels.removeLevelHint}
                    ariaLabel={labels.removeLevelAriaLabel(index + 1)}
                  >
                    <IconButton
                      aria-label={labels.removeLevelAriaLabel(index + 1)}
                      onClick={() =>
                        onChange(levels.filter((_, i) => i !== index))
                      }
                    >
                      <Trash2 size={14} aria-hidden />
                    </IconButton>
                  </HintAction>
                </span>
              ) : null}
            </li>
          ))}
        </ul>
        <div className="delpi-ui-sort-builder__actions">
          {levels.length < maxLevels ? (
            <HintAction
              hint={labels.addLevelHint}
              ariaLabel={labels.addLevelAriaLabel}
            >
              <ActionButton
                variant="ghost"
                type="button"
                aria-label={labels.addLevelAriaLabel}
                onClick={() =>
                  onChange([
                    ...levels,
                    {
                      field:
                        options.find(
                          (option) =>
                            !levels.some((l) => l.field === option.value),
                        )?.value ?? "",
                      direction: "asc",
                    },
                  ])
                }
              >
                <Plus size={16} aria-hidden />
                {labels.addLevelLabel}
              </ActionButton>
            </HintAction>
          ) : null}
          <HintAction
            hint={labels.applyHint}
            ariaLabel={labels.applyAriaLabel}
          >
            <ActionButton
              variant="primary"
              type="button"
              aria-label={labels.applyAriaLabel}
              onClick={() => {
                onChange(levels);
                onApply();
              }}
            >
              <Check size={16} aria-hidden />
              {labels.applyLabel}
            </ActionButton>
          </HintAction>
        </div>
      </div>
    );
  }

  return DashboardSortLevelsBuilder;
}

/* ------------------------------------------------------------------ */
/* Builder de critérios de filtro (AND)                                */
/* ------------------------------------------------------------------ */

export type DashboardFilterRulesBuilderLabels = {
  ariaLabel: string;
  fieldLabel: string;
  fieldHint: string;
  operatorHint: string;
  valueLabel: string;
  valueHint: string;
  removeRuleHint: string;
  removeRuleAriaLabel: string;
  addRuleHint: string;
  addRuleLabel: ReactNode;
  addRuleAriaLabel: string;
  clearHint: string;
  clearLabel: ReactNode;
  clearAriaLabel: string;
  applyHint: string;
  applyLabel: ReactNode;
  applyAriaLabel: string;
};

export type DashboardFilterRulesBuilderProps = {
  rules: DashboardFilterRule[];
  /** Catálogo de campos filtráveis tipados do MFE. */
  fields: readonly DashboardFilterFieldDescriptor[];
  onChange: (next: DashboardFilterRule[]) => void;
  onApply: () => void;
  onClear: () => void;
  /** Gerador de id de regra (padrão: contador+aleatório do kit). */
  createRuleId?: () => string;
};

export function newDashboardFilterRuleId(): string {
  return `rule-${Date.now().toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 7)}`;
}

const DEFAULT_OPERATOR_LABELS: Record<string, string> = {
  contains: "contém",
  eq: "é",
  neq: "não é",
  gte: "de",
  lte: "até",
};

export function createDashboardFilterRulesBuilder(config: {
  prefix: string;
  labels: DashboardFilterRulesBuilderLabels;
  /** Rótulos por operador (mescla com defaults PT-BR). */
  operatorLabels?: Record<string, string>;
  portalScopeClassName?: string;
}) {
  const prefix = config.prefix;
  const labels = config.labels;
  const operatorLabels = {
    ...DEFAULT_OPERATOR_LABELS,
    ...(config.operatorLabels ?? {}),
  };
  const classNames = filtersRowBemClasses(prefix);
  const selectClassNames: SelectControlClassNames =
    selectControlBemClasses(prefix);
  const portalScope = config.portalScopeClassName;

  function DashboardFilterRulesBuilder({
    rules,
    fields,
    onChange,
    onApply,
    onClear,
    createRuleId = newDashboardFilterRuleId,
  }: DashboardFilterRulesBuilderProps) {
    function updateRule(ruleId: string, patch: Partial<DashboardFilterRule>) {
      onChange(
        rules.map((rule) => (rule.id === ruleId ? { ...rule, ...patch } : rule)),
      );
    }

    function removeRule(ruleId: string) {
      onChange(rules.filter((rule) => rule.id !== ruleId));
    }

    function addRule() {
      const field = fields[0];
      if (!field) return;
      onChange([
        ...rules,
        {
          id: createRuleId(),
          field: field.key,
          operator: field.operator,
          value: field.defaultValue ?? "",
        },
      ]);
    }

    return (
      <div className="delpi-ui-filter-builder" aria-label={labels.ariaLabel}>
        <ul className="delpi-ui-filter-builder__rules">
          {rules.map((rule) => {
            const meta =
              fields.find((item) => item.key === rule.field) ?? fields[0];
            if (!meta) return null;
            const operatorLabel =
              meta.operatorLabel ??
              operatorLabels[meta.operator] ??
              meta.operator;
            return (
              <li
                key={rule.id}
                className="delpi-ui-filter-builder__rule"
                data-kind={meta.input}
              >
                <FilterSelectField
                  label={labels.fieldLabel}
                  hint={labels.fieldHint}
                  value={rule.field}
                  searchable
                  onChange={(field) => {
                    const nextMeta =
                      fields.find((item) => item.key === field) ?? meta;
                    updateRule(rule.id, {
                      field: nextMeta.key,
                      operator: nextMeta.operator,
                      value: nextMeta.defaultValue ?? "",
                    });
                  }}
                  options={fields.map((item) => ({
                    value: item.key,
                    label: item.label,
                  }))}
                  classNames={classNames}
                  selectClassNames={selectClassNames}
                  portalScopeClassName={portalScope}
                />
                <HintAction
                  hint={labels.operatorHint}
                  ariaLabel="Ajuda: operador"
                >
                  <span className="delpi-ui-filter-builder__op">
                    {operatorLabel}
                  </span>
                </HintAction>
                {meta.input === "select" ? (
                  <FilterSelectField
                    label={labels.valueLabel}
                    hint={labels.valueHint}
                    value={rule.value}
                    searchable={meta.searchable}
                    onChange={(value) => updateRule(rule.id, { value })}
                    options={[...(meta.options ?? [])]}
                    placeholderOption={meta.placeholderOption}
                    classNames={classNames}
                    selectClassNames={selectClassNames}
                    portalScopeClassName={portalScope}
                  />
                ) : null}
                {meta.input === "text" || meta.input === "date" ? (
                  <FilterInputField
                    label={labels.valueLabel}
                    hint={labels.valueHint}
                    type={meta.input === "date" ? "date" : "search"}
                    value={rule.value}
                    onChange={(value) => updateRule(rule.id, { value })}
                    classNames={classNames}
                  />
                ) : null}
                <span className="delpi-ui-filter-builder__remove">
                  <HintAction
                    hint={labels.removeRuleHint}
                    ariaLabel={labels.removeRuleAriaLabel}
                  >
                    <IconButton
                      aria-label={labels.removeRuleAriaLabel}
                      onClick={() => removeRule(rule.id)}
                    >
                      <Trash2 size={14} aria-hidden />
                    </IconButton>
                  </HintAction>
                </span>
              </li>
            );
          })}
        </ul>
        <div className="delpi-ui-filter-builder__actions">
          <HintAction
            hint={labels.addRuleHint}
            ariaLabel={labels.addRuleAriaLabel}
          >
            <ActionButton
              variant="ghost"
              type="button"
              aria-label={labels.addRuleAriaLabel}
              onClick={addRule}
            >
              <Plus size={16} aria-hidden />
              {labels.addRuleLabel}
            </ActionButton>
          </HintAction>
          <HintAction hint={labels.clearHint} ariaLabel={labels.clearAriaLabel}>
            <ActionButton
              variant="ghost"
              type="button"
              aria-label={labels.clearAriaLabel}
              onClick={onClear}
            >
              {labels.clearLabel}
            </ActionButton>
          </HintAction>
          <HintAction hint={labels.applyHint} ariaLabel={labels.applyAriaLabel}>
            <ActionButton
              variant="primary"
              type="button"
              aria-label={labels.applyAriaLabel}
              onClick={onApply}
            >
              {labels.applyLabel}
            </ActionButton>
          </HintAction>
        </div>
      </div>
    );
  }

  return DashboardFilterRulesBuilder;
}
