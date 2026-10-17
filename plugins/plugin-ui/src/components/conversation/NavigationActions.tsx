import { PanelLeftClose, PanelLeftOpen, Settings2, SquarePen } from "lucide-react";
import { IconButton } from "../actions/IconButton";

export type NavigationActionsProps =
  | {
      action: "toggle";
      expanded: boolean;
      onAction: () => void;
      label?: string;
      className?: string;
    }
  | {
      action: "new" | "options";
      collapsed?: boolean;
      onAction?: () => void;
      className?: string;
    };

/**
 * Presentation-only navigation controls, extracted from the existing shell
 * and sidebar. Callback presence is a UI gate, never a backend authorization.
 * Search stays owned by the existing ConversationSidebarSearch.
 */
export function NavigationActions(props: NavigationActionsProps) {
  if (props.action === "toggle") {
    const { expanded, onAction, className, label = "conversas" } = props;
    return (
      <IconButton
        className={["delpi-ui-conversation-three-region__rail-toggle", "delpi-ui-conversation-three-region__chrome-icon", className].filter(Boolean).join(" ")}
        aria-label={expanded ? `Recolher ${label}` : `Expandir ${label}`}
        aria-expanded={expanded}
        onClick={onAction}
      >
        {expanded
          ? <PanelLeftClose size={19} strokeWidth={1.8} aria-hidden="true" />
          : <PanelLeftOpen size={19} strokeWidth={1.8} aria-hidden="true" />}
      </IconButton>
    );
  }

  const { action, collapsed = false, onAction, className } = props;
  const isNew = action === "new";
  const label = isNew ? "Nova conversa" : "Opções";
  return (
    <button
      type="button"
      className={["delpi-ui-conversation-sidebar__action", isNew ? "delpi-ui-conversation-sidebar__action--primary" : null, className].filter(Boolean).join(" ")}
      disabled={!onAction}
      onClick={onAction}
      aria-label={label}
      title={!onAction ? isNew ? "Disponível após integração das sessões" : "Opções de conversa ainda indisponíveis" : collapsed ? label : undefined}
    >
      {isNew ? <SquarePen size={17} aria-hidden="true" /> : <Settings2 size={17} aria-hidden="true" />}
      {!collapsed ? <span>{label}</span> : null}
    </button>
  );
}
