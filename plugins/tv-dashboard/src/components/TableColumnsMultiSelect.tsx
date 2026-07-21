import { NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  isAutoBakedFieldLabel,
  lookupFieldLabel,
  type TableColumnProjection,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";

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
  /**
   * Renomeia no registro da fonte (preferido). Sem callback, o rótulo
   * opcional vai para `tableProjection.columns[].label` (override do visual).
   */
  onRenameField?: (key: string, label: string) => void;
  /** Rótulos atuais da fonte — valor do input quando onRenameField está definido. */
  sourceFieldLabels?: Record<string, string> | null;
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

function previousLabelByKey(
  previous?: TableViewProjection | null,
): Map<string, string | undefined> {
  return new Map((previous?.columns ?? []).map((col) => [col.key, col.label]));
}

/**
 * Monta projeção preservando labels custom já gravados.
 * Não injeta label do catálogo — senão sombreia `data_source.fieldLabels`.
 */
export function buildProjection(
  options: TableColumnOption[],
  visibleOrdered: string[],
  previous?: TableViewProjection | null,
): TableViewProjection | undefined {
  const catalog = options.map((item) => item.key);
  const prevLabels = previousLabelByKey(previous);
  const labelFor = (key: string) => {
    const custom = prevLabels.get(key)?.trim();
    return custom || undefined;
  };

  const sameOrder =
    visibleOrdered.length === catalog.length &&
    catalog.every((key, i) => visibleOrdered[i] === key);
  const hasCustomLabels = catalog.some((key) => Boolean(labelFor(key)));

  if (sameOrder && !hasCustomLabels) {
    return undefined;
  }

  if (sameOrder) {
    return {
      columns: visibleOrdered.map((key) => ({
        key,
        label: labelFor(key),
        visible: true,
      })),
    };
  }

  const hidden = catalog.filter((key) => !visibleOrdered.includes(key));
  const columns: TableColumnProjection[] = [
    ...visibleOrdered.map((key) => ({
      key,
      label: labelFor(key),
      visible: true,
    })),
    ...hidden.map((key) => ({
      key,
      label: labelFor(key),
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
  previous?: TableViewProjection | null,
): TableViewProjection | undefined {
  const next = [...currentVisible];
  const index = next.indexOf(key);
  if (checked && index < 0) next.push(key);
  if (!checked && index >= 0) next.splice(index, 1);
  return buildProjection(options, next, previous);
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
  return buildProjection(options, nextVisible, projection);
}

export function reorderTableColumns(
  options: TableColumnOption[],
  projection: TableViewProjection | undefined,
  visibleOrdered: string[],
): TableViewProjection | undefined {
  return buildProjection(options, visibleOrdered, projection);
}

export function patchTableColumnLabel(
  options: TableColumnOption[],
  projection: TableViewProjection | undefined,
  key: string,
  label: string,
): TableViewProjection | undefined {
  const visible = resolveVisibleKeys(options, projection);
  const base =
    buildProjection(options, visible, projection) ??
    ({
      columns: options.map((item) => ({
        key: item.key,
        visible: true,
      })),
    } satisfies TableViewProjection);
  const columns = (base.columns ?? []).map((col) =>
    col.key === key ? { ...col, label: label.trim() || undefined } : col,
  );
  return { columns };
}

/**
 * Seleção e ordem de colunas da table_view (arrastar para reordenar) + rótulo.
 */
export function TableColumnsMultiSelect({
  idPrefix,
  options,
  tableProjection,
  onChange,
  onRenameField,
  sourceFieldLabels,
  compact = false,
}: Props) {
  if (options.length === 0) return null;

  const visible = resolveVisibleKeys(options, tableProjection);
  const isAutomatic = !tableProjection?.columns?.length;
  const hidden = options.filter((opt) => !visible.includes(opt.key));

  const { canDrag, rowClassName, rowDropProps, handleDragProps } = useProjectionDragReorder(
    visible,
    (nextVisible) =>
      onChange(reorderTableColumns(options, tableProjection ?? undefined, nextVisible)),
  );

  function renameControl(key: string, defaultLabel: string) {
    const customFromSource = lookupFieldLabel(sourceFieldLabels, key) ?? "";
    const customFromProjection =
      tableProjection?.columns?.find((col) => col.key === key)?.label ?? "";
    const labelValue = onRenameField
      ? customFromSource
      : isAutoBakedFieldLabel(customFromProjection, key)
        ? ""
        : customFromProjection;
    return (
      <NativeTextControl
        className={compact ? "delpi-ui-native-control--compact" : undefined}
        aria-label={`Rótulo de ${key}`}
        placeholder={defaultLabel}
        value={labelValue}
        onChange={(value) => {
          if (onRenameField) {
            onRenameField(key, value);
            return;
          }
          onChange(patchTableColumnLabel(options, tableProjection ?? undefined, key, value));
        }}
      />
    );
  }

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
            <div className="td-deck-inspector__column-row-body">
              <NativeCheckboxControl
                id={`${idPrefix}-${option.key}`}
                className="td-deck-inspector__checkbox"
                checked
                label={option.label}
                onChange={(nextChecked) => {
                  onChange(
                    patchTableColumnVisibility(
                      options,
                      visible,
                      option.key,
                      nextChecked,
                      tableProjection,
                    ),
                  );
                }}
              />
              {renameControl(option.key, option.label)}
            </div>
          </div>
        );
      })}
      {hidden.map((option) => (
        <div
          key={option.key}
          className="td-deck-inspector__column-row td-deck-inspector__column-row--hidden"
        >
          <div className="td-deck-inspector__column-row-body">
            <NativeCheckboxControl
              id={`${idPrefix}-${option.key}`}
              className="td-deck-inspector__checkbox"
              checked={false}
              label={option.label}
              onChange={(nextChecked) => {
                onChange(
                  patchTableColumnVisibility(
                    options,
                    visible,
                    option.key,
                    nextChecked,
                    tableProjection,
                  ),
                );
              }}
            />
            {renameControl(option.key, option.label)}
          </div>
        </div>
      ))}
    </div>
  );
}
