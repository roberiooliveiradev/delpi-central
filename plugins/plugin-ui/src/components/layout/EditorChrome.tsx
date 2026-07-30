import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type EditorChromeDensity = "default" | "compact";

export type EditorChromeClassNames = {
  root: string;
  head: string;
  headLeading: string;
  headTabs: string;
  headTrailing: string;
  headTrail: string;
  ribbon: string;
  body: string;
};

export function editorChromeBemClasses(prefix = "delpi-ui"): EditorChromeClassNames {
  const base = `${prefix}-editor-chrome`;
  const ui = "delpi-ui-editor-chrome";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    head: pair(`${base}__head`, `${ui}__head`),
    headLeading: pair(`${base}__head-leading`, `${ui}__head-leading`),
    headTabs: pair(`${base}__head-tabs`, `${ui}__head-tabs`),
    headTrailing: pair(`${base}__head-trailing`, `${ui}__head-trailing`),
    headTrail: pair(`${base}__head-trail`, `${ui}__head-trail`),
    ribbon: pair(`${base}__ribbon`, `${ui}__ribbon`),
    body: pair(`${base}__body`, `${ui}__body`),
  };
}

const DEFAULT_CN = editorChromeBemClasses();

export type EditorChromeProps = {
  leading?: ReactNode;
  tabs?: ReactNode;
  trailing?: ReactNode;
  trail?: ReactNode;
  ribbon?: ReactNode;
  children?: ReactNode;
  density?: EditorChromeDensity;
  className?: string;
  classNames?: EditorChromeClassNames;
  "aria-label"?: string;
};

/**
 * Shell de editor em 2 faixas (head + ribbon) + corpo — padrão TV Dashboard.
 */
export function EditorChrome({
  leading,
  tabs,
  trailing,
  trail,
  ribbon,
  children,
  density = "compact",
  className,
  classNames = DEFAULT_CN,
  "aria-label": ariaLabel,
}: EditorChromeProps) {
  return (
    <section
      className={[classNames.root, className ?? ""].filter(Boolean).join(" ")}
      data-delpi-ui-density={density === "compact" ? "compact" : undefined}
      aria-label={ariaLabel}
    >
      <div className={classNames.head}>
        {leading ? <div className={classNames.headLeading}>{leading}</div> : null}
        {tabs ? <div className={classNames.headTabs}>{tabs}</div> : null}
        {trailing ? <div className={classNames.headTrailing}>{trailing}</div> : null}
        {trail ? <div className={classNames.headTrail}>{trail}</div> : null}
      </div>
      {ribbon != null ? <div className={classNames.ribbon}>{ribbon}</div> : null}
      {children != null ? <div className={classNames.body}>{children}</div> : null}
    </section>
  );
}
