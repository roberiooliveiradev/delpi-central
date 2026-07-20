import { Maximize2, Minimize2 } from "lucide-react";
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

import { withBemModifier } from "../../utils/delpiUiClass";
import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import { HelpTooltip } from "../help/HelpTooltip";
import {
  resolveMfeHostElement,
  resolveMfePortalScopeClassName,
} from "../shape/delpiUiPortalTheme";
import { DiagramLayoutProvider } from "./DiagramLayoutContext";

export type DiagramFullscreenFrameLabels = {
  expand?: string;
  exit?: string;
  expandHint?: string;
  closeAriaLabel?: string;
};

export type DiagramFullscreenFrameProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  /** Quando false, não mostra o botão de tela cheia. */
  enabled?: boolean;
  /**
   * Classe root do MFE (ex.: `dashboard-transformometro`).
   * Se omitida, infere o ancestral `.dashboard-*` do ponto de montagem.
   */
  portalScopeClassName?: string;
  /**
   * Contém o modal na área do MFE (não cobre sidebar/chrome do portal).
   * Default: `true`. Passe `false` para overlay no viewport.
   */
  containInHost?: boolean;
  labels?: DiagramFullscreenFrameLabels;
};

const MODAL_CLASS_NAMES = {
  ...modalShellBemClasses("delpi-ui-diagram"),
};

const DEFAULT_LABELS = {
  expand: "Tela cheia",
  exit: "Sair da tela cheia",
  expandHint:
    "Abre o editor em tela cheia com paleta, ferramentas e ações. Pressione Esc ou use «Sair da tela cheia» para voltar.",
  closeAriaLabel: "Fechar tela cheia",
} as const;

const GHOST_BTN = "delpi-ui-ghost-btn";

/**
 * Área de trabalho do diagrama com botão «Tela cheia» que abre o conteúdo
 * em {@link ModalShell} (padrão FilePreview — contido no host MFE).
 */
export function DiagramFullscreenFrame({
  title,
  subtitle,
  children,
  enabled = true,
  portalScopeClassName,
  containInHost = true,
  labels,
}: DiagramFullscreenFrameProps) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLSpanElement | null>(null);
  const [resolvedHost, setResolvedHost] = useState<HTMLElement | null>(null);

  const resolvedLabels = { ...DEFAULT_LABELS, ...labels };
  const contained = containInHost !== false && Boolean(resolvedHost);
  const scopeClassName =
    portalScopeClassName ??
    resolveMfePortalScopeClassName(resolvedHost ?? anchorRef.current) ??
    undefined;

  useLayoutEffect(() => {
    if (!open || containInHost === false) {
      setResolvedHost(null);
      return;
    }
    setResolvedHost(
      resolveMfeHostElement({
        anchor: anchorRef.current,
        portalScopeClassName,
      }),
    );
  }, [open, containInHost, portalScopeClassName]);

  const exit = () => setOpen(false);
  const enter = () => setOpen(true);

  return (
    <>
      <span ref={anchorRef} hidden aria-hidden="true" data-delpi-diagram-fullscreen-anchor="" />
      <DiagramLayoutProvider layout="default">
        <div className="tm-diagram-workspace">
          {enabled && !open ? (
            <div className="tm-diagram-workspace__expand-row">
              <HelpTooltip
                content={resolvedLabels.expandHint}
                ariaLabel="Ajuda: tela cheia do diagrama"
                wrap
                placement="bottom"
              >
                <button
                  type="button"
                  className={`${GHOST_BTN} tm-diagram-workspace__expand-btn`}
                  onClick={enter}
                >
                  <Maximize2 size={16} aria-hidden />
                  {resolvedLabels.expand}
                </button>
              </HelpTooltip>
            </div>
          ) : null}

          {!open ? <div className="tm-diagram-workspace__body">{children}</div> : null}
        </div>
      </DiagramLayoutProvider>

      <ModalShell
        open={open}
        title={title}
        description={subtitle}
        onClose={exit}
        classNames={MODAL_CLASS_NAMES}
        className={
          contained
            ? "delpi-ui-diagram-modal"
            : `${withBemModifier("delpi-ui-modal", "page")} delpi-ui-diagram-modal`
        }
        closeAriaLabel={resolvedLabels.closeAriaLabel}
        headerActions={
          <button type="button" className={GHOST_BTN} onClick={exit}>
            <Minimize2 size={16} aria-hidden />
            {resolvedLabels.exit}
          </button>
        }
        portalScopeClassName={scopeClassName}
        portalTarget={contained ? resolvedHost : undefined}
        containedInPortalTarget={contained}
      >
        <DiagramLayoutProvider layout="fill">
          <div className="tm-diagram-workspace tm-diagram-workspace--modal-body">{children}</div>
        </DiagramLayoutProvider>
      </ModalShell>
    </>
  );
}
