import { useRef, useState, type ReactNode } from "react";
import {
  AnchoredPanelPortal,
  HelpTooltip,
  IconButton,
} from "@delpi/plugin-ui/index";
import { Settings2 } from "lucide-react";

export type ComposerSettingsMenuProps = {
  /**
   * Seções do menu, por composição — hoje `DictationModeSettings`;
   * futuras seções entram como novos filhos sem alterar o menu (CS-18).
   * Uma seção que pede fechamento após escolha marca o contêiner com
   * `data-close-on-change` (contrato mínimo, opt-in por seção).
   */
  children: ReactNode;
};

const TRIGGER_LABEL = "Configurações do campo de pergunta";

/**
 * Botão discreto na barra de ações do composer que abre o menu
 * "Configurações do campo de pergunta" — painel flutuante clean
 * (popover ancorado, Escape/fora fecha, foco devolvido ao trigger).
 * Não conhece STT, draft nem backend.
 */
export function ComposerSettingsMenu({ children }: ComposerSettingsMenuProps) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLSpanElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const dismiss = () => {
    setOpen(false);
    anchorRef.current
      ?.querySelector<HTMLButtonElement>("button")
      ?.focus();
  };

  return (
    <span className="delia-composer-settings" ref={anchorRef}>
      <HelpTooltip wrap content={TRIGGER_LABEL}>
        <IconButton
          type="button"
          className={
            open
              ? "delia-composer-settings__trigger delia-composer-settings__trigger--open"
              : "delia-composer-settings__trigger"
          }
          aria-label={TRIGGER_LABEL}
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
        >
          <Settings2 size={16} strokeWidth={1.8} />
        </IconButton>
      </HelpTooltip>
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        className="delia-composer-settings__panel"
        role="dialog"
        aria-label={TRIGGER_LABEL}
        preferredPlacement="top"
        horizontalAlign="start"
        onDismiss={dismiss}
      >
        <div className="delia-composer-settings__header">
          <span className="delia-composer-settings__title">
            Configurações
          </span>
          <span className="delia-composer-settings__subtitle">
            Campo de pergunta
          </span>
        </div>
        <div
          onChange={(event) => {
            if (
              event.target instanceof HTMLElement &&
              event.target.closest("[data-close-on-change]")
            ) {
              dismiss();
            }
          }}
        >
          {children}
        </div>
      </AnchoredPanelPortal>
    </span>
  );
}
