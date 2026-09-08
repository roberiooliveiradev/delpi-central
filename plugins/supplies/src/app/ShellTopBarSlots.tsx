import { BookOpen, Search } from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { SP_HELP } from "../content/helpTooltips";
import { SHELL_NAV_CONTENT } from "../content/shellNav";
import { navigatePluginView } from "./pluginNavigation";

type ShellTopBarSecondaryProps = {
  onOpenPalette: () => void;
};

/** Slot secondary da TopBar — busca Ctrl+K (análogo aos favoritos no Comercial). */
export function ShellTopBarSecondary({ onOpenPalette }: ShellTopBarSecondaryProps) {
  return (
    <div className="sp-shell-secondary">
      <button
        type="button"
        className="sp-shell-secondary__search"
        onClick={onOpenPalette}
        aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
        title={SHELL_NAV_CONTENT.searchTitle}
      >
        <Search size={16} strokeWidth={1.75} aria-hidden="true" />
        <span className="sp-shell-secondary__search-label">{SHELL_NAV_CONTENT.searchLabel}</span>
        <kbd className="sp-shell-secondary__kbd">Ctrl+K</kbd>
      </button>
    </div>
  );
}

type ShellTopBarActionsProps = {
  basePath: string;
};

/** Slot actions da TopBar — Ajuda + hint de coexistência (padrão Comercial: ações à direita). */
export function ShellTopBarActions({ basePath }: ShellTopBarActionsProps) {
  return (
    <div className="sp-shell-actions">
      <button
        type="button"
        className="sp-shell-actions__help"
        onClick={() => navigatePluginView("help", { basePath })}
        aria-label={SHELL_NAV_CONTENT.helpActionAriaLabel}
      >
        <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
        <span>{SHELL_NAV_CONTENT.helpActionLabel}</span>
      </button>
      <HelpTooltip content={SP_HELP.coexistence} ariaLabel="Ajuda: Portal vs apps antigos" />
    </div>
  );
}
