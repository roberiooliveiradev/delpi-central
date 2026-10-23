import { useMemo, useRef, useState, type ReactNode } from "react";
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
   * Seleções dentro do menu aplicam imediatamente e não o fecham;
   * o painel só fecha por saída explícita (trigger, Escape, clique
   * externo) — spec 125 §10.
   */
  children: ReactNode;
  /**
   * `open` é controlado pelo host porque trocar o modo de ditado troca
   * a sub-árvore do composer (batch ⇄ live), remontando este menu —
   * estado local não sobreviveria à seleção.
   */
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const TRIGGER_LABEL = "Configurações do campo de pergunta";

/**
 * Botão discreto na barra de ações do composer que abre o menu
 * "Configurações do campo de pergunta" — painel flutuante clean
 * (popover ancorado, Escape/fora fecha, foco devolvido ao trigger).
 * Não conhece STT, draft nem backend.
 */
export function ComposerSettingsMenu({
  children,
  open,
  onOpenChange,
}: ComposerSettingsMenuProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  /*
   * Callback ref + estado (não useRef): quando o menu nasce já aberto —
   * remount ao trocar o modo de ditado — o ref da âncora ainda não está
   * anexado quando o layout effect de posição do portal roda. O estado
   * re-renderiza assim que o elemento materializa e o efeito reposiciona.
   */
  const [anchorEl, setAnchorEl] = useState<HTMLSpanElement | null>(null);
  const portalAnchorRef = useMemo(
    () => ({ current: anchorEl }),
    [anchorEl],
  );

  const dismiss = () => {
    onOpenChange(false);
    if (panelRef.current?.contains(document.activeElement)) {
      anchorEl
        ?.querySelector<HTMLButtonElement>("button")
        ?.focus();
    }
  };

  return (
    <span className="delia-composer-settings" ref={setAnchorEl}>
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
          onClick={() => onOpenChange(!open)}
        >
          <Settings2 size={16} strokeWidth={1.8} />
        </IconButton>
      </HelpTooltip>
      <AnchoredPanelPortal
        open={open}
        anchorRef={portalAnchorRef}
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
        {children}
      </AnchoredPanelPortal>
    </span>
  );
}
