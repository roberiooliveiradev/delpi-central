import { X } from "lucide-react";
import type { ReactNode } from "react";

export type FormatPaneTab = {
  id: string;
  label: string;
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

/** Painel lateral estilo PowerPoint — título, fechar, abas com sublinhado e corpo rolável. */
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
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={active}
                className={[
                  "delpi-ui-format-pane__tab",
                  active ? "delpi-ui-format-pane__tab--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onTabChange?.(tab.id)}
              >
                {tab.label}
              </button>
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
