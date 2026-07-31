import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Archive,
  Copy,
  Download,
  EyeOff,
  LayoutTemplate,
  Trash2,
  Upload,
} from "lucide-react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import type { SlideTemplate } from "../api/tvDashboardApi";

type Props = {
  open: boolean;
  position: FixedPanelPoint | null;
  template: SlideTemplate;
  onClose: () => void;
  onOpen: () => void;
  onPublish: () => void;
  onUnpublish: () => void;
  onClone: () => void;
  onExport: () => void;
  onArchive: () => void;
  onDelete: () => void;
};

/** Menu do botão direito nos cards da Biblioteca (mesmo padrão da home). */
export function TemplateLibraryContextMenu({
  open,
  position,
  template,
  onClose,
  onOpen,
  onPublish,
  onUnpublish,
  onClone,
  onExport,
  onArchive,
  onDelete,
}: Props) {
  function run(action: () => void) {
    action();
    onClose();
  }

  const isPublished = template.status === "published";
  const isSystem = template.isSystem;

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={`Ações: ${template.label}`}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      <ContextMenuItem
        label="Abrir"
        icon={LayoutTemplate}
        onSelect={() => run(onOpen)}
      />
      {isPublished ? (
        <ContextMenuItem
          label="Despublicar"
          icon={EyeOff}
          disabled={isSystem}
          onSelect={() => run(onUnpublish)}
        />
      ) : (
        <ContextMenuItem label="Publicar" icon={Upload} onSelect={() => run(onPublish)} />
      )}
      <ContextMenuItem label="Duplicar" icon={Copy} onSelect={() => run(onClone)} />
      <ContextMenuItem label="Exportar MDD" icon={Download} onSelect={() => run(onExport)} />
      <ContextMenuDivider />
      <ContextMenuItem
        label="Arquivar"
        icon={Archive}
        disabled={isSystem}
        onSelect={() => run(onArchive)}
      />
      <ContextMenuItem
        label="Excluir"
        icon={Trash2}
        disabled={isSystem}
        destructive
        onSelect={() => run(onDelete)}
      />
    </ContextMenu>
  );
}
