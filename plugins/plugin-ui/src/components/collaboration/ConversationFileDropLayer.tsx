import { useState, type DragEvent, type ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export const CONVERSATION_FILE_DROP_MAX_BYTES = 20 * 1024 * 1024;

export type ConversationFileDropLayerClassNames = {
  root: string;
  overlay: string;
};

export type ConversationFileDropLayerProps = {
  children: ReactNode;
  classNames: ConversationFileDropLayerClassNames;
  overlayLabel: string;
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  maxBytes?: number;
  accept?: string;
  className?: string;
};

export function conversationFileDropLayerBemClasses(
  prefix: string,
): ConversationFileDropLayerClassNames {
  const base = `${prefix}-conversation-drop`;
  const ui = "delpi-ui-conversation-drop";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    overlay: pair(`${base}__overlay`, `${ui}__overlay`),
  };
}

function matchesAccept(file: File, accept: string | undefined): boolean {
  const raw = (accept ?? "").trim();
  if (!raw) return true;
  const tokens = raw.split(",").map((token) => token.trim().toLowerCase()).filter(Boolean);
  const name = file.name.toLowerCase();
  const type = (file.type || "").toLowerCase();
  return tokens.some((token) => {
    if (token.endsWith("/*")) {
      return type.startsWith(token.slice(0, -1));
    }
    if (token.startsWith(".")) {
      return name.endsWith(token);
    }
    return type === token;
  });
}

export function ConversationFileDropLayer({
  children,
  classNames,
  overlayLabel,
  onFiles,
  disabled = false,
  maxBytes = CONVERSATION_FILE_DROP_MAX_BYTES,
  accept,
  className,
}: ConversationFileDropLayerProps) {
  const [active, setActive] = useState(false);
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  const onDragOver = (event: DragEvent<HTMLDivElement>) => {
    if (disabled) return;
    event.preventDefault();
    setActive(true);
  };

  const onDragLeave = (event: DragEvent<HTMLDivElement>) => {
    if (event.currentTarget.contains(event.relatedTarget as Node)) return;
    setActive(false);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setActive(false);
    if (disabled) return;
    const files = Array.from(event.dataTransfer.files ?? []).filter(
      (file) => file.size <= maxBytes && matchesAccept(file, accept),
    );
    if (files.length) onFiles(files);
  };

  return (
    <div
      className={rootClass}
      onDragOver={onDragOver}
      onDragEnter={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {children}
      {active ? (
        <div className={classNames.overlay} role="status">
          {overlayLabel}
        </div>
      ) : null}
    </div>
  );
}

export type DashboardConversationFileDropLayerProps = Omit<
  ConversationFileDropLayerProps,
  "classNames"
>;

export function createDashboardConversationFileDropLayer(prefix: string) {
  const classNames = conversationFileDropLayerBemClasses(prefix);
  return function DashboardConversationFileDropLayer(
    props: DashboardConversationFileDropLayerProps,
  ) {
    return <ConversationFileDropLayer classNames={classNames} {...props} />;
  };
}
