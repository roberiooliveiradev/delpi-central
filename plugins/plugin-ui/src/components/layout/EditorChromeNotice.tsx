import type { ButtonHTMLAttributes, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type EditorChromeNoticeTone = "neutral" | "info" | "warning" | "danger";

export type EditorChromeNoticeClassNames = {
  root: string;
  rootTone: Record<EditorChromeNoticeTone, string>;
  action: string;
};

export function editorChromeNoticeBemClasses(
  prefix = "delpi-ui",
): EditorChromeNoticeClassNames {
  const base = `${prefix}-editor-chrome-notice`;
  const ui = "delpi-ui-editor-chrome-notice";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    rootTone: {
      neutral: pair(`${base}--neutral`, `${ui}--neutral`),
      info: pair(`${base}--info`, `${ui}--info`),
      warning: pair(`${base}--warning`, `${ui}--warning`),
      danger: pair(`${base}--danger`, `${ui}--danger`),
    },
    action: pair(`${base}__action`, `${ui}__action`),
  };
}

const DEFAULT_CN = editorChromeNoticeBemClasses();

export type EditorChromeNoticeProps = {
  children: ReactNode;
  tone?: EditorChromeNoticeTone;
  /** Botão opcional (ex.: Ok para dispensar). */
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  classNames?: EditorChromeNoticeClassNames;
  actionProps?: Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "onClick" | "type">;
};

/** Aviso compacto para top bar / chrome de editor (info, warning, danger). */
export function EditorChromeNotice({
  children,
  tone = "info",
  actionLabel,
  onAction,
  className,
  classNames = DEFAULT_CN,
  actionProps,
}: EditorChromeNoticeProps) {
  return (
    <div
      className={[classNames.root, classNames.rootTone[tone], className ?? ""]
        .filter(Boolean)
        .join(" ")}
      role="status"
    >
      <span className="delpi-ui-editor-chrome-notice__body">{children}</span>
      {actionLabel && onAction ? (
        <button
          type="button"
          className={classNames.action}
          onClick={onAction}
          {...actionProps}
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

export type EditorChromeNoticesProps = {
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
};

/**
 * Pilha de avisos do chrome (também usável fora do {@link EditorChrome},
 * ex.: banner de colaboração em páginas de detalhe).
 */
export function EditorChromeNotices({
  children,
  className,
  "aria-label": ariaLabel,
}: EditorChromeNoticesProps) {
  return (
    <div
      className={["delpi-ui-editor-chrome-notices", className ?? ""].filter(Boolean).join(" ")}
      role="status"
      aria-label={ariaLabel}
    >
      {children}
    </div>
  );
}
