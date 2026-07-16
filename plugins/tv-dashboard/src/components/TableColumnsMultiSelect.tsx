import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import type { TableColumnProjection, TableViewProjection } from "@delpi/tv-dashboard-presentation";

export type TableColumnOption = {
  key: string;
  label: string;
};

type Props = {
  idPrefix: string;
  options: TableColumnOption[];
  /** undefined = todas visíveis na ordem do catálogo. */
  tableProjection?: TableViewProjection | null;
  onChange: (next: TableViewProjection | undefined) => void;
  compact?: boolean;
};

export function resolveVisibleKeys(
  options: TableColumnOption[],
  projection?: TableViewProjection | null,
): string[] {
  if (!projection?.columns?.length) {
    return options.map((item) => item.key);
  }
  const catalog = new Set(options.map((item) => item.key));
  const ordered = projection.columns
    .filter((col) => col.visible !== false && catalog.has(col.key))
    .map((col) => col.key);
  for (const option of options) {
    const known = projection.columns.some((col) => col.key === option.key);
    if (!known) ordered.push(option.key);
  }
  return ordered;
}

function buildProjection(
  options: TableColumnOption[],
  visibleOrdered: string[],
): TableViewProjection | undefined {
  const catalog = options.map((item) => item.key);
  if (visibleOrdered.length === catalog.length && catalog.every((key, i) => visibleOrdered[i] === key)) {
    return undefined;
  }
  if (visibleOrdered.length === catalog.length) {
    // Todas visíveis mas reordenadas.
    return {
      columns: visibleOrdered.map((key) => ({
        key,
        label: options.find((opt) => opt.key === key)?.label,
        visible: true,
      })),
    };
  }
  const hidden = catalog.filter((key) => !visibleOrdered.includes(key));
  const columns: TableColumnProjection[] = [
    ...visibleOrdered.map((key) => ({
      key,
      label: options.find((opt) => opt.key === key)?.label,
      visible: true,
    })),
    ...hidden.map((key) => ({
      key,
      label: options.find((opt) => opt.key === key)?.label,
      visible: false,
    })),
  ];
  return { columns };
}

export function patchTableColumnVisibility(
  options: TableColumnOption[],
  currentVisible: string[],
  key: string,
  checked: boolean,
): TableViewProjection | undefined {
  const next = [...currentVisible];
  const index = next.indexOf(key);
  if (checked && index < 0) next.push(key);
  if (!checked && index >= 0) next.splice(index, 1);
  return buildProjection(options, next);
}

export function moveTableColumn(
  options: TableColumnOption[],
  projection: TableViewProjection | undefined,
  key: string,
  direction: -1 | 1,
): TableViewProjection | undefined {
  const visible = resolveVisibleKeys(options, projection);
  const index = visible.indexOf(key);
  if (index < 0) return projection;
  const target = index + direction;
  if (target < 0 || target >= visible.length) return projection;
  const nextVisible = [...visible];
  const [item] = nextVisible.splice(index, 1);
  nextVisible.splice(target, 0, item);
  return buildProjection(options, nextVisible);
}

/**
 * Seleção e ordem de colunas da table_view.
 * Vazio/automático = todas as colunas do resolved.
 */
export function TableColumnsMultiSelect({
  idPrefix,
  options,
  tableProjection,
  onChange,
  compact = false,
}: Props) {
  if (options.length === 0) return null;

  const visible = resolveVisibleKeys(options, tableProjection);
  const isAutomatic = !tableProjection?.columns?.length;

  return (
    <div
      className={
        compact
          ? "td-deck-inspector__value-fields td-deck-inspector__value-fields--compact"
          : "td-deck-inspector__value-fields"
      }
      role="group"
      aria-label="Colunas da tabela"
    >
      <p className="td-deck-inspector__hint">
        {isAutomatic
          ? "Todas as colunas (desmarque para filtrar)"
          : `${visible.length} de ${options.length} colunas`}
      </p>
      {options.map((option) => {
        const checked = visible.includes(option.key);
        const orderIndex = visible.indexOf(option.key);
        return (
          <div key={option.key} className="td-deck-inspector__column-row">
            <NativeCheckboxControl
              id={`${idPrefix}-${option.key}`}
              className="td-deck-inspector__checkbox"
              checked={checked}
              label={option.label}
              onChange={(nextChecked) => {
                onChange(patchTableColumnVisibility(options, visible, option.key, nextChecked));
              }}
            />
            {checked && !isAutomatic ? (
              <span className="td-deck-inspector__column-order">
                <button
                  type="button"
                  className="td-btn td-btn--ghost td-btn--sm"
                  aria-label={`Subir ${option.label}`}
                  disabled={orderIndex <= 0}
                  onClick={() =>
                    onChange(moveTableColumn(options, tableProjection ?? undefined, option.key, -1))
                  }
                >
                  ↑
                </button>
                <button
                  type="button"
                  className="td-btn td-btn--ghost td-btn--sm"
                  aria-label={`Descer ${option.label}`}
                  disabled={orderIndex < 0 || orderIndex >= visible.length - 1}
                  onClick={() =>
                    onChange(moveTableColumn(options, tableProjection ?? undefined, option.key, 1))
                  }
                >
                  ↓
                </button>
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
