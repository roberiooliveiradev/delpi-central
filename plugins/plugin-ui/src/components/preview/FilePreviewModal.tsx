import type { ReactNode } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import { FilePreviewView } from "./FilePreviewView";
import type { FilePreviewLabels } from "./filePreviewTypes";
import {
  useFilePreviewLoader,
  type UseFilePreviewLoaderOptions,
} from "./useFilePreviewLoader";

export type FilePreviewModalProps = UseFilePreviewLoaderOptions & {
  open: boolean;
  title: string;
  onClose: () => void;
  labels?: Partial<FilePreviewLabels>;
  footer?: ReactNode;
  panelClassName?: string;
};

const MODAL_CLASS_NAMES = modalShellBemClasses("delpi-ui-file-preview-modal");

/** Modal genérico de pré-visualização de arquivo (blob, File ou fetch). */
export function FilePreviewModal({
  open,
  title,
  onClose,
  labels,
  footer,
  panelClassName,
  enabled,
  ...loaderOptions
}: FilePreviewModalProps) {
  const state = useFilePreviewLoader({
    ...loaderOptions,
    enabled: open && enabled !== false,
  });

  return (
    <ModalShell
      open={open}
      title={title}
      onClose={onClose}
      classNames={MODAL_CLASS_NAMES}
      className={panelClassName}
    >
      <div className="delpi-ui-file-preview">
        <FilePreviewView state={state} title={title} labels={labels} footer={footer} />
      </div>
    </ModalShell>
  );
}

export { FilePreviewView } from "./FilePreviewView";
