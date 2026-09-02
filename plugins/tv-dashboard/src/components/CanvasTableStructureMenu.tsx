import {
  Columns3,
  Rows3,
  TableCellsMerge,
  TableCellsSplit,
  type LucideIcon,
} from "lucide-react";

export type CanvasTableStructureActionId =
  | "insert-row-before"
  | "insert-row-after"
  | "insert-col-before"
  | "insert-col-after"
  | "delete-row"
  | "delete-col"
  | "merge"
  | "unmerge";

type Action = {
  id: CanvasTableStructureActionId;
  label: string;
  icon: LucideIcon;
  disabled?: boolean;
};

type Props = {
  onSelect: (actionId: CanvasTableStructureActionId) => void;
  canMerge?: boolean;
  canUnmerge?: boolean;
  canDeleteRow?: boolean;
  canDeleteCol?: boolean;
  className?: string;
};

/**
 * Menu `+` de estrutura da Grade — chrome `td-chart-add-element`.
 * Só dispara callbacks; persistência fica nos commands do host.
 */
export function CanvasTableStructureMenu({
  onSelect,
  canMerge = false,
  canUnmerge = false,
  canDeleteRow = true,
  canDeleteCol = true,
  className,
}: Props) {
  const actions: Action[] = [
    { id: "insert-row-before", label: "Inserir linha acima", icon: Rows3 },
    { id: "insert-row-after", label: "Inserir linha abaixo", icon: Rows3 },
    { id: "insert-col-before", label: "Inserir coluna à esquerda", icon: Columns3 },
    { id: "insert-col-after", label: "Inserir coluna à direita", icon: Columns3 },
    { id: "delete-row", label: "Excluir linha", icon: Rows3, disabled: !canDeleteRow },
    { id: "delete-col", label: "Excluir coluna", icon: Columns3, disabled: !canDeleteCol },
    { id: "merge", label: "Mesclar", icon: TableCellsMerge, disabled: !canMerge },
    { id: "unmerge", label: "Desmesclar", icon: TableCellsSplit, disabled: !canUnmerge },
  ];

  return (
    <ul
      className={["td-chart-add-element", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Estrutura da Grade"
    >
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <li key={action.id} className="td-chart-add-element__root">
            <button
              type="button"
              role="menuitem"
              className="td-chart-add-element__root-btn"
              disabled={action.disabled}
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
