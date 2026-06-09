import { PanelLeftOpen } from "lucide-react";
import { expandPortalSidebar } from "../lib/portalShell";

type Props = {
  visible: boolean;
  onExpanded?: () => void;
};

export function PortalSidebarTrigger({ visible, onExpanded }: Props) {
  if (!visible) return null;

  return (
    <button
      type="button"
      className="adc-portal-sidebar-trigger"
      aria-label="Abrir menu lateral do portal"
      title="Abrir menu do portal"
      onClick={() => {
        expandPortalSidebar();
        onExpanded?.();
      }}
    >
      <PanelLeftOpen size={18} />
      <span>Menu</span>
    </button>
  );
}
