import type { LucideIcon } from "lucide-react";

import { handleChatNavClick } from "../../navigation/chatNavigation";

import "./ChatSidebarWorkspaceItem.css";

type ChatSidebarWorkspaceItemProps = {
  icon: LucideIcon;
  title: string;
  subtitle?: string | null;
  active?: boolean;
  badge?: string | null;
  href?: string;
  onClick?: () => void;
};

export function ChatSidebarWorkspaceItem({
  icon: Icon,
  title,
  subtitle,
  active,
  badge,
  href,
  onClick,
}: ChatSidebarWorkspaceItemProps) {
  const className = active
    ? "mdc-sidebar-workspace-item mdc-sidebar-workspace-item--active"
    : "mdc-sidebar-workspace-item";

  const content = (
    <>
      <span className="mdc-sidebar-workspace-item__icon">
        <Icon size={15} aria-hidden="true" />
      </span>

      <span className="mdc-sidebar-workspace-item__content">
        <strong>{title}</strong>
        {subtitle ? <small>{subtitle}</small> : null}
      </span>

      {badge ? <em>{badge}</em> : null}
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        className={className}
        onClick={(event) => {
          handleChatNavClick(event, href, { onNavigate: onClick });
        }}
        title={subtitle || title}
      >
        {content}
      </a>
    );
  }

  return (
    <button type="button" className={className} onClick={onClick} title={subtitle || title}>
      {content}
    </button>
  );
}
