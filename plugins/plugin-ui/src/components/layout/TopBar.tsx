import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import {
  UnderlineNav,
  underlineNavBemClasses,
  type UnderlineNavClassNames,
  type UnderlineNavItem,
} from "./UnderlineNav";

export type TopBarClassNames = {
  root: string;
  row: string;
  nav: string;
  secondary: string;
  actions: string;
};

export type TopBarProps = {
  items: UnderlineNavItem[];
  activeId: string;
  classNames: TopBarClassNames;
  navClassNames: UnderlineNavClassNames;
  /** Slot entre nav e actions (ex.: favoritos). */
  secondary?: ReactNode;
  /** Slot à direita (escopo, ações). */
  actions?: ReactNode;
  /** Extensão lateral alinhada ao padding da página (padrão admin). */
  bleed?: boolean;
  sticky?: boolean;
  /** Fundo surface (banda). Default false = flush com a página. */
  surface?: boolean;
  className?: string;
  "aria-label"?: string;
};

export function topBarBemClasses(prefix: string): TopBarClassNames {
  return {
    root: delpiUiClass(`${prefix}-topbar`, "delpi-ui-topbar"),
    row: delpiUiClass(`${prefix}-topbar__row`, "delpi-ui-topbar__row"),
    nav: delpiUiClass(`${prefix}-topbar__nav`, "delpi-ui-topbar__nav"),
    secondary: delpiUiClass(`${prefix}-topbar__secondary`, "delpi-ui-topbar__secondary"),
    actions: delpiUiClass(`${prefix}-topbar__actions`, "delpi-ui-topbar__actions"),
  };
}

export function TopBar({
  items,
  activeId,
  classNames,
  navClassNames,
  secondary,
  actions,
  bleed = true,
  sticky = true,
  surface = false,
  className,
  "aria-label": ariaLabel = "Navegação",
}: TopBarProps) {
  const rootClass = [
    classNames.root,
    bleed ? withBemModifier(classNames.root, "bleed") : null,
    sticky ? withBemModifier(classNames.root, "sticky") : null,
    surface ? withBemModifier(classNames.root, "surface") : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <div className={classNames.row}>
        <div className={classNames.nav}>
          <UnderlineNav
            classNames={navClassNames}
            items={items}
            activeId={activeId}
            aria-label={ariaLabel}
          />
        </div>
        {secondary ? <div className={classNames.secondary}>{secondary}</div> : null}
        {actions ? <div className={classNames.actions}>{actions}</div> : null}
      </div>
    </div>
  );
}

export type DashboardTopBarProps = Omit<TopBarProps, "classNames" | "navClassNames">;

export function createDashboardTopBar(config: { prefix: string }) {
  const classNames = topBarBemClasses(config.prefix);
  const navClassNames = underlineNavBemClasses(config.prefix);
  return function DashboardTopBar(props: DashboardTopBarProps) {
    return <TopBar classNames={classNames} navClassNames={navClassNames} {...props} />;
  };
}
