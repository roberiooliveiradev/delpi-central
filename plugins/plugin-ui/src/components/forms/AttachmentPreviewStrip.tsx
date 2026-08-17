import { FileText, FileImage, File, X } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";

export type AttachmentPreviewStripMode = "preview" | "manage";

export type AttachmentPreviewStripItem = {
  id: string;
  fileName: string;
  contentType?: string | null;
  /** URL de objeto/blob para imagem; omitido = ícone por tipo. */
  previewUrl?: string | null;
  detail?: string;
  busy?: boolean;
};

export type AttachmentPreviewStripClassNames = {
  root: string;
  label: string;
  empty: string;
  track: string;
  itemFrame: string;
  item: string;
  remove: string;
  thumb: string;
  caption: string;
};

export type AttachmentPreviewStripLabels = {
  empty: string;
  openAriaLabel: (fileName: string) => string;
  removeAriaLabel: (fileName: string) => string;
};

export type AttachmentPreviewStripProps = {
  items: AttachmentPreviewStripItem[];
  onOpen: (item: AttachmentPreviewStripItem) => void;
  /** preview = só abrir; manage = thumb + botão remover. Default: preview. */
  mode?: AttachmentPreviewStripMode;
  onRemove?: (item: AttachmentPreviewStripItem) => void;
  heading?: ReactNode;
  emptyMessage?: string;
  className?: string;
  classNames: AttachmentPreviewStripClassNames;
  labels: AttachmentPreviewStripLabels;
};

export function attachmentPreviewStripBemClasses(
  prefix: string,
): AttachmentPreviewStripClassNames {
  const block = `${prefix}-attachment-preview-strip`;
  const ui = "delpi-ui-attachment-preview-strip";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(block, ui),
    label: pair(`${block}__label`, `${ui}__label`),
    empty: pair(`${block}__empty`, `${ui}__empty`),
    track: pair(`${block}__track`, `${ui}__track`),
    itemFrame: pair(`${block}__item-frame`, `${ui}__item-frame`),
    item: pair(`${block}__item`, `${ui}__item`),
    remove: pair(`${block}__remove`, `${ui}__remove`),
    thumb: pair(`${block}__thumb`, `${ui}__thumb`),
    caption: pair(`${block}__caption`, `${ui}__caption`),
  };
}

function ThumbIcon({ fileName, contentType }: { fileName: string; contentType?: string | null }) {
  const kind = resolveFilePreviewKind({ fileName, mimeType: contentType });
  if (kind === "image") return <FileImage size={28} aria-hidden />;
  if (kind === "pdf" || kind === "text" || kind === "docx") {
    return <FileText size={28} aria-hidden />;
  }
  return <File size={28} aria-hidden />;
}

export function AttachmentPreviewStrip({
  items,
  onOpen,
  mode = "preview",
  onRemove,
  heading,
  emptyMessage,
  className,
  classNames,
  labels,
}: AttachmentPreviewStripProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const canRemove = mode === "manage" && Boolean(onRemove);

  return (
    <div className={rootClass} data-mode={mode}>
      {heading != null ? <p className={classNames.label}>{heading}</p> : null}
      {items.length === 0 ? (
        <p className={classNames.empty}>{emptyMessage ?? labels.empty}</p>
      ) : (
        <div className={classNames.track} role="list">
          {items.map((item) => (
            <div key={item.id} className={classNames.itemFrame} role="listitem">
              <button
                type="button"
                className={classNames.item}
                aria-label={labels.openAriaLabel(item.fileName)}
                title={item.detail ? `${item.fileName} · ${item.detail}` : item.fileName}
                disabled={item.busy}
                onClick={() => onOpen(item)}
              >
                <span className={classNames.thumb}>
                  {item.previewUrl ? (
                    <img src={item.previewUrl} alt="" />
                  ) : (
                    <ThumbIcon fileName={item.fileName} contentType={item.contentType} />
                  )}
                </span>
                <span className={classNames.caption}>{item.fileName}</span>
              </button>
              {canRemove && onRemove ? (
                <button
                  type="button"
                  className={classNames.remove}
                  aria-label={labels.removeAriaLabel(item.fileName)}
                  title={labels.removeAriaLabel(item.fileName)}
                  disabled={item.busy}
                  onClick={(event) => {
                    event.stopPropagation();
                    onRemove(item);
                  }}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export type DashboardAttachmentPreviewStripProps = Omit<
  AttachmentPreviewStripProps,
  "classNames" | "labels"
> & {
  labels?: Partial<AttachmentPreviewStripLabels>;
};

export function createDashboardAttachmentPreviewStrip(config: {
  classNames: AttachmentPreviewStripClassNames;
  labels: AttachmentPreviewStripLabels;
}) {
  return function DashboardAttachmentPreviewStrip(
    props: DashboardAttachmentPreviewStripProps,
  ) {
    const { labels: labelOverrides, ...rest } = props;
    return (
      <AttachmentPreviewStrip
        classNames={config.classNames}
        labels={{ ...config.labels, ...labelOverrides }}
        {...rest}
      />
    );
  };
}
