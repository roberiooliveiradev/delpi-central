import type { ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type AttachmentFileListItem = {
  id: string;
  fileName: string;
  detail?: string;
  busy?: boolean;
};

export type AttachmentFileListClassNames = {
  root: string;
  item: string;
  meta: string;
  name: string;
  detail: string;
  actions: string;
  empty: string;
};

export type AttachmentFileListLabels = {
  open: string;
  download: string;
  remove: string;
  empty: string;
};

export type AttachmentFileListProps = {
  items: AttachmentFileListItem[];
  onOpen?: (item: AttachmentFileListItem) => void;
  onDownload?: (item: AttachmentFileListItem) => void;
  onRemove?: (item: AttachmentFileListItem) => void;
  canRemove?: boolean;
  emptyMessage?: string;
  className?: string;
  classNames: AttachmentFileListClassNames;
  labels: AttachmentFileListLabels;
  leadingSlot?: ReactNode;
};

export function attachmentFileListBemClasses(prefix: string): AttachmentFileListClassNames {
  const block = `${prefix}-attachment-file-list`;
  const ui = "delpi-ui-attachment-file-list";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(block, ui),
    item: pair(`${block}__item`, `${ui}__item`),
    meta: pair(`${block}__meta`, `${ui}__meta`),
    name: pair(`${block}__name`, `${ui}__name`),
    detail: pair(`${block}__detail`, `${ui}__detail`),
    actions: pair(`${block}__actions`, `${ui}__actions`),
    empty: pair(`${block}__empty`, `${ui}__empty`),
  };
}

export function AttachmentFileList({
  items,
  onOpen,
  onDownload,
  onRemove,
  canRemove = Boolean(onRemove),
  emptyMessage,
  className,
  classNames,
  labels,
  leadingSlot,
}: AttachmentFileListProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      {leadingSlot}
      {items.length === 0 ? (
        <p className={classNames.empty}>{emptyMessage ?? labels.empty}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.id} className={classNames.item}>
              <div className={classNames.meta}>
                {onOpen ? (
                  <button
                    type="button"
                    className={classNames.name}
                    disabled={item.busy}
                    onClick={() => onOpen(item)}
                  >
                    {item.fileName}
                  </button>
                ) : (
                  <p className={classNames.name}>{item.fileName}</p>
                )}
                {item.detail ? <p className={classNames.detail}>{item.detail}</p> : null}
              </div>
              <div className={classNames.actions}>
                {onOpen ? (
                  <ActionButton
                    variant="ghost"
                    disabled={item.busy}
                    onClick={() => onOpen(item)}
                  >
                    {labels.open}
                  </ActionButton>
                ) : null}
                {onDownload ? (
                  <ActionButton
                    variant="ghost"
                    disabled={item.busy}
                    onClick={() => onDownload(item)}
                  >
                    {labels.download}
                  </ActionButton>
                ) : null}
                {canRemove && onRemove ? (
                  <ActionButton
                    variant="ghost"
                    disabled={item.busy}
                    onClick={() => onRemove(item)}
                  >
                    {labels.remove}
                  </ActionButton>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export type DashboardAttachmentFileListProps = Omit<
  AttachmentFileListProps,
  "classNames" | "labels"
> & {
  labels?: Partial<AttachmentFileListLabels>;
};

export function createDashboardAttachmentFileList(config: {
  classNames: AttachmentFileListClassNames;
  labels: AttachmentFileListLabels;
}) {
  return function DashboardAttachmentFileList(props: DashboardAttachmentFileListProps) {
    const { labels: labelOverrides, ...rest } = props;
    return (
      <AttachmentFileList
        classNames={config.classNames}
        labels={{ ...config.labels, ...labelOverrides }}
        {...rest}
      />
    );
  };
}
