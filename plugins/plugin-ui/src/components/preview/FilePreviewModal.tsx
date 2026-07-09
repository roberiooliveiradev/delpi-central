import type { ReactNode } from "react";
import { useEffect } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
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
  enabled,
  ...loaderOptions
}: FilePreviewModalProps) {
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

  return (
    <ModalShell
      open={open}
      title={title}
      onClose={onClose}
      classNames={MODAL_CLASS_NAMES}
      className={panelClassName}
      headerActions={headerActions}
    >
      <div className="delpi-ui-file-preview">
        <FilePreviewView state={state} title={title} labels={labels} />
        {afterPreview ? <div className="delpi-ui-file-preview__after">{afterPreview}</div> : null}
        {resolvedFooter ? <div className="delpi-ui-file-preview__footer">{resolvedFooter}</div> : null}
      </div>
    </ModalShell>
  );
}

export { FilePreviewView } from "./FilePreviewView";
