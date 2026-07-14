import { X, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { HintAction } from "../help/HintAction";

export type FormatPaneTab = {
  id: string;
  label: string;
  /** Ícone alinhado à top bar (chrome tabs). */
  icon?: LucideIcon;
  /** Balão explicativo da aba (hover). */
  hint?: string;
};

export type FormatPaneShellProps = {
  title: string;
  onClose?: () => void;
  closeLabel?: string;
  tabs?: readonly FormatPaneTab[];
  activeTabId?: string;
  onTabChange?: (tabId: string) => void;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
};

function FormatPaneTabButton({
  tab,
  active,
  onTabChange,
}: {
  tab: FormatPaneTab;
  active: boolean;
  onTabChange?: (tabId: string) => void;
}) {
  const Icon = tab.icon;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      className={["delpi-ui-format-pane__tab", active ? "delpi-ui-format-pane__tab--active" : ""]
        .filter(Boolean)
        .join(" ")}
      onClick={() => onTabChange?.(tab.id)}
    >
      {Icon ? <Icon className="delpi-ui-format-pane__tab-icon" size={14} aria-hidden="true" /> : null}
      {tab.label}
    </button>
  );
}

/** Painel lateral estilo PowerPoint — título, fechar, abas com sublinhado reto e corpo rolável. */
export function FormatPaneShell({
  title,
  onClose,
  closeLabel = "Fechar painel",
  tabs,
  activeTabId,
  onTabChange,
  children,
  className,
  bodyClassName,
}: FormatPaneShellProps) {
  const rootClass = ["delpi-ui-format-pane", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      <header className="delpi-ui-format-pane__head">
        <h2 className="delpi-ui-format-pane__title">{title}</h2>
        {onClose ? (
          <button
            type="button"
            className="delpi-ui-format-pane__close"
            onClick={onClose}
            aria-label={closeLabel}
          >
            <X size={16} aria-hidden="true" />
          </button>
        ) : null}
      </header>
      {tabs && tabs.length > 0 ? (
        <div className="delpi-ui-format-pane__tabs" role="tablist">
          {tabs.map((tab) => {
            const active = tab.id === activeTabId;
            if (!tab.hint) {
              return (
                <FormatPaneTabButton
                  key={tab.id}
                  tab={tab}
                  active={active}
                  onTabChange={onTabChange}
                />
              );
            }
            return (
              <HintAction
                key={tab.id}
                hint={tab.hint}
                ariaLabel={`Ajuda: ${tab.label}`}
                placement="bottom"
              >
                <FormatPaneTabButton tab={tab} active={active} onTabChange={onTabChange} />
              </HintAction>
            );
          })}
        </div>
      ) : null}
      <div className={["delpi-ui-format-pane__body", bodyClassName].filter(Boolean).join(" ")}>
        {children}
      </div>
    </div>
  );
}
