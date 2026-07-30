import { Columns3, Database } from "lucide-react";

export type TableDataMenuActionId = "source" | "columns";

type Props = {
  onSelect: (actionId: TableDataMenuActionId) => void;
  className?: string;
};

const ACTIONS: Array<{
  id: TableDataMenuActionId;
  label: string;
  icon: typeof Database;
}> = [
  { id: "source", label: "Selecionar fonte…", icon: Database },
  { id: "columns", label: "Colunas do visual…", icon: Columns3 },
];

/**
 * Menu de dados da tabela — ícone + rótulo (ribbon + float funil).
 * Mesmo chrome visual do «Adicionar elemento» (lista cascata).
 */
export function TableDataMenu({ onSelect, className }: Props) {
  return (
    <ul
      className={["td-chart-add-element", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Dados da tabela"
    >
      {ACTIONS.map((action) => {
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
