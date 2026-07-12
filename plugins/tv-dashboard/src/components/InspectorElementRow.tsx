import { NativeCheckboxControl } from "@delpi/plugin-ui/index";

type InspectorElementRowProps = {
  id: string;
  label: string;
  hint?: string;
  focused?: boolean;
  /** Se omitido, linha só seleciona (ex.: Moldura) — mantém coluna do toggle alinhada. */
  enabled?: boolean;
  onToggle?: (next: boolean) => void;
  onSelect: () => void;
};

/**
 * Linha canônica «Elementos do …» no inspetor (gráfico / tabela / KPI).
 * Checkbox + rótulo — mesmo visual em todos os blocos de dados.
 */
export function InspectorElementRow({
  id,
  label,
  hint,
  focused = false,
  enabled,
  onToggle,
  onSelect,
}: InspectorElementRowProps) {
  const canToggle = typeof enabled === "boolean" && typeof onToggle === "function";

  return (
    <div
      className={["td-chart-element", "td-chart-element--row", focused ? "td-chart-element--focused" : null]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-chart-element__summary">
        <span className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          {canToggle ? (
            <NativeCheckboxControl
              checked={enabled}
              aria-label={`Exibir ${label}`}
              onChange={onToggle}
            />
          ) : (
            <span className="td-chart-element__toggle-spacer" aria-hidden="true" />
          )}
        </span>
        <button
          type="button"
          className="td-chart-element__label-btn"
          id={id}
          title={hint}
          onClick={(event) => {
            event.preventDefault();
            onSelect();
          }}
        >
          {label}
        </button>
      </div>
    </div>
  );
}
