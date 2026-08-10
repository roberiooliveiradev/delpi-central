import type { KeyboardEvent, ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type UnderlineNavItem = {
  id: string;
  label: ReactNode;
  icon?: ReactNode;
  /** Contagem badge (ex.: overdue+today). Omitir ou 0 = sem badge. */
  count?: number;
  /** Tooltip / título nativo do botão. */
  title?: string;
  /** Id do painel controlado, obrigatório semanticamente no modo tabs. */
  controlId?: string;
  /** Id do tab usado pelo painel em aria-labelledby. */
  tabId?: string;
  onSelect?: () => void;
};

export type UnderlineNavClassNames = {
  root: string;
  scroller: string;
  item: string;
  icon: string;
  label: string;
  count: string;
};

export type UnderlineNavProps = {
  items: UnderlineNavItem[];
  activeId: string;
  mode?: "navigation" | "tabs";
  classNames: UnderlineNavClassNames;
  className?: string;
  "aria-label"?: string;
};

export function underlineNavBemClasses(prefix: string): UnderlineNavClassNames {
  return {
    root: delpiUiClass(`${prefix}-underline-nav`, "delpi-ui-underline-nav"),
    scroller: delpiUiClass(`${prefix}-underline-nav__scroller`, "delpi-ui-underline-nav__scroller"),
    item: delpiUiClass(`${prefix}-underline-nav__item`, "delpi-ui-underline-nav__item"),
    icon: delpiUiClass(`${prefix}-underline-nav__icon`, "delpi-ui-underline-nav__icon"),
    label: delpiUiClass(`${prefix}-underline-nav__label`, "delpi-ui-underline-nav__label"),
    count: delpiUiClass(`${prefix}-underline-nav__count`, "delpi-ui-underline-nav__count"),
  };
}

export function UnderlineNav({
  items,
  activeId,
  mode = "navigation",
  classNames,
  className,
  "aria-label": ariaLabel = "Navegação",
}: UnderlineNavProps) {
  if (!items.length) return null;

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft" && event.key !== "Home" && event.key !== "End") {
      return;
    }
    event.preventDefault();
    const buttons = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(
      "button[data-underline-nav-item]",
    );
    if (!buttons?.length) return;
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % buttons.length;
    if (event.key === "ArrowLeft") next = (index - 1 + buttons.length) % buttons.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = buttons.length - 1;
    buttons[next]?.focus();
    buttons[next]?.click();
  };

  const activeTabIndex = Math.max(
    0,
    items.findIndex((item) => item.id === activeId),
  );
  const itemsContent = (
    <>
        {items.map((item, index) => {
          const active = item.id === activeId;
          const itemClass = active ? withBemModifier(classNames.item, "active") : classNames.item;
          const count = typeof item.count === "number" && item.count > 0 ? item.count : null;
          return (
            <button
              key={item.id}
              type="button"
              data-underline-nav-item=""
              className={itemClass}
              role={mode === "tabs" ? "tab" : undefined}
              id={mode === "tabs" ? (item.tabId ?? `${item.id}-tab`) : undefined}
              aria-current={mode === "navigation" && active ? "page" : undefined}
              aria-selected={mode === "tabs" ? active : undefined}
              aria-controls={mode === "tabs" ? item.controlId : undefined}
              tabIndex={mode === "tabs" ? (index === activeTabIndex ? 0 : -1) : undefined}
              title={item.title}
              onClick={item.onSelect}
              onKeyDown={(event) => onKeyDown(event, index)}
            >
              {item.icon ? <span className={classNames.icon}>{item.icon}</span> : null}
              <span className={classNames.label}>{item.label}</span>
              {count != null ? (
                <span className={classNames.count} aria-hidden="true">
                  {count > 99 ? "99+" : count}
                </span>
              ) : null}
            </button>
          );
        })}
    </>
  );

  if (mode === "tabs") {
    return (
      <div className={rootClass}>
        <div className={classNames.scroller} role="tablist" aria-label={ariaLabel}>
          {itemsContent}
        </div>
      </div>
    );
  }

  return (
    <nav className={rootClass} aria-label={ariaLabel}>
      <div className={classNames.scroller}>{itemsContent}</div>
    </nav>
  );
}

export type DashboardUnderlineNavProps = Omit<UnderlineNavProps, "classNames">;

export function createDashboardUnderlineNav(config: { prefix: string }) {
  const classNames = underlineNavBemClasses(config.prefix);
  return function DashboardUnderlineNav(props: DashboardUnderlineNavProps) {
    return <UnderlineNav classNames={classNames} {...props} />;
  };
}
