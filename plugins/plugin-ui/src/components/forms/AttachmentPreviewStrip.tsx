import { FileText, FileImage, File } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";

export type AttachmentPreviewStripItem = {
  id: string;
  fileName: string;
  contentType?: string | null;
  /** URL de objeto/blob para imagem; omitido = ícone por tipo. */
  previewUrl?: string | null;
  detail?: string;
};

export type AttachmentPreviewStripClassNames = {
  root: string;
  label: string;
  empty: string;
  track: string;
  item: string;
  thumb: string;
  caption: string;
};

export type AttachmentPreviewStripLabels = {
  empty: string;
  openAriaLabel: (fileName: string) => string;
};

export type AttachmentPreviewStripProps = {
  items: AttachmentPreviewStripItem[];
  onOpen: (item: AttachmentPreviewStripItem) => void;
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
    item: pair(`${block}__item`, `${ui}__item`),
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
  heading,
  emptyMessage,
  className,
  classNames,
  labels,
}: AttachmentPreviewStripProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      {heading != null ? <p className={classNames.label}>{heading}</p> : null}
      {items.length === 0 ? (
        <p className={classNames.empty}>{emptyMessage ?? labels.empty}</p>
      ) : (
        <div className={classNames.track} role="list">
          {items.map((item) => (
            <div key={item.id} role="listitem">
              <button
                type="button"
                className={classNames.item}
                aria-label={labels.openAriaLabel(item.fileName)}
                title={item.detail ? `${item.fileName} · ${item.detail}` : item.fileName}
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
