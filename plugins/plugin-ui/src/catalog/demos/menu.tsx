import { useState } from "react";

import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  ContextMenuToolbar,
  ContextMenuToolbarButton,
} from "../../components/menu";
import type { CatalogEntryDraft } from "../types";

export const menuCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "menu.ContextMenu",
    family: "menu",
    exportName: "ContextMenu",
    title: "ContextMenu",
    description: "Menu contextual portaled (posição fixa).",
    demos: [
      {
        id: "default",
        label: "Abrir",
        render: () => <ContextMenuDemo />,
      },
    ],
  },
  {
    id: "menu.ContextMenuItem",
    family: "menu",
    exportName: "ContextMenuItem",
    title: "ContextMenuItem",
    demos: [
      {
        id: "default",
        label: "Itens",
        render: () => (
          <div className="puc-card" style={{ maxWidth: 220 }}>
            <ContextMenuItem label="Editar" onSelect={() => undefined} />
            <ContextMenuDivider />
            <ContextMenuItem label="Excluir" destructive onSelect={() => undefined} />
          </div>
        ),
      },
    ],
  },
  {
    id: "menu.ContextMenuDivider",
    family: "menu",
    exportName: "ContextMenuDivider",
    title: "ContextMenuDivider",
    demos: [
      {
        id: "default",
        label: "Divisor",
        render: () => (
          <div className="puc-card" style={{ maxWidth: 220 }}>
            <ContextMenuItem label="Ação A" onSelect={() => undefined} />
            <ContextMenuDivider />
            <ContextMenuItem label="Ação B" onSelect={() => undefined} />
          </div>
        ),
      },
    ],
  },
  {
    id: "menu.ContextMenuToolbar",
    family: "menu",
    exportName: "ContextMenuToolbar",
    title: "ContextMenuToolbar",
    demos: [
      {
        id: "default",
        label: "Toolbar",
        render: () => (
          <ContextMenuToolbar aria-label="Ações">
            <ContextMenuToolbarButton label="Copiar" onClick={() => undefined} />
            <ContextMenuToolbarButton label="Colar" onClick={() => undefined} />
          </ContextMenuToolbar>
        ),
      },
    ],
  },
  {
    id: "menu.ContextMenuToolbarButton",
    family: "menu",
    exportName: "ContextMenuToolbarButton",
    title: "ContextMenuToolbarButton",
    demos: [
      {
        id: "default",
        label: "Botão",
        render: () => <ContextMenuToolbarButton label="Ação" onClick={() => undefined} />,
      },
    ],
  },
];

function ContextMenuDemo() {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);

  return (
    <div className="puc-stack">
      <button
        type="button"
        className="puc-primary-btn"
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          setPosition({ x: rect.left, y: rect.bottom + 8 });
          setOpen(true);
        }}
      >
        Abrir menu
      </button>
      <ContextMenu open={open} position={position} onClose={() => setOpen(false)} aria-label="Menu demo">
        <ContextMenuItem label="Opção 1" onSelect={() => setOpen(false)} />
        <ContextMenuDivider />
        <ContextMenuItem label="Opção 2" onSelect={() => setOpen(false)} />
      </ContextMenu>
    </div>
  );
}
