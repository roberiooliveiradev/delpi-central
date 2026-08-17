import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type ViewTransitionTone = "page" | "panel";

export type ViewTransitionClassNames = {
  root: string;
};

export type ViewTransitionProps = {
  /** Muda a key → remonta e dispara a animação de entrada. */
  transitionKey: string;
  classNames: ViewTransitionClassNames;
  children: ReactNode;
  /** `page` = fade+slide 220ms; `panel` = mais curto (abas internas). */
  tone?: ViewTransitionTone;
  className?: string;
  "aria-live"?: "off" | "polite" | "assertive";
};

export function viewTransitionBemClasses(prefix: string): ViewTransitionClassNames {
  return {
    root: delpiUiClass(`${prefix}-view-transition`, "delpi-ui-view-transition"),
  };
}

export function ViewTransition({
  transitionKey,
  classNames,
  children,
  tone = "page",
  className,
  "aria-live": ariaLive = "off",
}: ViewTransitionProps) {
  const rootClass = [
    classNames.root,
    withBemModifier(classNames.root, tone),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div key={transitionKey} className={rootClass} aria-live={ariaLive}>
      {children}
    </div>
  );
}

export type DashboardViewTransitionProps = Omit<ViewTransitionProps, "classNames">;

export function createDashboardViewTransition(config: { prefix: string }) {
  const classNames = viewTransitionBemClasses(config.prefix);
  return function DashboardViewTransition(props: DashboardViewTransitionProps) {
    return <ViewTransition classNames={classNames} {...props} />;
  };
}
