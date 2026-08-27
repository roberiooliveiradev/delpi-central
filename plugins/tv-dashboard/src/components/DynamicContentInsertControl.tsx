import { Braces } from "lucide-react";
import { useMemo, useRef, useState } from "react";

import {
  discoverResolvedFieldOptions,
  isComunicadoVisualBoxBlock,
  normalizeCanvasTableCell,
  resolveCanvasTableCellResolved,
  resolveCanvasTableCellSourceId,
  type DynamicContentKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { primaryCanvasTableCellRef } from "../utils/canvasTableCellSelection";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DynamicContentPickerPopover } from "./DynamicContentPickerPopover";
import { TdRibbonIconButton } from "./tdRibbonUi";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;
const D = TV_DASHBOARD_HELP_TOOLTIPS.dynamicContent;

type Props = {
  variant?: "ribbon" | "inspector";
};

/**
 * Atalho `{ }` — abre o fluxo de conteúdo dinâmico e aplica no alvo ativo
 * (texto/forma em edição ou célula da Grade).
 */
export function DynamicContentInsertControl({ variant = "ribbon" }: Props) {
  const {
    selected,
    blocks,
    editingTextId,
    selectedCanvasTableCell,
    applyDynamicContentSpec,
    openDataCatalog,
    requestRibbonTab,
  } = useComunicadoEditor();

  const anchorRef = useRef<HTMLElement | null>(null);
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<DynamicContentKind>("data_field");

  const primaryCellRef = useMemo(
    () =>
      selected?.type === "canvas_table" &&
      selectedCanvasTableCell?.blockId === selected.id
        ? primaryCanvasTableCellRef(selectedCanvasTableCell)
        : null,
    [selected, selectedCanvasTableCell],
  );

  const targetBlock = useMemo(() => {
    if (editingTextId) {
      return blocks.find((block) => block.id === editingTextId) ?? null;
    }
    if (selected?.type === "canvas_table" && primaryCellRef) {
      return selected;
    }
    return null;
  }, [blocks, editingTextId, primaryCellRef, selected]);

  const sourceId = useMemo(() => {
    if (!targetBlock) return "";
    if (targetBlock.type === "canvas_table" && primaryCellRef) {
      const cell = normalizeCanvasTableCell(
        targetBlock.cells[primaryCellRef.row]?.[primaryCellRef.col],
      );
      return resolveCanvasTableCellSourceId(targetBlock, cell);
    }
    if ("dataSourceId" in targetBlock) {
      return String(targetBlock.dataSourceId ?? "").trim();
    }
    return "";
  }, [primaryCellRef, targetBlock]);

  const linkedSource = sourceId ? blocks.find((block) => block.id === sourceId) ?? null : null;
  const resolved = useMemo(() => {
    if (targetBlock?.type === "canvas_table" && primaryCellRef) {
      const cell = normalizeCanvasTableCell(
        targetBlock.cells[primaryCellRef.row]?.[primaryCellRef.col],
      );
      const fromMap = resolveCanvasTableCellResolved(targetBlock, cell);
      if (fromMap) return fromMap;
    }
    if (linkedSource && "resolved" in linkedSource && linkedSource.resolved) {
      return linkedSource.resolved;
    }
    if (targetBlock && "resolved" in targetBlock) return targetBlock.resolved;
    return undefined;
  }, [linkedSource, primaryCellRef, targetBlock]);
  const fieldLabels =
    linkedSource && "fieldLabels" in linkedSource
      ? (linkedSource as { fieldLabels?: Record<string, string> }).fieldLabels
      : undefined;

  const fieldOptions = useMemo(
    () =>
      discoverResolvedFieldOptions(resolved, undefined, fieldLabels).map((item) => ({
        field: item.field,
        label: item.label ?? item.field,
      })),
    [fieldLabels, resolved],
  );

  const visible =
    Boolean(
      editingTextId &&
        targetBlock &&
        isComunicadoVisualBoxBlock(targetBlock) &&
        editingTextId === targetBlock.id,
    ) ||
    Boolean(
      selected?.type === "canvas_table" &&
        selectedCanvasTableCell &&
        selectedCanvasTableCell.blockId === selected.id,
    );

  if (!visible) return null;

  const linkOrCatalog = () => {
    requestRibbonTab("data");
    if (!sourceId) openDataCatalog("insert");
  };

  return (
    <>
      {variant === "ribbon" ? (
        <span
          ref={(node) => {
            anchorRef.current = node;
          }}
          className="td-dynamic-content-insert"
        >
          <TdRibbonIconButton
            hint={H.insertFieldAtCursor}
            ariaLabel={D.insertAria}
            active={open}
            onClick={() => setOpen((current) => !current)}
          >
            <Braces size={15} aria-hidden="true" />
          </TdRibbonIconButton>
        </span>
      ) : (
        <button
          ref={(node) => {
            anchorRef.current = node;
          }}
          type="button"
          className="td-btn td-btn--sm"
          aria-label={D.insertAria}
          title={H.insertFieldAtCursor}
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => setOpen((current) => !current)}
        >
          <Braces size={15} aria-hidden="true" />
          <span>{D.insertLabel}</span>
        </button>
      )}
      <DynamicContentPickerPopover
        open={open}
        onOpenChange={setOpen}
        anchorRef={anchorRef}
        kind={kind}
        onKindChange={setKind}
        fieldOptions={fieldOptions}
        hasDataSource={Boolean(sourceId)}
        onPick={(spec) => {
          applyDynamicContentSpec(spec);
        }}
        onLinkOrOpenCatalog={linkOrCatalog}
      />
    </>
  );
}
