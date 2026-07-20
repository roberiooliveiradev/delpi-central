import type { ReactNode } from "react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import {
  resolveMfeHostElement,
  resolveMfePortalScopeClassName,
} from "../shape/delpiUiPortalTheme";
import { FilePreviewMetaFooter } from "./FilePreviewMetaFooter";
import { FilePreviewView } from "./FilePreviewView";
import type { FilePreviewContentState, FilePreviewLabels } from "./filePreviewTypes";
import {
  useFilePreviewLoader,
  type UseFilePreviewLoaderOptions,
} from "./useFilePreviewLoader";

export type FilePreviewModalProps = UseFilePreviewLoaderOptions & {
  open: boolean;
  title: string;
  onClose: () => void;
  labels?: Partial<FilePreviewLabels>;
  /** Estado montado pelo consumidor — ignora o hook interno quando informado. */
  previewState?: FilePreviewContentState;
  /** Chips de metadados no rodapé (tipo, tamanho, data). */
  metaItems?: Array<string | null | undefined>;
  /** Conteúdo opcional abaixo do preview (ex.: descrição da evidência). */
  afterPreview?: ReactNode;
  /** Ações extras no header (ex.: botão Baixar). */
  headerActions?: ReactNode;
  /** Callback quando o carregamento falha (exceto unsupported/empty). */
  onLoadError?: (message: string) => void;
  footer?: ReactNode;
  panelClassName?: string;
  /**
   * Classe root do MFE (ex.: `dashboard-transformometro`).
   * Se omitida, infere o ancestral `.dashboard-*` do ponto de montagem.
   */
  portalScopeClassName?: string;
  /**
   * Contém o modal na área do MFE (não cobre sidebar/chrome do portal).
   * Default: `true`. Passe `false` para overlay fullscreen no viewport.
   */
  containInHost?: boolean;
  /** Host explícito do portal (sobrescreve a resolução automática). */
  portalTarget?: Element | null;
};

const MODAL_CLASS_NAMES = {
  ...modalShellBemClasses("delpi-ui-file-preview"),
  headerActions: "delpi-ui-file-preview-modal__header-actions",
};

/** Modal genérico de pré-visualização de arquivo (blob, File ou fetch). */
export function FilePreviewModal({
  open,
  title,
  onClose,
  labels,
  previewState,
  metaItems,
  afterPreview,
  headerActions,
  onLoadError,
  footer,
  panelClassName,
  portalScopeClassName,
  containInHost = true,
  portalTarget,
  enabled,
  ...loaderOptions
}: FilePreviewModalProps) {
  const anchorRef = useRef<HTMLSpanElement | null>(null);
  const [resolvedHost, setResolvedHost] = useState<HTMLElement | null>(null);

  useLayoutEffect(() => {
    if (!open || containInHost === false) {
      setResolvedHost(null);
      return;
    }
    if (portalTarget instanceof HTMLElement) {
      setResolvedHost(portalTarget);
      return;
    }
    setResolvedHost(
      resolveMfeHostElement({
        anchor: anchorRef.current,
        portalScopeClassName,
      }),
    );
  }, [open, containInHost, portalTarget, portalScopeClassName]);

  const loadedState = useFilePreviewLoader({
    ...loaderOptions,
    enabled: open && enabled !== false && previewState == null,
  });
  const state = previewState ?? loadedState;
  const resolvedFooter =
    footer ?? (metaItems?.some((item) => item?.trim()) ? <FilePreviewMetaFooter items={metaItems} /> : null);

  useEffect(() => {
    if (!open || !onLoadError || !state.error || state.error === "empty" || state.error === "unsupported") {
      return;
    }
    onLoadError(state.error === "load_failed" ? "Erro ao carregar pré-visualização do arquivo." : state.error);
  }, [open, onLoadError, state.error]);

  const contained = containInHost !== false && Boolean(resolvedHost);
  const scopeClassName =
    portalScopeClassName ??
    resolveMfePortalScopeClassName(resolvedHost ?? anchorRef.current) ??
    undefined;

  return (
    <>
      <span ref={anchorRef} hidden aria-hidden="true" data-delpi-file-preview-anchor="" />
      <ModalShell
        open={open}
        title={title}
        onClose={onClose}
        classNames={MODAL_CLASS_NAMES}
        className={panelClassName}
        headerActions={headerActions}
        portalScopeClassName={scopeClassName}
        portalTarget={contained ? resolvedHost : undefined}
        containedInPortalTarget={contained}
      >
        <div className="delpi-ui-file-preview">
          <FilePreviewView state={state} title={title} labels={labels} />
          {afterPreview ? <div className="delpi-ui-file-preview__after">{afterPreview}</div> : null}
          {resolvedFooter ? <div className="delpi-ui-file-preview__footer">{resolvedFooter}</div> : null}
        </div>
      </ModalShell>
    </>
  );
}

export { FilePreviewView } from "./FilePreviewView";
