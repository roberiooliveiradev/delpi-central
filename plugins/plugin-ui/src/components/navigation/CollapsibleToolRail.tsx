import { ChevronDown, ChevronRight, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useState, type ReactNode } from "react";

export type ToolRailItem = {
  id: string;
  label: string;
  icon: ReactNode;
  description?: string;
  statusText?: string;
  disabled?: boolean;
};

export type ToolRailGroup = {
  id: string;
  label?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  items: readonly ToolRailItem[];
};

export type CollapsibleToolRailProps = {
  groups: readonly ToolRailGroup[];
  activeId?: string;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onSelect: (id: string) => void;
  ariaLabel: string;
  expandLabel?: string;
  collapseLabel?: string;
  className?: string;
};

function ToolRailGroupView({
  group, expanded, activeId, onSelect,
}: {
  group: ToolRailGroup;
  expanded: boolean;
  activeId?: string;
  onSelect: (id: string) => void;
}) {
  const [groupOpen, setGroupOpen] = useState(group.defaultOpen ?? !group.collapsible);
  const isOpen = !group.collapsible || groupOpen;
  return (
    <div className="delpi-ui-tool-rail__group" data-group={group.id}>
      {group.label && expanded && (
        group.collapsible ? (
          <button
            type="button"
            className="delpi-ui-tool-rail__group-toggle"
            aria-expanded={isOpen}
            onClick={() => setGroupOpen(value => !value)}
          >
            <span>{group.label}</span>
            {isOpen ? <ChevronDown size={15} aria-hidden="true" /> : <ChevronRight size={15} aria-hidden="true" />}
          </button>
        ) : (
          <span className="delpi-ui-tool-rail__group-label">{group.label}</span>
        )
      )}
      {isOpen && (
        <div className="delpi-ui-tool-rail__items">
          {group.items.map(item => (
            <button
              key={item.id}
              type="button"
              className="delpi-ui-tool-rail__item"
              data-active={activeId === item.id ? "true" : undefined}
              aria-pressed={activeId === item.id}
              aria-label={item.label}
              title={[item.label, item.statusText].filter(Boolean).join(" — ")}
              disabled={item.disabled}
              onClick={() => { if (!item.disabled) onSelect(item.id); }}
            >
              <span className="delpi-ui-tool-rail__icon" aria-hidden="true">{item.icon}</span>
              {expanded && (
                <span className="delpi-ui-tool-rail__copy">
                  <span className="delpi-ui-tool-rail__name">{item.label}</span>
                  {item.statusText && <span className="delpi-ui-tool-rail__status">{item.statusText}</span>}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Presentation-only, controlled secondary navigation rail.
 * No domain methods, RBAC, persistence or routing inside Plugin UI.
 */
export function CollapsibleToolRail({
  groups, activeId, expanded, onExpandedChange, onSelect, ariaLabel,
  expandLabel = "Expandir ferramentas", collapseLabel = "Recolher ferramentas", className,
}: CollapsibleToolRailProps) {
  return (
    <nav
      className={["delpi-ui-tool-rail", className].filter(Boolean).join(" ")}
      data-expanded={expanded ? "true" : "false"}
      aria-label={ariaLabel}
    >
      <div className="delpi-ui-tool-rail__header">
        {expanded && <span className="delpi-ui-tool-rail__heading">{ariaLabel}</span>}
        <button
          type="button"
          className="delpi-ui-tool-rail__collapse"
          aria-label={expanded ? collapseLabel : expandLabel}
          aria-expanded={expanded}
          onClick={() => onExpandedChange(!expanded)}
        >
          {expanded ? <PanelLeftClose size={18} aria-hidden="true" /> : <PanelLeftOpen size={18} aria-hidden="true" />}
        </button>
      </div>
      {groups.map(group => (
        <ToolRailGroupView
          key={group.id}
          group={group}
          expanded={expanded}
          activeId={activeId}
          onSelect={onSelect}
        />
      ))}
    </nav>
  );
}
