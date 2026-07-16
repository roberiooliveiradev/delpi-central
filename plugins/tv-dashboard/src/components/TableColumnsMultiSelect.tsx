import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import type { TableColumnProjection, TableViewProjection } from "@delpi/tv-dashboard-presentation";

import { useProjectionDragReorder } from "../hooks/useProjectionDragReorder";

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
  nextVisible.splice(target, 0, item!);
  return buildProjection(options, nextVisible);
}

export function reorderTableColumns(
  options: TableColumnOption[],
  projection: TableViewProjection | undefined,
  visibleOrdered: string[],
): TableViewProjection | undefined {
  return buildProjection(options, visibleOrdered);
}

/**
 * Seleção e ordem de colunas da table_view (arrastar para reordenar).
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
  const hidden = options.filter((opt) => !visible.includes(opt.key));

  const { canDrag, rowClassName, rowDropProps, handleDragProps } = useProjectionDragReorder(
    visible,
    (nextVisible) => onChange(reorderTableColumns(options, tableProjection ?? undefined, nextVisible)),
  );

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
          ? "Todas as colunas — arraste para reordenar (ou desmarque para filtrar)"
          : `${visible.length} de ${options.length} colunas — arraste ⋮⋮ para reordenar`}
      </p>
      {visible.map((key, index) => {
        const option = options.find((opt) => opt.key === key) ?? { key, label: key };
        return (
          <div
            key={option.key}
            className={rowClassName("td-deck-inspector__column-row", index)}
            {...rowDropProps(index)}
          >
            {canDrag ? (
              <button
                type="button"
                className="td-deck-inspector__drag-handle"
                aria-label={`Arrastar coluna ${option.label}`}
                title="Arrastar para reordenar"
                {...handleDragProps(index)}
              >
                ⋮⋮
              </button>
            ) : null}
            <NativeCheckboxControl
              id={`${idPrefix}-${option.key}`}
              className="td-deck-inspector__checkbox"
              checked
              label={option.label}
              onChange={(nextChecked) => {
                onChange(patchTableColumnVisibility(options, visible, option.key, nextChecked));
              }}
            />
          </div>
        );
      })}
      {hidden.map((option) => (
        <div key={option.key} className="td-deck-inspector__column-row td-deck-inspector__column-row--hidden">
          <NativeCheckboxControl
            id={`${idPrefix}-${option.key}`}
            className="td-deck-inspector__checkbox"
            checked={false}
            label={option.label}
            onChange={(nextChecked) => {
              onChange(patchTableColumnVisibility(options, visible, option.key, nextChecked));
            }}
          />
        </div>
      ))}
    </div>
  );
}
