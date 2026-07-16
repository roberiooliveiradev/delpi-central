import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  ArrowDownAZ,
  ArrowDownZA,
  ChevronDown,
  ChevronUp,
  Clipboard,
  Columns3,
  Eraser,
  Filter,
  Pencil,
  RefreshCw,
  Trash2,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const C = TV_DASHBOARD_HELP_TOOLTIPS.dataPrepareContextMenu;

export type DataPrepareCtxTarget =
  | { kind: "query"; id: string }
  | { kind: "fonte" }
  | { kind: "step"; index: number }
  | { kind: "column"; name: string };

export type DataPrepareContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  target: DataPrepareCtxTarget | null;
  canMoveStepUp?: boolean;
  canMoveStepDown?: boolean;
  hasSteps?: boolean;
  onClose: () => void;
  onRefresh: () => void;
  onClearSteps: () => void;
  onCopyText: (text: string) => void;
  onEditStepFx: (index: number) => void;
  onMoveStep: (index: number, delta: number) => void;
  onDeleteStep: (index: number) => void;
  onRenameColumn: (column: string) => void;
  onFilterColumn: (column: string) => void;
  onSortColumn: (column: string, direction: "asc" | "desc") => void;
  onRemoveColumn: (column: string) => void;
  onKeepOnlyColumn: (column: string) => void;
  queryOperationId?: string | null;
};

/**
 * Menu de contexto (botão direito) do modal Preparar dados.
 */
export function DataPrepareContextMenu({
  open,
  position,
  target,
  canMoveStepUp = false,
  canMoveStepDown = false,
  hasSteps = false,
  onClose,
  onRefresh,
  onClearSteps,
  onCopyText,
  onEditStepFx,
  onMoveStep,
  onDeleteStep,
  onRenameColumn,
  onFilterColumn,
  onSortColumn,
  onRemoveColumn,
  onKeepOnlyColumn,
  queryOperationId = null,
}: DataPrepareContextMenuProps) {
  function run(action: () => void) {
    action();
    onClose();
  }

  if (!target) return null;

  return (
    <ContextMenu open={open} position={position} onClose={onClose} aria-label={C.menu}>
      {target.kind === "query" || target.kind === "fonte" ? (
        <>
          <ContextMenuItem
            label={C.refresh}
            icon={RefreshCw}
            onSelect={() => run(onRefresh)}
          />
          {target.kind === "query" ? (
            <>
              <ContextMenuItem
                label={C.clearSteps}
                icon={Eraser}
                disabled={!hasSteps}
                onSelect={() => run(onClearSteps)}
              />
              <ContextMenuDivider />
              <ContextMenuItem
                label={C.copyRoute}
                icon={Clipboard}
                disabled={!queryOperationId}
                onSelect={() => run(() => onCopyText(queryOperationId || ""))}
              />
            </>
          ) : null}
        </>
      ) : null}

      {target.kind === "step" ? (
        <>
          <ContextMenuItem
            label={C.editFx}
            icon={Pencil}
            onSelect={() => run(() => onEditStepFx(target.index))}
          />
          <ContextMenuItem
            label={C.moveUp}
            icon={ChevronUp}
            disabled={!canMoveStepUp}
            onSelect={() => run(() => onMoveStep(target.index, -1))}
          />
          <ContextMenuItem
            label={C.moveDown}
            icon={ChevronDown}
            disabled={!canMoveStepDown}
            onSelect={() => run(() => onMoveStep(target.index, 1))}
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.deleteStep}
            icon={Trash2}
            destructive
            onSelect={() => run(() => onDeleteStep(target.index))}
          />
        </>
      ) : null}

      {target.kind === "column" ? (
        <>
          <ContextMenuItem
            label={C.renameColumn}
            icon={Pencil}
            onSelect={() => run(() => onRenameColumn(target.name))}
          />
          <ContextMenuItem
            label={C.filterColumn}
            icon={Filter}
            onSelect={() => run(() => onFilterColumn(target.name))}
          />
          <ContextMenuItem
            label={C.sortAsc}
            icon={ArrowDownAZ}
            onSelect={() => run(() => onSortColumn(target.name, "asc"))}
          />
          <ContextMenuItem
            label={C.sortDesc}
            icon={ArrowDownZA}
            onSelect={() => run(() => onSortColumn(target.name, "desc"))}
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.selectAllColumns}
            icon={Columns3}
            onSelect={() => run(() => onKeepOnlyColumn(target.name))}
          />
          <ContextMenuItem
            label={C.removeColumn}
            icon={Trash2}
            destructive
            onSelect={() => run(() => onRemoveColumn(target.name))}
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.copyColumn}
            icon={Clipboard}
            onSelect={() => run(() => onCopyText(target.name))}
          />
        </>
      ) : null}
    </ContextMenu>
  );
}
