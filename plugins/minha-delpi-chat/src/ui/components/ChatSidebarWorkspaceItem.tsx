import type { LucideIcon } from "lucide-react";

import "./ChatSidebarWorkspaceItem.css";

type ChatSidebarWorkspaceItemProps = {
  icon: LucideIcon;
  title: string;
  subtitle?: string | null;
  active?: boolean;
  badge?: string | null;
  onClick?: () => void;
};

export function ChatSidebarWorkspaceItem({
  icon: Icon,
  title,
  subtitle,
  active,
  badge,
  onClick,
}: ChatSidebarWorkspaceItemProps) {
  return (
    <button
      type="button"
      className={
        active
          ? "mdc-sidebar-workspace-item mdc-sidebar-workspace-item--active"
          : "mdc-sidebar-workspace-item"
      }
      onClick={onClick}
      title={subtitle || title}
    >
      <span className="mdc-sidebar-workspace-item__icon">
        <Icon size={15} aria-hidden="true" />
      </span>

      <span className="mdc-sidebar-workspace-item__content">
        <strong>{title}</strong>
        {subtitle ? <small>{subtitle}</small> : null}
      </span>

      {badge ? <em>{badge}</em> : null}
    </button>
  );
}
