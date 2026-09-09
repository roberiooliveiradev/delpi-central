import type { ReactNode } from "react";
import { HelpTooltip, delpiUiClass } from "@delpi/plugin-ui/index";

type AdminTabHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  /** Texto de Ajuda (hover) — catálogo adminHelpTooltips.pages. */
  helpHint: string;
  actions?: ReactNode;
  summary?: ReactNode;
  className?: string;
};

/**
 * Cabeçalho de aba admin — dual-class com tokens do PageHeader do kit (convergência gradual).
 */
export function AdminTabHeader({
  eyebrow,
  title,
  description,
  helpHint,
  actions,
  summary,
  className,
}: AdminTabHeaderProps) {
  const rootClass = [
    delpiUiClass("mdc-admin-tab-header", "delpi-ui-page-header"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <header className={rootClass}>
      <div
        className={delpiUiClass(
          "mdc-admin-page-header",
          "delpi-ui-page-header__content",
        )}
      >
        {eyebrow ? <p className="mdc-chat-eyebrow">{eyebrow}</p> : null}
        <h2>
          {title}
          {" "}
          <HelpTooltip content={helpHint} />
        </h2>
        {description ? <p>{description}</p> : null}
      </div>
      {summary}
      {actions ? (
        <div
          className={delpiUiClass(
            "mdc-admin-tab-header__actions",
            "delpi-ui-page-header__actions",
          )}
        >
          {actions}
        </div>
      ) : null}
    </header>
  );
}
