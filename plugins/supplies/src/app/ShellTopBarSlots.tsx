import { HelpTooltip } from "@delpi/plugin-ui/index";

import { SP_HELP } from "../content/helpTooltips";
import { SHELL_NAV_CONTENT } from "../content/shellNav";
import { SuppliesTopBarSearchTrigger } from "./suppliesUi";

type ShellTopBarSecondaryProps = {
  onOpenPalette: () => void;
};

/** Slot secondary — busca Ctrl+K (kit), igual Comercial. */
export function ShellTopBarSecondary({ onOpenPalette }: ShellTopBarSecondaryProps) {
  return (
    <div className="sp-shell-secondary">
      <SuppliesTopBarSearchTrigger
        onOpen={onOpenPalette}
        label={SHELL_NAV_CONTENT.searchLabel}
        shortcutLabel={SHELL_NAV_CONTENT.searchShortcutLabel}
        aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
        title={SHELL_NAV_CONTENT.searchTitle}
      />
    </div>
  );
}

/**
 * Slot actions — hint de coexistência apenas.
 * Ajuda fica só na nav (padrão Comercial; sem CTA duplicado).
 */
export function ShellTopBarActions() {
  return (
    <div className="sp-shell-actions">
      <HelpTooltip content={SP_HELP.coexistence} ariaLabel="Ajuda: Portal vs apps antigos" />
    </div>
  );
}
