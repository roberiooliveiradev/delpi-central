import { Bot, Blocks, FolderKanban, MessagesSquare } from "lucide-react";
import type { ReactNode } from "react";

export type NavigationRailCategory = "conversations" | "projects" | "agents" | "plugins";

export type NavigationRailProps = {
  activeCategory?: NavigationRailCategory;
  /** A callback means UI navigation is available, NOT backend authorization. */
  onSelectCategory?: (category: NavigationRailCategory) => void;
  /** Only approved visible entries may be enabled by their owner/consumer. */
  availableCategories?: readonly NavigationRailCategory[];
  className?: string;
};

const CATEGORIES: readonly {
  id: NavigationRailCategory;
  label: string;
  icon: ReactNode;
}[] = [
  { id: "conversations", label: "Conversas", icon: <MessagesSquare size={19} strokeWidth={1.8} aria-hidden="true" /> },
  { id: "projects", label: "Projetos", icon: <FolderKanban size={19} strokeWidth={1.8} aria-hidden="true" /> },
  { id: "agents", label: "Agentes", icon: <Bot size={19} strokeWidth={1.8} aria-hidden="true" /> },
  { id: "plugins", label: "Plugins", icon: <Blocks size={19} strokeWidth={1.8} aria-hidden="true" /> },
];

/**
 * Render-only category rail. The surrounding shell owns its expand/collapse
 * toggle and its single navigation landmark. No sessions, catalog, API or ACT.
 */
export function NavigationRail({
  activeCategory = "conversations",
  onSelectCategory,
  availableCategories = [],
  className,
}: NavigationRailProps) {
  return (
    <div className={["delpi-ui-navigation-rail", className].filter(Boolean).join(" ")} aria-label="Categorias da DÉLIA">
      {CATEGORIES.map(({ id, label, icon }) => {
        const enabled = !!onSelectCategory && availableCategories.includes(id);
        return (
          <button
            key={id}
            type="button"
            className="delpi-ui-navigation-rail__item"
            aria-label={label}
            title={enabled ? label : `${label} — indisponível`}
            aria-current={activeCategory === id ? "page" : undefined}
            disabled={!enabled}
            onClick={() => onSelectCategory?.(id)}
          >
            {icon}
          </button>
        );
      })}
    </div>
  );
}
