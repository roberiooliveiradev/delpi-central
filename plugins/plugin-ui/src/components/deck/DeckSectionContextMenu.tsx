import {
  Eye,
  EyeOff,
  FolderInput,
  Plus,
  Pencil,
  Settings2,
  Trash2,
} from "lucide-react";

import { ContextMenu } from "../menu/ContextMenu";
import { ContextMenuDivider } from "../menu/ContextMenuDivider";
import { ContextMenuItem } from "../menu/ContextMenuItem";
import type { FixedPanelPoint } from "../menu/useFixedPanelPosition";

export type DeckSectionContextMenuAction =
  | "add-slide"
  | "rename"
  | "properties"
  | "toggle-active"
  | "collapse"
  | "expand"
  | "delete-section"
  | "delete-section-and-slides";

export type DeckSectionContextMenuProps = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
  collapsed?: boolean;
  active?: boolean;
  /** Se false, omite ações de exclusão (seção principal). */
  allowDelete?: boolean;
  portalScopeClassName?: string;
  onAction: (action: DeckSectionContextMenuAction) => void;
};

/**
 * Menu de seção (PPT-like): nova tela, renomear, propriedades, ocultar, colapsar, excluir.
 */
export function DeckSectionContextMenu({
  open,
  position,
  onClose,
  collapsed = false,
  active = true,
  allowDelete = true,
  portalScopeClassName,
  onAction,
}: DeckSectionContextMenuProps) {
  const run = (action: DeckSectionContextMenuAction) => {
    onAction(action);
    onClose();
  };

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label="Menu da seção"
      portalScopeClassName={portalScopeClassName}
    >
      <ContextMenuItem
        label="Nova tela nesta seção"
        icon={Plus}
        onSelect={() => run("add-slide")}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label="Renomear"
        icon={Pencil}
        onSelect={() => run("rename")}
      />
      <ContextMenuItem
        label="Propriedades da seção"
        icon={Settings2}
        onSelect={() => run("properties")}
      />
      <ContextMenuItem
        label={active ? "Ocultar na TV" : "Mostrar na TV"}
        icon={active ? EyeOff : Eye}
        onSelect={() => run("toggle-active")}
      />
      <ContextMenuItem
        label={collapsed ? "Expandir" : "Recolher"}
        icon={FolderInput}
        onSelect={() => run(collapsed ? "expand" : "collapse")}
      />
      {allowDelete ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label="Excluir seção"
            icon={Trash2}
            onSelect={() => run("delete-section")}
          />
          <ContextMenuItem
            label="Excluir seção e slides"
            icon={Trash2}
            destructive
            onSelect={() => run("delete-section-and-slides")}
          />
        </>
      ) : null}
    </ContextMenu>
  );
}
