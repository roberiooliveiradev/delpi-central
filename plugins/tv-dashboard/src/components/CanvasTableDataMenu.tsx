import { Columns3, Database, type LucideIcon } from "lucide-react";

export type CanvasTableDataMenuActionId = "source" | "columns" | "cell-binding";

type Action = {
  id: CanvasTableDataMenuActionId;
  label: string;
  icon: LucideIcon;
};

type Props = {
  variant?: "block" | "cell";
  onSelect: (actionId: CanvasTableDataMenuActionId) => void;
  className?: string;
};

const BLOCK_ACTIONS: Action[] = [
  { id: "source", label: "Selecionar fonte…", icon: Database },
  { id: "columns", label: "Colunas do visual…", icon: Columns3 },
];

const CELL_ACTIONS: Action[] = [
  { id: "source", label: "Selecionar fonte…", icon: Database },
  { id: "cell-binding", label: "Vínculo da célula…", icon: Columns3 },
];

/**
 * Menu de dados da Grade — chrome `td-chart-add-element`.
 * Variantes bloco/célula via props.
 */
export function CanvasTableDataMenu({
  variant = "block",
  onSelect,
  className,
}: Props) {
  const actions = variant === "cell" ? CELL_ACTIONS : BLOCK_ACTIONS;
  return (
    <ul
      className={["td-chart-add-element", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label={variant === "cell" ? "Dados da célula da Grade" : "Dados da Grade"}
    >
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <li key={action.id} className="td-chart-add-element__root">
            <button
              type="button"
              role="menuitem"
              className="td-chart-add-element__root-btn"
              onClick={() => onSelect(action.id)}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{action.label}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
