import { Search } from "lucide-react";
import { forwardRef } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type TopBarSearchTriggerClassNames = {
  root: string;
  label: string;
  kbd: string;
};

export type TopBarSearchTriggerProps = {
  onOpen: () => void;
  label: string;
  shortcutLabel: string;
  "aria-label": string;
  title?: string;
  classNames: TopBarSearchTriggerClassNames;
  className?: string;
  /** Quando a palette está aberta (aria-expanded). */
  expanded?: boolean;
};

export function topBarSearchTriggerBemClasses(prefix: string): TopBarSearchTriggerClassNames {
  const base = `${prefix}-topbar-search`;
  const ui = "delpi-ui-topbar-search";
  return {
    root: delpiUiClass(base, ui),
    label: delpiUiClass(`${base}__label`, `${ui}__label`),
    kbd: delpiUiClass(`${base}__kbd`, `${ui}__kbd`),
  };
}

/**
 * Pill da TopBar que abre a Command Palette (Ctrl/Cmd+K).
 * CSS: `styles/top-bar.css` (`.delpi-ui-topbar-search*`).
 */
export const TopBarSearchTrigger = forwardRef<HTMLButtonElement, TopBarSearchTriggerProps>(
  function TopBarSearchTrigger(
    {
      onOpen,
      label,
      shortcutLabel,
      title,
      classNames,
      className,
      expanded = false,
      "aria-label": ariaLabel,
    },
    ref,
  ) {
    const rootClass = [classNames.root, className].filter(Boolean).join(" ");
    return (
      <button
        ref={ref}
        type="button"
        className={rootClass}
        onClick={onOpen}
        aria-label={ariaLabel}
        aria-haspopup="dialog"
        aria-expanded={expanded}
        title={title}
      >
        <Search size={16} strokeWidth={1.75} aria-hidden="true" />
        <span className={classNames.label}>{label}</span>
        <kbd className={classNames.kbd}>{shortcutLabel}</kbd>
      </button>
    );
  },
);

export type DashboardTopBarSearchTriggerProps = Omit<TopBarSearchTriggerProps, "classNames">;

export function createDashboardTopBarSearchTrigger(config: { prefix: string }) {
  const classNames = topBarSearchTriggerBemClasses(config.prefix);
  return forwardRef<HTMLButtonElement, DashboardTopBarSearchTriggerProps>(
    function DashboardTopBarSearchTrigger(props, ref) {
      return <TopBarSearchTrigger ref={ref} classNames={classNames} {...props} />;
    },
  );
}
