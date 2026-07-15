import { Moon, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import logoMinhaDelpi from "../assets/logoMinhaDelpi.svg";
import { MODULE_EYEBROW, MODULE_TITLE } from "../content/catalog";

type ModuleHeaderProps = {
  title?: string;
  /** Só logo + eyebrow (página de detalhe). */
  brandOnly?: boolean;
  /** Toggle de tema — útil no standalone; oculto na impressão. */
  showThemeToggle?: boolean;
  /** Ações à direita (ex.: Administrar conteúdo). */
  actions?: ReactNode;
};

function readIsDark(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.getAttribute("data-theme") === "dark";
}

export function ModuleHeader({
  title = MODULE_TITLE,
  brandOnly = false,
  showThemeToggle = false,
  actions = null,
}: ModuleHeaderProps) {
  const [isDark, setIsDark] = useState(readIsDark);

  useEffect(() => {
    if (!showThemeToggle) return;
    document.documentElement.setAttribute(
      "data-theme",
      isDark ? "dark" : "light",
    );
  }, [isDark, showThemeToggle]);

  return (
    <header
      className={`gp-header${brandOnly ? " gp-header--brand" : ""} gp-no-print-hide`}
    >
      <div className="gp-header__brand">
        <img
          className="gp-header__logo"
          src={logoMinhaDelpi}
          alt="Minha DELPI"
        />
        {!brandOnly ? (
          <>
            <span className="gp-header__divider" aria-hidden="true" />
            <div className="gp-header__titles">
              <p className="gp-header__eyebrow">{MODULE_EYEBROW}</p>
              <h1 className="gp-header__title">{title}</h1>
            </div>
          </>
        ) : (
          <span className="gp-header__eyebrow gp-header__eyebrow--inline">
            {MODULE_EYEBROW}
          </span>
        )}
      </div>

      <div className="gp-header__actions">
        {actions}
        {showThemeToggle ? (
          <button
            type="button"
            className="gp-theme-toggle"
            onClick={() => setIsDark((prev) => !prev)}
            aria-label={isDark ? "Ativar tema claro" : "Ativar tema escuro"}
            aria-pressed={isDark}
          >
            {isDark ? (
              <Sun size={18} strokeWidth={2} aria-hidden="true" />
            ) : (
              <Moon size={18} strokeWidth={2} aria-hidden="true" />
            )}
          </button>
        ) : null}
      </div>
    </header>
  );
}
