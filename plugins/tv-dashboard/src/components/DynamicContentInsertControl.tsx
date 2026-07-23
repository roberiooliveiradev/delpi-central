import { Braces } from "lucide-react";
import { useMemo, useRef, useState } from "react";

import {
  discoverResolvedFieldOptions,
  isComunicadoVisualBoxBlock,
  type DynamicContentKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
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

  const targetBlock = useMemo(() => {
    if (editingTextId) {
      return blocks.find((block) => block.id === editingTextId) ?? null;
    }
    if (
      selected?.type === "canvas_table" &&
      selectedCanvasTableCell?.blockId === selected.id
    ) {
      return selected;
    }
    return null;
  }, [blocks, editingTextId, selected, selectedCanvasTableCell]);

  const sourceId =
    targetBlock && "dataSourceId" in targetBlock
      ? String(targetBlock.dataSourceId ?? "").trim()
      : "";
  const linkedSource = sourceId ? blocks.find((block) => block.id === sourceId) ?? null : null;
  const resolved =
    linkedSource && "resolved" in linkedSource && linkedSource.resolved
      ? linkedSource.resolved
      : targetBlock && "resolved" in targetBlock
        ? targetBlock.resolved
        : undefined;
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
