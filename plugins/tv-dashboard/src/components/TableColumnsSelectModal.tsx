import {
  buildViewFrameFitPatch,
  discoverResolvedFieldOptions,
  isDataSourceBlockType,
  patchFieldLabels,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
  type ComunicadoTableViewBlock,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  TableColumnsMultiSelect,
  resolveVisibleKeys,
  type TableColumnOption,
} from "./TableColumnsMultiSelect";
import { HostContainedDialog } from "./ui/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
  block: ComunicadoTableViewBlock;
};

/**
 * Diálogo host-contained «Colunas do visual» — paridade com ChartSelectDataModal.
 * O menu flutuante/ribbon abre o card centralizado no host (não só a sidebar).
 */
export function TableColumnsSelectModal({ open, onClose, block }: Props) {
  const {
    blocks,
    updateSelected,
    updateBlock,
    selectedTablePart,
    selectTablePart,
    reconcileTablePartsForVisibleKeys,
  } = useComunicadoEditor();

  const source = useMemo(() => {
    if (!block.dataSourceId) return null;
    const found = blocks.find((item) => item.id === block.dataSourceId);
    return found && isDataSourceBlockType(found.type)
      ? (found as ComunicadoDataSourceBlock)
      : null;
  }, [block.dataSourceId, blocks]);

  const columnOptions: TableColumnOption[] = useMemo(() => {
    const resolved = source?.resolved ?? block.resolved;
    if (!resolved) return [];
    return discoverResolvedFieldOptions(resolved, undefined, source?.fieldLabels).map((item) => ({
      key: item.field,
      label: item.label,
    }));
  }, [block.resolved, source]);

  const applyProjection = (next: TableViewProjection | undefined) => {
    const prevVisible = resolveVisibleKeys(columnOptions, block.tableProjection);
    const nextVisible = resolveVisibleKeys(columnOptions, next);
    reconcileTablePartsForVisibleKeys(prevVisible, nextVisible);
    const framePatch = buildViewFrameFitPatch({
      ...block,
      tableProjection: next,
    } as ComunicadoBlock);
    updateSelected({
      tableProjection: next,
      ...(framePatch ?? {}),
    } as Partial<ComunicadoTableViewBlock>);
  };

  return (
    <HostContainedDialog
      open={open}
      title="Colunas do visual"
      onClose={onClose}
      className="td-modal--table-columns"
    >
      <p className="td-deck-inspector__hint">
        Marque as colunas visíveis, arraste para reordenar e ajuste o rótulo. As alterações
        aplicam-se ao visual selecionado.
      </p>
      {columnOptions.length === 0 ? (
        <p className="td-deck-inspector__meta">
          Sem campos disponíveis. Conecte uma fonte e atualize o visual.
        </p>
      ) : (
        <TableColumnsMultiSelect
          idPrefix="td-select-table-col"
          options={columnOptions}
          tableProjection={block.tableProjection}
          onChange={applyProjection}
          focusedColumnKey={
            selectedTablePart?.kind === "headerCell" && selectedTablePart.colIndex != null
              ? resolveVisibleKeys(columnOptions, block.tableProjection)[
                  selectedTablePart.colIndex
                ] ?? null
              : null
          }
          onSelectColumn={(key) => {
            const visibleKeys = resolveVisibleKeys(columnOptions, block.tableProjection);
            const colIndex = visibleKeys.indexOf(key);
            if (colIndex < 0) return;
            selectTablePart(block.id, { kind: "headerCell", colIndex });
          }}
          sourceFieldLabels={source?.fieldLabels}
          onRenameField={
            source
              ? (key, label) => {
                  updateBlock(source.id, {
                    fieldLabels: patchFieldLabels(source.fieldLabels, key, label),
                  } as Partial<ComunicadoBlock>);
                }
              : undefined
          }
        />
      )}
      <div className="td-data-prepare__row" style={{ marginTop: 12, justifyContent: "flex-end" }}>
        <button type="button" className="td-btn td-btn--sm" onClick={onClose}>
          Concluir
        </button>
      </div>
    </HostContainedDialog>
  );
}
